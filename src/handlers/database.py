"""
AuctioNation2 main database handling resources.

All of the below handlers are designed to contain their own method 'START()' that 
executes operations proper to the specific class.
"""
# --------
# IMPORTS |
# --------
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

# --------
# CLASSES |
# --------
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

    CREATE_ITEM_TABLE = """
        CREATE TABLE item_data(
            wow_item_id SERIAL PRIMARY KEY,
            name VARCHAR,
            class VARCHAR,
            subclass VARCHAR,
            slot VARCHAR,
            quality VARCHAR,
            icon_url TEXT
        )
    """

    CREATE_TIME_TABLE = """
        CREATE TABLE api_request_time_record(
            id SERIAL PRIMARY KEY,
            api_request_time TIMESTAMP,
            faction_sign VARCHAR(1)
        )
    """

    INSERT_TIME_RECORD = """
        INSERT INTO api_request_time_record(
            api_request_time,
            faction_sign
        )
        VALUES(
            '%s',
            '%s'
        )
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
        SELECT 
            buyout, 
            api_request_time, 
            quantity 
        FROM realm_%s 
        WHERE faction='%s' AND wow_item_id=%d
    """

    # query to read live auctions (that is, most recent data) together with item names,
    # also contains already half-done pagination
    READ_AUCTION_DATA = """
        SELECT
            realm_{0}.wow_id, 
            realm_{0}.wow_item_id,
            realm_{0}.buyout, 
            realm_{0}.quantity, 
            realm_{0}.time_left,
            item_data.name
        FROM realm_{0}
        JOIN item_data
        ON realm_{0}.wow_item_id = item_data.wow_item_id
        WHERE 
            faction='{1}' 
            AND api_request_time=(
                SELECT api_request_time
                FROM api_request_time_record
                GROUP BY faction_sign, api_request_time, id
                HAVING faction_sign='{1}' AND id=MAX(id)
            )
            AND name LIKE '%{2}%'
        ORDER BY wow_id
        OFFSET {3} FETCH NEXT {4} ROWS ONLY
    """


