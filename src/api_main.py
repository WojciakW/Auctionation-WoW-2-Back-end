from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
from handlers.database import ItemReadHandler, AuctionReadHandler, ItemSearchHandler


app = FastAPI()

origins = [
    'http://127.0.0.1:3000',
    'http://localhost:3000'
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/items/{realm_name}/{faction_sign}/{wow_item_id}/")
async def response_item_data(realm_name: str, faction_sign: str, wow_item_id: int):
    """
    Returns item-specific auctions data in JSON format:
        - mean buyout,
        - median buyout,
        - lowest buyout,
        - auctions count
    Each set of those is strictly linked to its own unique BlizzAPI request time,
    this route returns all collected entries from the database.
    """
    # wrong realm name handling
    if realm_name not in ItemReadHandler.REALM_LIST_EU.values():
        raise HTTPException(status_code=404)

    # spawn new handler instance, collect all entries, do calculations
    i = ItemReadHandler(
        realm_name=     realm_name,
        faction_sign=   faction_sign,
        wow_item_id=    wow_item_id
    )
    return i.response


@app.get("/auctions/{realm_name}/{faction_sign}/{wow_item_slug}/")
async def response_auction_data(realm_name: str, faction_sign: str, wow_item_slug: str, 
                                page: int = 1, limit: int = 20):
    """
    Returns live auctions from the database.
    Query params: page - results page number (default 1), 
    limit - maximum number of entries per page (defaul 20).
    """
    # hardcoded query limit for safety purposes, raises 413: 'Payload Too Large'
    if limit > 100:
        raise HTTPException(status_code=413)

    # wrong realm name handling
    if realm_name not in ItemReadHandler.REALM_LIST_EU.values():
        raise HTTPException(status_code=404)

    # spawn new handler instance, collect all entries based on given pagination parameters
    a = AuctionReadHandler(
        realm_name=     realm_name,
        faction_sign=   faction_sign,
        item_slug=      wow_item_slug,
        page=           page,
        limit=          limit
    )
    return a.response


@app.get("/item_search/{wow_item_slug}/")
async def response_item_search(wow_item_slug: str, page: int = 1, limit: int = 20):
    """
    Returns all WoW items found by given search query, together with their specific WoW data.
    Query params: page - results page number (default 1), 
    limit - maximum number of entries per page (defaul 20).
    """
    # hardcoded query limit for safety purposes, raises 413: 'Payload Too Large'
    if limit > 100:
        raise HTTPException(status_code=413)

    # spawn new handler instance, collect all entries
    i = ItemSearchHandler(
        item_slug=      wow_item_slug,
        page=           page,
        limit=          limit
    )
    return i.response