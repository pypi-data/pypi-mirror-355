import asyncio
from urllib.parse import unquote, quote_plus
from pyrogram import Client
from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw.types import InputBotAppShortName, InputUser
from pyrogram.raw.functions.users import GetUsers
from curl_cffi import requests
import re

def cap(text) -> str:
    words = re.findall(r"\w+(?:'\w+)?", text)
    for word in words:
        if len(word) > 0:
            cap = word[0].upper() + word[1:]
            text = text.replace(word, cap, 1)
    return text

def listToURL(gifts: list) -> str:
    return '%2C'.join(quote_plus(cap(gift)) for gift in gifts)

async def update_auth(api_id: int|str, api_hash: str) -> str:
    """
    Updates Telegram authData for Portals API using Pyrogram.

    Args:
        api_id (int|str)
        api_hash (str)

    Returns:
        str: new authData
    """
    async with Client("account", api_id=api_id, api_hash=api_hash) as client:
        peer = await client.resolve_peer("portals")
        user_full = await client.invoke(GetUsers(id=[peer]))
        bot_raw = user_full[0]
        bot = InputUser(user_id=bot_raw.id, access_hash=bot_raw.access_hash)
        bot_app = InputBotAppShortName(bot_id=bot, short_name="market")
        web_view = await client.invoke(
            RequestAppWebView(
                peer=peer,
                app=bot_app,
                platform="desktop",
            )
        )
        initData = unquote(web_view.url.split('tgWebAppData=', 1)[1].split('&tgWebAppVersion', 1)[0])
        return f"tma {initData}"

SORTS = {
    "latest": "&sort_by=listed_at+desc",
    "price_asc": "&sort_by=price+asc",
    "price_desc": "&sort_by=price+desc",
    "gift_id_asc": "&sort_by=external_collection_number+asc",
    "gift_id_desc": "&sort_by=external_collection_number+desc",
    "model_rarity_asc": "&sort_by=model_rarity+asc",
    "model_rarity_desc": "&sort_by=model_rarity+desc"
}

API_URL = "https://portals-market.com/api/"

HEADERS = {
        "Authorization": "",
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
        "Origin": "https://portals-market.com",
        "Referer": "https://portals-market.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0"
    }

def search(sort: str = "price_asc", offset: int = 0, limit: int = 20, gift_name: str | list = "", model: str | list = "", backdrop: str | list = "", symbol: str | list = "", min_price: int = 0, max_price: int = 100000, authData: str = "") -> list:
    """
    Search for gifts with various filters and sorting options.

    Args:
        sort (str): The sorting method for the results. Available options:
            "price_asc", "price_desc", "latest", "gift_id_asc", "gift_id_desc", 
            "model_rarity_asc", "model_rarity_desc". Defaults to "price_asc".
        offset (int): The pagination offset (limit*page). Defaults to 0.
        limit (int): The maximum number of results to return. Defaults to 20 (probably max is 20).
        gift_name (str | list): The name or list of names of gifts to filter.
        model (str | list): The model or list of models to filter.
        backdrop (str | list): The backdrop or list of backdrops to filter.
        symbol (str | list): The symbol or list of symbols to filter.
        min_price (int): The minimum price of the gifts to filter. Defaults to 0.
        max_price (int): The maximum price of the gifts to filter. Defaults to 100000.
        authData (str): The authentication data required for the API request.

    Returns:
        list: A list of dictionaries containing the search results.

    Raises:
        Exception: If min_price or max_price are not integers.
        Exception: If max_price is less than min_price.
        Exception: If authData is not provided.
        Exception: If gift_name, model, backdrop, or symbol are not strings or lists.
        Exception: If the API request fails.
    """

    URL = API_URL + "nfts/" + "search?" + f"offset={offset}" + f"&limit={limit}" + f"{SORTS[sort]}"

    try:
        min_price = int(min_price)
        max_price = int(max_price)
    except:
        raise Exception("portalsapi: search(): Error: min_price and max_price must be integers")
    
    if max_price < 100000:
        URL += f"&min_price={min_price}&max_price={max_price}"

    if authData == "":
        raise Exception("portalsapi: search(): Error: authData is required")
    if max_price < min_price:
        raise Exception("portalsapi: search(): Error: max_price must be greater than min_price")

    if gift_name:
        if type(gift_name) == str:
            URL += f"&filter_by_collections={quote_plus(cap(gift_name))}"
        elif type(gift_name) == list:
            URL += f"&filter_by_collections={listToURL(gift_name)}"
        else:
            raise Exception("portalsapi: search(): Error: gift_name must be a string or list")
    if model:
        if type(model) == str:
            URL += f"&filter_by_models={quote_plus(cap(model))}"
        elif type(model) == list:
            URL += f"&filter_by_models={listToURL(model)}"
        else:
            raise Exception("portalsapi: search(): Error: model must be a string or list")
    if backdrop:
        if type(backdrop) == str:
            URL += f"&filter_by_backdrops={quote_plus(cap(backdrop))}"
        elif type(backdrop) == list:
            URL += f"&filter_by_backdrops={listToURL(backdrop)}"
        else:
            raise Exception("portalsapi: search(): Error: backdrop must be a string or list")
    if symbol:
        if type(symbol) == str:
            URL += f"&filter_by_symbols={quote_plus(cap(symbol))}"
        elif type(symbol) == list:
            URL += f"&filter_by_symbols={listToURL(symbol)}"
        else:
            raise Exception("portalsapi: search(): Error: symbol must be a string or list")
    
    URL += "&status=listed"

    HEADERS["Authorization"] = authData

    response = requests.get(URL, headers=HEADERS, impersonate="chrome110")
    if response.status_code != 200:
        raise Exception(f"portalsapi: search(): Error: status_code: {response.status_code}, response_text: {response.text}")

    return response.json()["results"] if response.json()["results"] else response.json()

