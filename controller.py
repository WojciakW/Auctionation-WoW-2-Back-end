from src.handlers.database import (
    RealmWriteHandler, 
    ItemDataPopulator,
    RealmTableMaker,
    ItemTableMaker
)


class Controller:

    @staticmethod
    def run_create_realm_tables():
        r = RealmTableMaker()
        r.run()

    @staticmethod
    def run_create_item_table():
        i = ItemTableMaker()
        i.run()

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
        i.run()


if __name__ == '__main__':
    # placeholder
    Controller.run_populate_items()