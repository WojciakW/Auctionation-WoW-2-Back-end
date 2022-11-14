from src.handlers.database import (
    RealmWriteHandler, 
    ItemDataPopulator,
    RealmTableMaker,
    DateTableMaker,
)


def run_create_realm_tables() -> None:
    """
    Setup PostgreSQL Realm tables 'realm_{realm_name}'.
    """
    handler = RealmTableMaker()
    handler.START()

def run_create_time_table() -> None:
    """
    Setup PostgreSQL BlizzAPI request time record table 'api_request_time_record'.
    """
    handler = DateTableMaker()
    handler.START()

def run_auction_writes() -> None:
    """
    Fetch and write all the live auctions data.
    """
    handler = RealmWriteHandler()
    for realm_id in handler.REALM_LIST_EU:
        handler.START(realm_id, 'a')
        handler.START(realm_id, 'h')

def run_populate_items() -> None:
    """
    Write all the items data.
    """
    handler = ItemDataPopulator()
    handler.START()


if __name__ == '__main__':
    # placeholder
    pass