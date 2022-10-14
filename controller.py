from src.handlers.database import (
    RealmWriteHandler, 
    ItemDataPopulator,
    RealmTableMaker,
    ItemTableMaker,
    DateTableMaker,
    AuctionReadHandler
)


class Controller:
    handler = None

    @classmethod
    def RUN_create_realm_tables(cls) -> None:
        """
        Setup PostgreSQL Realm tables 'realm_{realm_name}'.
        """
        cls.handler = RealmTableMaker()
        cls.handler.START()

    @classmethod
    def RUN_create_item_table(cls) -> None:
        """
        Setup PostgreSQL Item table 'item_data'.
        """
        cls.handler = ItemTableMaker()
        cls.handler.START()
    
    @classmethod
    def RUN_create_time_table(cls) -> None:
        """
        Setup PostgreSQL BlizzAPI request time record table 'api_request_time_record'.
        """
        cls.handler = DateTableMaker()
        cls.handler.START()

    @classmethod
    def RUN_auction_writes(cls) -> None:
        """
        Fetch and write all the live auctions data.
        """
        cls.handler = RealmWriteHandler()
        for realm_id in cls.handler.REALM_LIST_EU:
            cls.handler.START(realm_id, 'a')
            cls.handler.START(realm_id, 'h')

    @classmethod
    def RUN_populate_items(cls) -> None:
        """
        Write all the items data.
        """
        cls.handler = ItemDataPopulator()
        cls.handler.START()


if __name__ == '__main__':
    # placeholder