def giftsFloors(authData: str = "") -> dict:
    """
    Retrieves the floor prices for all gift collections (short names only).

    Args:
        authData (str): The authentication data required for the API request.

    Returns:
        dict: A dictionary containing the floor prices of collections if the request is successful.

    Raises:
        Exception: If authData is not provided.
        Exception: If the API request fails or returns a non-200 status code.
    """

    URL = API_URL + "collections/floors"

    if authData == "":
        raise Exception("portalsapi: giftsFloors(): Error: authData is required")

    HEADERS["Authorization"] = authData

    response = requests.get(URL, headers=HEADERS, impersonate="chrome110")
    if response.status_code != 200:
        raise Exception(f"portalsapi: giftsFloors(): Error: status_code: {response.status_code}, response_text: {response.text}")

    return response.json()['floorPrices'] if response.json()['floorPrices'] else None

def myPortalsGifts(offset: int = 0, limit: int = 20, listed: bool = True, authData: str = "") -> list:
    """
    Retrieves a list of the user's owned Portal gifts.

    Args:
        offset (int): The offset for pagination.
        limit (int): The maximum number of items to return.
        listed (bool): If True, only gifts listed for sale are shown. Defaults to True.
        authData (str): The authentication data required for the API request.

    Returns:
        list: A list of the user's owned Portal gifts if the request is successful.

    Raises:
        Exception: If authData is not provided.
        Exception: If the API request fails or returns a non-200 status code.
    """
    URL = API_URL + "nfts/" + "owned?" + f"offset={offset}" + f"&limit={limit}"

    if authData == "":
        raise Exception("portalsapi: myPortalsGifts(): Error: authData is required")
    if listed == True:
        URL += "&status=listed"
    else:
        URL += "&status=unlisted"
    
    HEADERS["Authorization"] = authData

    response = requests.get(URL, headers=HEADERS, impersonate="chrome110")
    if response.status_code != 200:
        raise Exception(f"portalsapi: myPortalsGifts(): Error: status_code: {response.status_code}, response_text: {response.text}")

    return response.json()['nfts'] if response.json()['nfts'] else response.json()

def myPoints(authData: str = "") -> dict:
    """
    Retrieves the user's Portals Points information.

    Args:
        authData (str): The authentication data required for the API request.

    Returns:
        dict: A dictionary containing the user's points information if the request is successful.

    Raises:
        Exception: If authData is not provided.
        Exception: If the API request fails or returns a non-200 status code.
    """
    URL = API_URL + "points/my-points"

    if authData == "":
        raise Exception("portalsapi: myPoints(): Error: authData is required")

    HEADERS["Authorization"] = authData

    response = requests.get(URL, headers=HEADERS, impersonate="chrome110")
    if response.status_code != 200:
        raise Exception(f"portalsapi: myPoints(): Error: status_code: {response.status_code}, response_text: {response.text}")

    return response.json() if response.status_code == 200 else None

