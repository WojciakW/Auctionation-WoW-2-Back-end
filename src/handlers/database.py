from datetime import datetime, date
from pathlib import Path

from .connection import BlizzApi, DatabaseConnection
from .exceptions import TimeoutError
from .multiprocess import MultiprocessManager
from .local_settings import USER, PASSWORD

import json
import csv
import os
import psycopg2

import numpy as np


class DateEncoder(json.JSONEncoder):
    """
        Encodes datetime.datetime objects to string form.

    """

    def default(self, obj):

        if isinstance(obj, date):
            return str(obj)
        
        return super().default(self, obj)


class QueryMixin:
    """
        Mixin to contain SQL query-oriented constants.

    """

    REALM_LIST_EU = {
        4440: 'everlook',
        4441: 'auberdine',
        4442: 'lakeshire',
        4452: 'chromie',
        4453: 'pyrewood_village',
        4454: 'mirage_raceway',
        4455: 'razorfen',
        4456: 'nethergarde_keep',
        4463: 'lucifron',
        4464: 'sulfuron',
        4465: 'golemagg',
        4466: 'patchwerk',
        4467: 'firemaw',
        4474: 'flamegor',
        4475: 'shazzrah',
        4476: 'gehennas',
        4477: 'venoxis',
        4478: 'razorgore',
        4676: 'zandalar_tribe',
        4678: 'hydraxian_waterlords',
        4701: 'mograine',
        4702: 'gandling',
        4703: 'amnennar',
        4704: 'wyrmthalak',
        4705: 'stonespine',
        4706: 'flamelash',
        4741: 'noggenfogger',
        4742: 'ashbringer',
        4743: 'skullflame',
        4744: 'finkle',
        4745: 'transcendence',
        4746: 'bloodfang',
        4749: 'earthshaker',
        4751: 'dragonfang',
        4754: 'rhok_delar',
        4755: 'dreadmist',
        4756: 'dragon_s_call',
        4757: 'ten_storms',
        4758: 'judgement',
        4759: 'celebras',
        4763: 'heartstriker',
        4766: 'harbinger_of_doom',
        4813: 'mandokir'
    }

    FACTIONS = {
        'a': 2,
        'h': 6
    }

    CREATE_REALMS = """
        CREATE TABLE realm_%s(
            id SERIAL PRIMARY KEY,
            faction VARCHAR(1),
            wow_id BIGINT,
            wow_item_id INT,
            buyout INT,
            quantity INT,
            api_request_time TIMESTAMP,
            time_left SMALLINT
        );
    """

    BULK_CREATE_AUCTIONS = """
        COPY realm_%s(
            faction,
            wow_id,
            wow_item_id,
            buyout,
            quantity,
            api_request_time,
            time_left
        )
        FROM '%s/%s_%s.csv'
        DELIMITER ','
        CSV HEADER;
    """

    POPULATE_ITEM_DATA = """
        COPY item_data(
            wow_item_id,
            name,
            class,
            subclass,
            slot,
            quality,
            icon_url
        )
        FROM '%s'
        DELIMITER ','
        CSV HEADER;
    """

    READ_ITEM_DATA = """
        SELECT buyout, api_request_time, quantity FROM realm_%s WHERE faction='%s' AND wow_item_id=%d
    """


class StatCalculator:
    """
        Static calculator class utilizing multiprocessing. 
        Implemented to provide scalability and abstraction.

    """

    @staticmethod
    def get_mean(data: dict) -> dict:
        """
            Returns mean price per item unit for all the entries collected by different api_request_time.

        """

        result = {}

        for entry in data:
            prices_list = data.get(entry)

            result[entry] = np.mean(prices_list)

        return result


    @staticmethod
    def get_count(data: dict) -> dict:
        """
            Returns item auctions count for all the entries collected by different api_request_time.

        """

        result = {}

        for entry in data:
            result[entry] = len(data.get(entry))

        return result


    @staticmethod
    def get_median(data: dict) -> dict:
        """
            Returns median price per item unit for all the entries collected by different api_request_time

        """

        result = {}

        for entry in data:
            prices_list = data.get(entry)

            result[entry] = np.median(prices_list)

        return result


    @staticmethod
    def get_lowest(data: dict) -> dict:
        """
            Returns lowest price per item unit for all the entries collected by different api_request_time

        """
        result = {}

        for entry in data:
            result[entry] = min(data.get(entry))

        return result


class RealmTableMaker(DatabaseConnection, QueryMixin):
    """
        Used to setup database realm tables.

    """
    def __init__(self):
        super().__init__()
        self.cursor = self.connection.cursor()

    
    def run(self):
        for realm_id in self.REALM_LIST_EU:
            self.cursor.execute(self.CREATE_REALMS % self.REALM_LIST_EU[realm_id])
            self.connection.commit()


