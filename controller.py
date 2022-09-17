from src.handlers.database import RealmWriteHandler, ItemDataPopulator
import multiprocessing


class Controller:

    @staticmethod
    def run_auction_writes():
        r_a = RealmWriteHandler('a')
        r_h = RealmWriteHandler('h')

        for realm_id in RealmWriteHandler.REALM_LIST_EU:
            r_a.run_session(realm_id)
            r_h.run_session(realm_id)


    @staticmethod
    def run_populate_items():
        i = ItemDataPopulator()
        i.populate_data()


if __name__ == '__main__':
    # placeholder
    pass