def myBalances(authData: str = "") -> dict:
    """
    Retrieves the user's balances.

    Args:
        authData (str): The authentication data required for the API request.

    Returns:
        dict: A dictionary containing the user's balances if the request is successful.

    Raises:
        Exception: If authData is not provided.
        Exception: If the API request fails or returns a non-200 status code.
    """
    URL = API_URL + "users/wallets/"

    if authData == "":
        raise Exception("portalsapi: myBalances(): Error: authData is required")

    HEADERS["Authorization"] = authData

    response = requests.get(URL, headers=HEADERS, impersonate="chrome110")
    if response.status_code != 200:
        raise Exception(f"portalsapi: myBalances(): Error: status_code: {response.status_code}, response_text: {response.text}")

    return response.json() if response.status_code == 200 else None

def myActivity(offset: int = 0, limit: int = 20, authData: str = "") -> list:
    """
    Retrieves the user's activity on the marketplace.

    Args:
        offset (int): The pagination offset (limit*page). Defaults to 0.
        limit (int): The maximum number of results to return. Defaults to 20.
        authData (str): The authentication data required for the API request.

    Returns:
        list: A list of dictionaries containing the user's activity if the request is successful.

    Raises:
        Exception: If authData is not provided.
        Exception: If the API request fails or returns a non-200 status code.
    """
    URL = API_URL + "users/actions/" + f"?offset={offset}" + f"&limit={limit}"

    if authData == "":
        raise Exception("portalsapi: myActivity(): Error: authData is required")

    HEADERS["Authorization"] = authData

    response = requests.get(URL, headers=HEADERS, impersonate="chrome110")
    if response.status_code != 200:
        raise Exception(f"portalsapi: myActivity(): Error: status_code: {response.status_code}, response_text: {response.text}")

    return response.json()['actions'] if response.json()['actions'] else response.json()

def collections(limit: int = 100, authData: str = "") -> list:
    """
    Retrieves a list of collections and their floors, supply, daily volume etc from the marketplace.

    Args:
        limit (int): The maximum number of results to return. Defaults to 100.
        authData (str): The authentication data required for the API request.

    Returns:
        list: A list of dictionaries containing information about the collections if the request is successful.

    Raises:
        Exception: If authData is not provided.
        Exception: If the API request fails or returns a non-200 status code.
    """
    URL = API_URL + "collections" + f"?limit={limit}"

    if authData == "":
        raise Exception("portalsapi: collections(): Error: authData is required")

    HEADERS["Authorization"] = authData

    response = requests.get(URL, headers=HEADERS, impersonate="chrome110")
    if response.status_code != 200:
        raise Exception(f"portalsapi: collections(): Error: status_code: {response.status_code}, response_text: {response.text}")

    return response.json()['collections'] if response.json()['collections'] else response.json()