class RealmWriteHandler(QueryMixin):
    """
        Auction data writes handling class. 

    """
    
    def __init__(
            self, 
            faction_sign:   str
        ) -> None:

        super().__init__()

        self.faction_sign = faction_sign
        self.cache_path = f'{Path(__file__).resolve().parents[1]}/cache/'
        self.time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    
    def set_auction_data(self, realm_id):
        """
            Fetches live auction data from BlizzAPI and sets it as an instance attribute.

        """

        api = BlizzApi(
            f'https://eu.api.blizzard.com/data/wow/connected-realm/{realm_id}/auctions/{self.FACTIONS[self.faction_sign]}?namespace=dynamic-classic-eu&locale=en_GB&access_token=')
        api.get_response()

        if api.timeout:
            print(f'BlizzAPI request for realm id: {realm_id}, {self.faction_sign} timed out.')

            raise TimeoutError

        return json.loads(api.response.content)


    def bulk_write(self, realm_id):
        """
            Does a 'bulk write' operation based on SQL COPY query from a .csv cache file.

        """

        connection = psycopg2.connect(
                database='auctionation2_test',
                user=USER,
                password=PASSWORD,
                host='127.0.0.1',
                port='5432'
            )

        cursor = connection.cursor()

        cursor.execute(
            self.BULK_CREATE_AUCTIONS %
                (
                    self.REALM_LIST_EU[realm_id],
                    self.cache_path,
                    realm_id,
                    self.faction_sign
                )
            )

        connection.commit()
        connection.close()


    def cache_auction_data(self, realm_id):
        """
            Writes temporary .csv file into cache/ directory for further SQL import purpose.

        """
        
        auction_data = self.set_auction_data(realm_id)

        print(f'Caching auctions data from realm id: {realm_id}, {self.faction_sign} faction ({len(auction_data.get("auctions"))} entries)')

        with open(f'{self.cache_path}/{realm_id}_{self.faction_sign}.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)

            if not auction_data.get('auctions'):  # ignore empty Auction Houses
                print(f'None auctions in realm_id id: {realm_id}, {self.faction_sign}')

                return None
            
            writer.writerow([
                'faction',
                'wow_id',
                'wow_item_id',
                'buyout',
                'quantity',
                'api_request_time',
                'time_left',
            ])

            for line in auction_data.get('auctions'):

                if line.get('buyout') == 0:
                    continue
                
                # normalization
                if line.get('time_left') == 'SHORT':
                    time_left = 1
                
                elif line.get('time_left') == 'MEDIUM':
                    time_left = 2
                
                elif line.get('time_left') == 'LONG':
                    time_left = 3
                
                elif line.get('time_left') == 'VERY_LONG':
                    time_left = 4

                writer.writerow([
                    self.faction_sign,
                    line.get('id'),
                    line.get('item').get('id'),
                    line.get('buyout'),
                    line.get('quantity'),
                    self.time,
                    time_left,
                ])


    def clear_cache(self, realm_id):
        """
            Removes .csv cache file.

        """

        os.remove(f'{self.cache_path}/{realm_id}_{self.faction_sign}.csv')


    @MultiprocessManager.process_mark    
    def run_session(self, realm_id):
        self.cache_auction_data(realm_id)
        self.bulk_write(realm_id)
        self.clear_cache(realm_id)


class ItemDataPopulator(QueryMixin, DatabaseConnection):
    """
        Used to populate item data table.

    """

    def __init__(self) -> None:
        super().__init__()
        self.path = f'{Path(__file__).resolve().parents[1]}/out.csv'

    
    def run(self):
        cursor = self.connection.cursor()
        cursor.execute(self.POPULATE_ITEM_DATA % (self.path))
        self.connection.commit()


class ItemReadHandler(DatabaseConnection, QueryMixin):
    """
        Item data reads handling class.

    """

    def __init__(
            self, 
            realm_name:     str, 
            faction_sign:   str, 
            wow_item_id:    int
        ):

        super().__init__()

        self.realm_name =   realm_name
        self.faction_sign = faction_sign
        self.wow_item_id =  wow_item_id

        self.raw_data = self.read_raw_data()

        self.response = MultiprocessManager.compute_reads(
            func1=  StatCalculator.get_lowest,
            func2=  StatCalculator.get_mean,
            func3=  StatCalculator.get_median,
            func4=  StatCalculator.get_count,
            data=   self.raw_data
        )


    def __str__(self) -> str:
        return f'ItemReadHandler instance: {self.realm_name}, {self.faction_sign}, {self.wow_item_id}'


    def read_raw_data(self):
        
        cursor = self.connection.cursor()
        cursor.execute(
            self.READ_ITEM_DATA % (
                self.realm_name,
                self.faction_sign,
                self.wow_item_id
            )
        )

        fetched_data = cursor.fetchall()

        price_date_map = {}

        for row in fetched_data:

            # hardcoded row data values:
            date_value =        f'{row[1]}'
            buyout_value =      row[0]
            quantity_value =    row[2]

            if not price_date_map.get(date_value):
                price_date_map[date_value] = []
            
            price_date_map[date_value].append(buyout_value / quantity_value) #  ! price per unit !

        return price_date_map


class AuctionReadHandler(DatabaseConnection, QueryMixin):
    """
        Auction data reads handling class.

    """

    def __init__(
            self, 
            realm_name:     str, 
            faction_sign:   str,
            item_slug:      str
        ):

        super().__init__()

        self.realm_name =   realm_name
        self.faction_sign = faction_sign
        self.item_slug =    item_slug
    

    def read_data(self):
        pass