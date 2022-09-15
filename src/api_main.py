from fastapi import FastAPI, HTTPException
import json
from handlers.database import ItemReadHandler


app = FastAPI()


@app.get("/items/{realm_name}/{faction_sign}/{wow_item_id}/")
async def response_item_data(
        realm_name:     str, 
        faction_sign:   str, 
        wow_item_id:    int
    ):

    if realm_name not in ItemReadHandler.REALM_LIST_EU.values():
        raise HTTPException(status_code=404)

    i = ItemReadHandler(
        realm_name,
        faction_sign,
        wow_item_id
    )

    return i.response