def marketActivity(sort: str = "latest", offset: int = 0, limit: int = 20, activityType: str = "", gift_name: str | list= "", model: str | list = "", backdrop: str | list = "", symbol: str | list = "", min_price: int = 0, max_price: int = 100000, authData: str = "") -> list:
    """
    Retrieves market activity with various filters and sorting options.

    Args:
        sort (str): The sorting method for the results. Options include "latest", "price_asc", "price_desc", 
            "gift_id_asc", "gift_id_desc", "model_rarity_asc", "model_rarity_desc". Defaults to "latest".
        offset (int): The pagination offset (limit*page). Defaults to 0.
        limit (int): The maximum number of results to return. Defaults to 20.
        activityType (str): The type of activity to filter by. Options are "buy", "listing", "price_update", 
            "offer", or an empty string for no filter.
        gift_name (str | list): The name or list of names of gifts to filter.
        model (str | list): The model or list of models to filter.
        backdrop (str | list): The backdrop or list of backdrops to filter.
        symbol (str | list): The symbol or list of symbols to filter.
        min_price (int): The minimum price of the gifts to filter. Defaults to 0.
        max_price (int): The maximum price of the gifts to filter. Defaults to 100000.
        authData (str): The authentication data required for the API request.

    Returns:
        list: A list of dictionaries containing the market activity results.

    Raises:
        Exception: If authData is not provided.
        Exception: If max_price is less than min_price.
        Exception: If activityType is not one of the valid options.
        Exception: If gift_name, model, backdrop, or symbol are not strings or lists.
        Exception: If the API request fails.
    """

    URL = API_URL + "nfts/" + "search?" + f"offset={offset}" + f"&limit={limit}" + f"{SORTS[sort]}"

    try:
        min_price = int(min_price)
        max_price = int(max_price)
    except:
        raise Exception("portalsapi: marketActivity(): Error: min_price and max_price must be integers")

    if max_price < 100000:
        URL += f"&min_price={min_price}&max_price={max_price}"

    if authData == "":
        raise Exception("portalsapi: marketActivity(): Error: authData is required")
    if max_price < min_price:
        raise Exception("portalsapi: marketActivity(): Error: max_price must be greater than min_price")
    if activityType.lower() not in ["", "buy", "listing", "price_update", "offer"]:
        raise Exception("portalsapi: marketActivity(): Error: activityType may be empty, buy, listing, offer or price_update only.")

    if gift_name:
        if type(gift_name) == str:
            URL += f"&filter_by_collections={quote_plus(cap(gift_name))}"
        elif type(gift_name) == list:
            URL += f"&filter_by_collections={listToURL(gift_name)}"
        else:
            raise Exception("portalsapi: marketActivity(): Error: gift_name must be a string or list")
    if model:
        if type(model) == str:
            URL += f"&filter_by_models={quote_plus(cap(model))}"
        elif type(model) == list:
            URL += f"&filter_by_models={listToURL(model)}"
        else:
            raise Exception("portalsapi: marketActivity(): Error: model must be a string or list")
    if backdrop:
        if type(backdrop) == str:
            URL += f"&filter_by_backdrops={quote_plus(cap(backdrop))}"
        elif type(backdrop) == list:
            URL += f"&filter_by_backdrops={listToURL(backdrop)}"
        else:
            raise Exception("portalsapi: marketActivity(): Error: backdrop must be a string or list")
    if symbol:
        if type(symbol) == str:
            URL += f"&filter_by_symbols={quote_plus(cap(symbol))}"
        elif type(symbol) == list:
            URL += f"&filter_by_symbols={listToURL(symbol)}"
        else:
            raise Exception("portalsapi: marketActivity(): Error: symbol must be a string or list")
    if activityType:
        URL += f"&filter_by_activity_type={quote_plus(activityType.lower())}"

    URL += "&status=listed"

    HEADERS["Authorization"] = authData

    response = requests.get(URL, headers=HEADERS, impersonate="chrome110")
    if response.status_code != 200:
        raise Exception(f"portalsapi: marketActivity(): Error: status_code: {response.status_code}, response_text: {response.text}")

    return response.json()['results'] if response.json()['results'] else response.json()

def convertForListing(nft_id: str = "", price: float = 0):
    return {"nft_id": nft_id, "price": str(price)}

def convertForBuying(nft_id: str = "", owner_id: int = 0, price: float = 0):
    return {"id": nft_id, "owner_id": owner_id, "price": str(price)}

def bulkList(nfts: list = [], authData: str = "") -> dict:
    """
    Lists multiple NFTs for sale in bulk.

    Args:
        nfts (list): A non-empty list of dictionaries, each containing 'nft_id', and 'price' as keys.
        authData (str): The authentication data required for the API request.

    Returns:
        dict: A dictionary containing the response from the API if the request is successful.

    Raises:
        Exception: If authData is not provided.
        Exception: If nfts is not a non-empty list.
        Exception: If the API request fails or returns a non-200 status code.
    """

    URL = API_URL + "nfts/bulk-list"

    if authData == "":
        raise Exception("portalsapi: bulkList(): Error: authData is required")
    if type(nfts) != list or len(nfts) == 0:
        raise Exception("portalsapi: bulkList(): Error: nfts must be a non-empty list")

    HEADERS["Authorization"] = authData

    PAYLOAD = {
        "nft_prices": nfts
    }

    response = requests.post(URL, json=PAYLOAD, headers=HEADERS, impersonate="chrome110")
    if response.status_code not in [200, 204]:
        raise Exception(f"portalsapi: bulkList(): Error: status_code: {response.status_code}, response_text: {response.text}")

    return response.json() if response.status_code == 200 else None