class StatsCalculator:
    """
    Main static class used for various statistical computions. 
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

    
    def START(self):
        """
        Run all the operations.
        """
        for realm_id in self.REALM_LIST_EU:
            self.cursor.execute(self.CREATE_REALMS % self.REALM_LIST_EU[realm_id])
            self.connection.commit()


class ItemTableMaker(DatabaseConnection, QueryMixin):
    """
    Used to setup database item table.
    """
    def __init__(self):
        super().__init__()
        self.cursor = self.connection.cursor()

    def START(self):
        """
        Run all the operations.
        """
        self.cursor.execute(self.CREATE_ITEM_TABLE)
        self.connection.commit()


class DateTableMaker(DatabaseConnection, QueryMixin):
    """
    Uset to setup api_request_time table.
    """
    def __init__(self):
        super().__init__()
        self.cursor = self.connection.cursor()
    
    def START(self):
        """
        Run all the operations
        """
        self.cursor.execute(self.CREATE_TIME_TABLE)
        self.connection.commit()


class RealmWriteHandler(DatabaseConnection, QueryMixin):
    """
    Auction data writes handling class. 
    """
    def __init__(self, faction_sign: str) -> None:
        super().__init__()

        self.faction_sign = faction_sign
        self.cache_path = f'{Path(__file__).resolve().parents[1]}/cache/'
        self.time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # insert proper api_request_time record along the object construction
        self.cursor = self.connection.cursor()
        self.cursor.execute(
            self.INSERT_TIME_RECORD % (
                self.time,
                self.faction_sign
            )
        )
        self.connection.commit()

    
    def _set_auction_data(self, realm_id: int) -> dict:
        """
        Fetches live auctions data from BlizzAPI and returns it as deserialized JSON.
        """

        api = BlizzApi(
            f'https://eu.api.blizzard.com/data/wow/connected-realm/{realm_id}/auctions/{self.FACTIONS[self.faction_sign]}?namespace=dynamic-classic-eu&locale=en_GB&access_token=')
        api.get_response()

        # connection timeout error handling
        if api.timeout:
            print(f'BlizzAPI request for realm id: {realm_id}, {self.faction_sign} timed out.')
            raise TimeoutError

        return json.loads(api.response.content)


    def _bulk_write(self, realm_id: int) -> None:
        """
        Does a 'bulk write' operation based on SQL COPY query from a .csv cache file.
        """
        # manual psycopg2 connection necessary for multiprocessing (any other way?)
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


    def _cache_auction_data(self, realm_id: int) -> bool:
        """
        Writes temporary .csv file into cache/ directory for further SQL import purpose.
        Returns False in case operation failed, True otherwise.
        """
        auction_data = self._set_auction_data(realm_id)

        # ignore empty Auction Houses and break
        if not auction_data.get('auctions'):  
            print(f'None auctions in realm_id id: {realm_id}, {self.faction_sign}')
            return False

        print(f'Caching auctions data from realm id: {realm_id}, {self.faction_sign} faction ({len(auction_data.get("auctions"))} entries)')

        # create .csv file
        with open(f'{self.cache_path}/{realm_id}_{self.faction_sign}.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # write header
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
                # ignore auctions with no set buyout (only bids)
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

        return True

    def _clear_cache(self, realm_id: int) -> None:
        """
        Removes .csv cache file.
        """
        os.remove(f'{self.cache_path}/{realm_id}_{self.faction_sign}.csv')

    @MultiprocessManager.process_mark    
    def START(self, realm_id: int) -> None:
        """
        Run all the operations. Each method call spawns a new process.
        """
        # break in case of an empty Auction House:
        if not self._cache_auction_data(realm_id):
            return None

        self._bulk_write(realm_id)
        self._clear_cache(realm_id)


class ItemDataPopulator(QueryMixin, DatabaseConnection):
    """
     Used to populate item data table.
    """
    def __init__(self) -> None:
        super().__init__()
        self.path = f'{Path(__file__).resolve().parents[1]}/out.csv'

    def START(self) -> None:
        """
        Run all the operations.
        """
        cursor = self.connection.cursor()
        cursor.execute(self.POPULATE_ITEM_DATA % (self.path))
        self.connection.commit()


class ItemReadHandler(DatabaseConnection, QueryMixin):
    """
    Item data reads handling class.
    """
    def __init__(self, realm_name: str, faction_sign: str, wow_item_id: int):
        super().__init__()

        self._realm_name =   realm_name
        self._faction_sign = faction_sign
        self._wow_item_id =  wow_item_id

        self._raw_data = self._read_raw_data()

        # overall output is set as an instance attribute utilizing multiprocessing's "Pool"
        self.response = MultiprocessManager.compute_reads(
            func1=  StatsCalculator.get_lowest,
            func2=  StatsCalculator.get_mean,
            func3=  StatsCalculator.get_median,
            func4=  StatsCalculator.get_count,
            data=   self._raw_data
        )

    def __str__(self) -> str:
        return f'ItemReadHandler instance: {self._realm_name}, {self._faction_sign}, {self._wow_item_id}'

    def _read_raw_data(self) -> dict:
        """
        Makes a direct read from the database based on instance attributes (request parameters).
        """
        cursor = self.connection.cursor()
        cursor.execute(
            self.READ_ITEM_DATA % (
                self._realm_name,
                self._faction_sign,
                self._wow_item_id
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

            #  !! price per unit !!
            price_date_map[date_value].append(buyout_value / quantity_value) 

        return price_date_map


class AuctionReadHandler(DatabaseConnection, QueryMixin):
    """
    Auction data reads handling class.
    """
    def __init__(self, realm_name: str, faction_sign: str, item_slug: str,
                 page: int, limit: int):
        super().__init__()

        self._realm_name =   realm_name
        self._faction_sign = faction_sign
        self._item_slug =    item_slug

        # pagination params
        self._page =         page
        self._limit =        limit

        # declare how many entries to skip from start
        self._offset =       (self._page - 1) * self._limit

        self.cursor = self.connection.cursor()

        # output is set as an instance attribute
        self.response = self._read_data()

    def _read_data(self):
        self.cursor.execute(
            self.READ_AUCTION_DATA.format(
                self._realm_name,
                self._faction_sign,
                self._item_slug,
                self._offset,
                self._limit
            )
        )

        fetched_data = self.cursor.fetchall()
        result = []
        for row in fetched_data:
            # serializing
            result.append(
                {
                    'auction_id': row[0], 
                    'data': {
                        'wow_item_id':  row[1],
                        'buyout':       row[2],
                        'quantity':     row[3],
                        'time_left':    row[4],
                        'item_name':    row[5]
                    }
                }
            )
        return result