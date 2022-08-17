from handlers.database import RealmDataHandler
from pathlib import Path

def run():
    
    for realm_id in RealmDataHandler.REALM_LIST_EU:

        rh = RealmDataHandler(str(realm_id))

        for faction in ('a', 'h'):

            try:
                rh.set_auction_data(faction)
            except TimeoutError:
                continue

            rh.cache_auction_data(
                rh.auction_data_alliance, 
                faction
            )
            rh.bulk_create_from_cache(
                RealmDataHandler.REALM_LIST_EU[realm_id],
                realm_id,
                faction
            )
            rh.clear_cache(
                realm_id,
                faction
            )

            #             try:
            #     rh.set_auction_data('a')
            #     rh.set_auction_data('h')
            # except TimeoutError:
            #     continue

            # rh.cache_auction_data(
            #     rh.auction_data_alliance, 
            #     'a'
            # )
            # rh.bulk_create_from_cache(
            #     RealmDataHandler.REALM_LIST_EU[realm_id],
            #     CACHE_PATH,
            #     realm_id,
            #     'a'
            # )
            # rh.clear_cache(
            #     CACHE_PATH,
            #     realm_id,
            #     'a'
            # )

            # rh.cache_auction_data(
            #     rh.auction_data_horde, 
            #     'h'
            # )
            # rh.bulk_create_from_cache(
            #     RealmDataHandler.REALM_LIST_EU[realm_id],
            #     CACHE_PATH,
            #     realm_id,
            #     'h'
            # )


if __name__ == '__main__':
    p = Path(__file__).resolve().parents[0]
    print(f'{p}/cache/')