def sale(nft_id: str = "", price: int|float = 0,authData: str = "") -> dict | None:
    """
    Lists a single NFT for sale.

    Args:
        nft_id (str): The unique identifier of the NFT to be listed.
        price (int|float): The price at which the NFT should be listed for sale.
        authData (str): The authentication data required for the API request.

    Returns:
        dict: A dictionary containing the response from the API if the request is successful.
        None: Likely 204 no content response from the API.

    Raises:
        Exception: If authData is not provided.
        Exception: If nft_id is not provided.
        Exception: If price is not provided or not a number.
        Exception: If the API request fails or returns a non-200 status code.
    """

    URL = API_URL + "nfts/bulk-list"

    if authData == "":
        raise Exception("portalsapi: sale(): Error: authData is required")
    if not nft_id:
        raise Exception("portalsapi: sale(): Error: nft_id is required")
    if price == 0 or type(price) not in [int, float]:
        raise Exception("portalsapi: sale(): Error: price error")

    nfts = [{"nft_id": nft_id, "price": str(price)}]

    HEADERS["Authorization"] = authData

    PAYLOAD = {
        "nft_prices": nfts
    }

    response = requests.post(URL, json=PAYLOAD, headers=HEADERS, impersonate="chrome110")
    if response.status_code not in [200, 204]:
        raise Exception(f"portalsapi: sale(): Error: status_code: {response.status_code}, response_text: {response.text}")

    return response.json() if response.status_code == 200 else None

def buy(nft_id: str = "", owner_id: int = 0, price: int|float = 0, authData: str = "") -> dict | None:
    """
    Buys a gift with the given nft_id from the given owner_id at the given price.

    Args:
        nft_id (str): The unique identifier of the NFT to be bought.
        owner_id (int): The Telegram ID of the user who owns the NFT.
        price (int|float): The price at which the NFT should be bought.
        authData (str): The authentication data required for the API request.

    Returns:
        dict: A dictionary containing the response from the API if the request is successful.
        None: Likely 204 no content response from the API.

    Raises:
        Exception: If authData is not provided.
        Exception: If nft_id is not provided.
        Exception: If owner_id is not provided.
        Exception: If price is not provided or not a number.
        Exception: If the API request fails or returns a non-200 status code.
    """
    URL = API_URL + "nfts"

    if authData == "":
        raise Exception("portalsapi: buy(): Error: authData is required")
    if not nft_id:
        raise Exception("portalsapi: buy(): Error: nft_id is required")
    if owner_id == 0:
        raise Exception("portalsapi: buy(): Error: owner_id is required")
    if price == 0 or type(price) not in [int, float]:
        raise Exception("portalsapi: buy(): Error: price error")

    HEADERS["Authorization"] = authData

    nfts = [{"id": nft_id, "owner_id": owner_id, "price": str(price)}]
    '''
    {"nft_details":[{"id":"aaaa8eb4-deac-4ba2-aa5c-ea79c73f0d5b","owner_id":6540727795,"price":"1.85"}]}
    '''

    PAYLOAD = {
        "nft_details": nfts
    }

    response = requests.post(URL, json=PAYLOAD, headers=HEADERS, impersonate="chrome110")
    if response.status_code not in [200, 204]:
        raise Exception(f"portalsapi: buy(): Error: status_code: {response.status_code}, response_text: {response.text}")

    return response.json() if response.status_code == 200 else None

