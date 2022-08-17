from datetime import datetime
from pathlib import Path

from handlers.connection import BlizzApiHandler, DatabaseConnector
from handlers.exceptions import TimeoutError

import time
import re
import json
import csv
import os


class PostgresManager:

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

    FACTIONS = {
            'a': 2,
            'h': 6
        }

    CREATE_DATE = """
        INSERT INTO app_auctionation_dates(
            value
        ) 
        VALUES(
            '%s'
        );
    """

    CREATE_AUCTIONS_BASE = """
        INSERT INTO app_auctionation_auction(
            faction,
            wow_id,
            wow_item_id,
            buyout,
            quantity,
            to_archive,
            api_request_time_id,
            realm_id
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

    def __init__(self):
        self.time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.db_conn = DatabaseConnector().connection


class RealmDataHandler(PostgresManager):

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

    def __init__(self, realm_id=None):
        super().__init__()

        self.realm_id = realm_id

        self.auction_data_alliance = None
        self.auction_data_horde = None

        self.cache_path = f'{Path(__file__).resolve().parents[0]}/cache/'

    def make_realms(self):
        """
        Creates appropriate realm tables.
        """

        api = BlizzApiHandler(
            'https://eu.api.blizzard.com/data/wow/realm/index?namespace=dynamic-classic-eu&locale=en_GB&access_token='
        )
        api.get_response()

        if api.timeout:
            pass

        else:
            response_json = json.loads(api.response.content)

            for i in range(len(response_json.get('realms'))):
                realm_name = re.sub('\s', '_', response_json.get('realms')[i].get('name'))
                realm_name = re.sub(r"a*'", '_', realm_name)

                cursor = self.db_conn.cursor()
                cursor.execute(
                    self.CREATE_REALMS
                    % (
                        realm_name,
                    )
                )
                self.db_conn.commit()

    
    def set_auction_data(self, faction_sign):

        FACTIONS = {
            'a': 2,
            'h': 6
        }

        api = BlizzApiHandler(
            f'https://eu.api.blizzard.com/data/wow/connected-realm/{self.realm_id}/auctions/{FACTIONS.get(faction_sign)}?namespace=dynamic-classic-eu&locale=en_GB&access_token=')
        api.get_response()

        if api.timeout:
            print(f'BlizzAPI request for realm id: {self.realm_id}, {faction_sign} timed out.')

            raise TimeoutError

        if faction_sign == 'a':
            self.auction_data_alliance = json.loads(api.response.content)
        
        elif faction_sign == 'h':
            self.auction_data_horde = json.loads(api.response.content)


    def cache_auction_data(self, faction_data, faction_sign):
        print(f'Caching auctions data from realm id: {self.realm_id}, {faction_sign}')

        with open(f'cache/{self.realm_id}_{faction_sign}.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)

            if not faction_data.get('auctions'):  # ignore empty Auction Houses
                print(f'None auctions in realm id: {self.realm_id}, {faction_sign}')

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

            for line in faction_data.get('auctions'):

                if line.get('buyout') == 0:
                    continue
                
                # encode time left to ints for space saving
                if line.get('time_left') == 'SHORT':
                    time_left = 1
                
                elif line.get('time_left') == 'MEDIUM':
                    time_left = 2
                
                elif line.get('time_left') == 'LONG':
                    time_left = 3
                
                elif line.get('time_left') == 'VERY_LONG':
                    time_left = 4

                writer.writerow([
                    faction_sign,
                    line.get('id'),
                    line.get('item').get('id'),
                    line.get('buyout'),
                    line.get('quantity'),
                    self.time,
                    time_left,
                ])


    def bulk_create_from_cache(self, realm_name, realm_cache, faction_sign):
        cursor = self.db_conn.cursor()

        cursor.execute(
            self.BULK_CREATE_AUCTIONS %
                (
                    realm_name,
                    self.cache_path,
                    realm_cache,
                    faction_sign
                )
            )

        self.db_conn.commit()


    def clear_cache(self, realm, faction_sign):
        os.remove(f'{self.cache_path}/{realm}_{faction_sign}.csv')


class DatabaseHandler(PostgresManager):

    def populate_date(self):
        cursor = self.db_conn.cursor()
        cursor.execute(DatabaseHandler.CREATE_DATE % self.time)
        self.db_conn.commit()

    def populate_realms(self):
        pass

    def populate_items(self):
        pass

    def populate_auctions(self):
        api = BlizzApiHandler(
            'https://eu.api.blizzard.com/data/wow/connected-realm/4440/auctions/2?namespace=dynamic-classic-eu&locale=en_GB&access_token=')
        api.get_response()

        if api.timeout:
            pass

        else:
            response_json = json.loads(api.response.content)

            for _ in range(50):  # batch create
                values_base = 'VALUES '

                for i in range(1000):

                    print(i, end='\r')

                    if response_json.get('auctions')[i].get('buyout') == 0:
                        continue

                    wow_id              = int(response_json.get('auctions')[i].get('id'))
                    wow_item_id         = int(response_json.get('auctions')[i].get('item').get('id'))
                    buyout              = int(response_json.get('auctions')[i].get('buyout'))
                    api_request_time    = self.time
                    faction             = 'd'
                    realm               = 'dupa'
                    quantity            = int(response_json.get('auctions')[i].get('quantity'))

                    value = f"('{faction}', {wow_id}, {wow_item_id}, {buyout}, {quantity}, false, ( SELECT id FROM app_auctionation_dates WHERE value='{api_request_time}' ), 2)"

                    if i != 999:
                        value += ','

                    values_base += value

                cursor = self.db_conn.cursor()
                cursor.execute(DatabaseHandler.CREATE_AUCTIONS_BASE + values_base)
                self.db_conn.commit()


def archive_auctions(self):
    pass


# handler = DatabaseHandler()
# #
# # handler.populate_date()
#
# start = time.time()
# handler.populate_realms()
# end = time.time()
#
# print(end - start, 's')