def makeOffer(nft_id: str = "", offer_price: float = 0, expiration_days: int = 7, authData: str = "") -> dict | None:
    """
    Creates an offer for a specified NFT.

    Args:
        nft_id (str): The unique identifier of the NFT for which the offer is being made.
        offer_price (float): The price of the offer.
        expiration_days (int): The number of days until the offer expires. 0 - no expiration, 7 - 7 days.
        authData (str): The authentication data required for the API request.

    Returns:
        dict: A dictionary containing the response from the API if the request is successful.
        None: Likely 204 no content response from the API.

    Raises:
        Exception: If nft_id is not provided.
        Exception: If offer_price is not provided.
        Exception: If expiration_days is not 7 or 0.
        Exception: If authData is not provided.
        Exception: If the API request fails or returns a non-200 status code.
    """

    URL = API_URL + "offers"

    if not nft_id:
        raise Exception("portalsapi: makeOffer(): Error: nft_id is required")
    if offer_price == 0:
        raise Exception("portalsapi: makeOffer(): Error: offer_price is required")
    if expiration_days not in [7, 0]:
        raise Exception("portalsapi: makeOffer(): Error: expiration_days must be 7 or 0")
    if authData == "":
        raise Exception("portalsapi: makeOffer(): Error: authData is required")

    HEADERS["Authorization"] = authData

    PAYLOAD = {
        "offer": {
            "nft_id": nft_id,
            "price": str(offer_price)
            }
    }

    if expiration_days == 7:
        PAYLOAD.update({"expiration_days": 7})

    response = requests.post(URL, json=PAYLOAD, headers=HEADERS, impersonate="chrome110")
    if response.status_code not in [200, 204]:
        raise Exception(f"portalsapi: makeOffer(): Error: status_code: {response.status_code}, response_text: {response.text}")

    return response.json() if response.status_code == 200 else None

def cancelOffer(offer_id: str = "", authData: str = "") -> dict | None:
    """
    Cancels an offer with the given offer_id.

    Args:
        offer_id (str): The unique identifier of the offer to be canceled.
        authData (str): The authentication data required for the API request.

    Returns:
        dict: A dictionary containing the response from the API if the request is successful.
        None: Likely 204 no content response from the API.

    Raises:
        Exception: If offer_id is not provided.
        Exception: If authData is not provided.
        Exception: If the API request fails or returns a non-200 status code.
    """
    URL = API_URL + "offers/" + f"{offer_id}" + "/cancel"

    if not offer_id:
        raise Exception("portalsapi: cancelOffer(): Error: offer_id is required")
    if authData == "":
        raise Exception("portalsapi: cancelOffer(): Error: authData is required")

    HEADERS["Authorization"] = authData

    response = requests.post(URL, headers=HEADERS, impersonate="chrome110")
    if response.status_code not in [200, 204]:
        raise Exception(f"portalsapi: cancelOffer(): Error: status_code: {response.status_code}, response_text: {response.text}")

    return response.json() if response.status_code == 200 else None

def changePrice(nft_id: str = "", price: float = 0, authData: str = "") -> dict | None:
    """
    Updates the price of a specified NFT.

    Args:
        nft_id (str): The unique identifier of the NFT for which the price is being updated.
        price (float): The new price to set for the NFT.
        authData (str): The authentication data required for the API request.

    Returns:
        dict: A dictionary containing the response from the API if the request is successful.
        None: Likely 204 no content response from the API.

    Raises:
        Exception: If nft_id is not provided.
        Exception: If price is not provided.
        Exception: If authData is not provided.
        Exception: If the API request fails or returns a non-200 status code.
    """

    URL = API_URL + "nfts/" + f"{nft_id}/" + "list"

    if not nft_id:
        raise Exception("portalsapi: changePrice(): Error: nft_id is required")
    if price == 0:
        raise Exception("portalsapi: changePrice(): Error: price is required")
    if authData == "":
        raise Exception("portalsapi: changePrice(): Error: authData is required")

    HEADERS["Authorization"] = authData

    PAYLOAD = {
        "price": str(price)
    }

    response = requests.post(URL, json=PAYLOAD, headers=HEADERS, impersonate="chrome110")
    if response.status_code not in [200, 204]:
        raise Exception(f"portalsapi: changePrice(): Error: status_code: {response.status_code}, response_text: {response.text}")

    return response.json() if response.status_code == 200 else None

class PortalsGift:
    """
    Attributes:
        id (str): Portals ID of the gift
        tg_id (int): Telegram ID of the gift
        collection_id (str): Portals ID of the gift collection
        owner_id (int): ID of the gift owner
        name (str): Name of the gift
        photo_url (str): Photo URL of the gift (model + bg + symbol preview)
        price (str): Price of the gift
        model (str): Model of the gift
        model_rarity (float): Model rarity of the gift
        symbol (str): Symbol of the gift
        symbol_rarity (float): Symbol rarity of the gift
        backdrop (str): Backdrop of the gift
        backdrop_rarity (float): Backdrop rarity of the gift
        listed_at (str): Time the gift was listed
        status (str): (usually listed)
        animation_url (str): Lottie animation URL of the gift
        emoji_id (str): Telegram custom emoji ID of the gift
        floor_price (str): Floor price of the gift (not the model)
        unlocks_at (str): Time of when the gift will be available to be minted
    """
    def __init__(self, data: dict):
        self.__dict__ = data
    
    def toDict(self):
        return self.__dict__
    
    @property
    def id(self):
        return self.__dict__["id"]
    
    @property
    def tg_id(self):
        return self.__dict__["external_collection_number"]
    
    @property
    def collection_id(self):
        return self.__dict__["collection_id"]
    
    @property
    def owner_id(self):
        return self.__dict__["owner_id"]
    
    @property
    def name(self):
        return self.__dict__["name"]
    
    @property
    def photo_url(self):
        return self.__dict__["photo_url"]
    
    @property
    def price(self):
        return float(self.__dict__["price"]) if self.__dict__["price"] else None
    
    @property
    def model(self):
        for attr in self.__dict__["attributes"]:
            if attr["type"] == "model":
                return attr["value"]
        return None
    
    @property
    def model_rarity(self):
        for attr in self.__dict__["attributes"]:
            if attr["type"] == "model":
                return attr["rarity_per_mille"]
        return None
    
    @property
    def symbol(self):
        for attr in self.__dict__["attributes"]:
            if attr["type"] == "symbol":
                return attr["value"]
        return None
    
    @property
    def symbol_rarity(self):
        for attr in self.__dict__["attributes"]:
            if attr["type"] == "symbol":
                return attr["rarity_per_mille"]
        return None
    
    @property
    def backdrop(self):
        for attr in self.__dict__["attributes"]:
            if attr["type"] == "backdrop":
                return attr["value"]
        return None
    
    @property
    def backdrop_rarity(self):
        for attr in self.__dict__["attributes"]:
            if attr["type"] == "backdrop":
                return attr["rarity_per_mille"]
        return None
    
    @property
    def listed_at(self):
        return self.__dict__["listed_at"]
    
    @property
    def status(self):
        return self.__dict__["status"]
    
    @property
    def animation_url(self):
        return self.__dict__["animation_url"]
    
    @property
    def emoji_id(self):
        return self.__dict__["emoji_id"]
    
    @property
    def floor_price(self):
        return float(self.__dict__["floor_price"]) if self.__dict__["floor_price"] else None
    
    @property
    def unlocks_at(self):
        return self.__dict__["unlocks_at"]
    
def withdrawPortals(amount: float = 0, wallet: str = "", authData: str = "") -> dict:
    """
    Withdraw Portals from the user's wallet to an external address.

    Args:
        amount (float): The amount of Portals to withdraw.
        wallet (str): The external address to withdraw to.
        authData (str): The authentication data required for the API request.

    Returns:
        dict: A dictionary containing ID of the withdrawal.

    Raises:
        Exception: If amount is not provided.
        Exception: If wallet is not provided.
        Exception: If authData is not provided.
        Exception: If the API request fails or returns a non-200 status code.
    """
    URL = API_URL + "users/wallets/withdraw"

    if amount == 0:
        raise Exception("portalsapi: withdrawPortals(): Error: amount is required")
    if not wallet:
        raise Exception("portalsapi: withdrawPortals(): Error: wallet is required")
    if not authData:
        raise Exception("portalsapi: withdrawPortals(): Error: authData is required")
    
    HEADERS["Authorization"] = authData

    PAYLOAD = {
        "amount": str(amount),
        "external_address": wallet
        }
    
    response = requests.post(URL, json=PAYLOAD, headers=HEADERS, impersonate="chrome110")
    if response.status_code not in [200, 204]:
        raise Exception(f"portalsapi: withdrawPortals(): Error: status_code: {response.status_code}, response_text: {response.text}")

    return response.json() if response.status_code == 200 else None