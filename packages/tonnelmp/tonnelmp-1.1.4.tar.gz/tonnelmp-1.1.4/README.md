[![pypi](https://img.shields.io/pypi/v/tonnelmp.svg)](https://pypi.org/project/tonnelmp/) [![stars](https://img.shields.io/github/stars/bleach-hub/tonnelmp?style=social)](https://github.com/bleach-hub/tonnelmp/stargazers) [![Me](https://img.shields.io/badge/Telegram-@perfectlystill-blue?logo=telegram)](https://t.me/perfectlystill) [![Updates & Devs chat](https://img.shields.io/badge/Telegram-@giftsdevs-blue?logo=telegram)](https://t.me/giftsdevs)

# ***Tonnel Marketplace API***

This is a simple module that will help you interacting with Tonnel Marketplace API. Tested almost every API myself so you dont have to blindly test it.

*[Join our Telegram chat!](https://t.me/giftsdevschat)*

#### Functionality

***Gifts:***

- Searching for gifts with a lot of filters available
- Get all floor prices for all the gifts / models
- Buying, listing for sale, cancelling the sale
- Minting gift, returning it to your telegram account
- Retrieving gifts sale history
- *[SOON] Creating buy orders, staking gifts*

***Auctions:***

- Searching for auctions
- Bidding, creating auction, cancelling auction

***Giveaways:***

- Retrieving giveaway info
- Joining giveaway
- *[SOON] Creating giveaway*

***Account:***

- Retrieving balances, memo etc.
- Withdrawing funds
- Switching internal purchase on/off

## Installing

```python
pip install tonnelmp
```

## [IMPORTANT] Where to get Auth Data

**Most of the functions require your tonnel authentication data, so please don't skip this section of documentation.**

You can get it pretty easily. Go to [market.tonnel.network](https://market.tonnel.network/), login to your account, then open browser console (ctrl + shift + c on windows)

Then navigate to Application tab -> Storage -> Local Storage -> https://market.tonnel.network/ -> web-initData -> copy the value next to it **entirely**

## Change log

#### Version 1.0.3

- Fixed `wtf` module not importing correctly

#### Version 1.0.4

- Improved `buyGift()` function. Now you can pass `receiver: int` arg to send the gift to someone else by telegram user id. Also added `anonymously: bool, showPrice: bool` args. Defaults for both - `False`.
- Added `returnGift()` function.
- Added `withdraw()` function.
- Added `mintGift()` function.
- Added `placeBid()` function.
- Added `switchTransfer()` function.
- Updated documentation

#### Versions 1.0.4.1 - 1.0.4.2

- Minor changes - replaced `response.text` with status code on exception due to too many lines in it (trashes out logging).
- forgot to add myGifts() to init XD, added and the function should work

#### Version 1.0.5

- Improved `getGifts(), getAuctions(), saleHistory()` functions. Now you can pass model/backdrop/symbol with or without rarity percentage included *(before this update you could only pass without rarity percentage)*
- Example: `getGifts(gift_name="toy bear", model="wizard")` - without rarity percentage; `getGifts(gift_name="toy bear", model="wizard (1.5%)") `- with rarity percentage included

#### Version 1.0.5.1

- Added `unlockListing()` function
- Updated documentation

#### Version 1.0.6

- Added `giveawayInfo()` and `joinGiveaway()` functions
- Updated documentation

#### Version 1.0.7

- Added `filterStats()` and `filterStatsPretty()` functions
- Changed `user_auth` arg in most of the functions to `authData` because it was annoying me xd
- Updated `joinGiveaway()` function to use chrome110 impersonation

#### Version 1.1.1

- Fixed `getGifts()` returning 0 len list for gifts `Durov's Cap` and `Jack-in-the-Box`
- Added `premarket, telegramMarketplace, mintable, bundle` bool parameters to `getGifts()`
- Added `giftData()` function
- Updated `filterStatsPretty()` function.
- Updated `Gift` class
- *More info in updated documentation.*

#### Version 1.1.2

- Fixed searching gifts with apostrophes in name/model

#### Version 1.1.3

- **Fixed 403 error**. *Thanks to boostNT and Alexander <3*
- Please send your feedback if you still get an error. Will try to fix it ASAP.
- Currently working on adding proxies support since freeman isn't really friendly about what you guys do :D

#### Version 1.1.4

- Fixed `gift_name` not adding to filters in `saleHistory()` and `getAuctions()`

## Some returns examples:

#### Gift example:

```python
from tonnelmp import getGifts
print(getGifts(gift_name="toy bear", limit=1))
```

`limit` will be the maximum len of the list.

**Output (list object with dicts):**

```python
[
	{
	'gift_num': 35531,
	'customEmojiId': '5289634279544876303',
	'gift_id': 4840785,
	'name': 'Toy Bear',
	'model': 'Zebra (1.5%)',
	'asset': 'TON',
	'symbol': 'Rabbit (0.2%)',
	'backdrop': 'Burgundy (2%)',
	'availabilityIssued': 0,
	'availabilityTotal': 0,
	'backdropData': {},
	'message_in_channel': 0,
	'price': 12.9,
	'status': 'forsale',
	'limited': False,
	'auction': None,
	'export_at': '2025-05-28T12:25:01.000Z'
	}
]
```

`gift_num` - telegram gift number

`customEmojiId` - telegram custom emoji id

`gift_id` - tonnel gift id

`name` - gift name

`model` - gift model

`asset` - asset name

`symbol` - symbol name

`backdrop` - backdrop name

`price` - price in TON without 10% fee.

`status` - status of the gift - forsale / auction (not sure about auction sorry)

`auction` - either None or auction data in dict

`export_at` - time of when the gift will be mintable

`bundleData` *[only for bundles]* - list of dicts / None

`premarket` - Bool (true / false), whether gift is on premarket or not

#### Balances example:

```python
from tonnelmp import info
print(info(authData="your_auth_data"))
```

**Output:**

```python
{
	'status': 'success',
	'balance': 123.123123123, # your ton balance
	'memo': ' ... ', # your memo
	'transferGift': False, # false = internal purchase
	'usdtBalance': 123.123123123, # your usdt balance
	'tonnelBalance': 123.123123123, # your tonnel balance
	'referrer': 123123123, # your referrer telegram id
	'photo_url': ' ... ', # your telegram pfp url
	'name': ' ... ' # your telegram name
}
```

# Documentation

## Gift Class

Wrapper for gift dictionary

#### Attributes

- .gift_num
- .gift_id
- .name
- .model
- .backdrop
- .symbol
- .price
- .status
- .asset
- .auction
- .premarket
- .bundleData

.. and more

#### Example

```python
from tonnelmp import Gift, getGifts()
gift = Gift(getGifts(limit=1, sort="latest")[0])
print(gift.name, gift.gift_num, gift.gift_id, gift.price)
```

**Output:**

```python
Winter Wreath 23548 4848019 9.8
```

## Functions:

#### getGifts()

```python
getGifts(gift_name: str, model: str, backdrop: str, symbol: str, gift_num: int, page: int, limit: int, sort: str, price_range: list | int, asset: str, premarket: bool = False, telegramMarketplace: bool = False, mintable: bool = False, bundle: bool = False, authData: str) -> list
```

- Returns a list with dict objects containing gifts details.
- Now supports `premarket`, `telegramMarketplace`, `mintable` gifts and bundles.
- Available options:
  *sort (Default="price_asc"):* `"price_asc", "price_desc", "latest", "mint_time", "rarity", "gift_id_asc", "gift_id_desc"`
  *asset (Default="TON"):* `"TON", "USDT", "TONNEL"`
- limit arg maximum = 30 (as far as i know)

#### getAuctions()

```python
getAuctions(gift_name: str, model: str, backdrop: str, symbol: str, gift_num: int, page: int, limit: int, sort: str, price_range: list | int=0, asset: str, authData: str="") -> list
```

- Get auctions with optional filters. Doesnt require anything at all.
- Available options:
  *sort:* `"ending_soon", "latest", "highest_bid", "latest_bid"`
  *limit maximum* = 30
  *asset:* `"TON", "USDT", "TONNEL"`

#### myGifts()

```python
myGifts(listed: bool, page: int, limit: int, authData: str) -> list:
```

- Returns a list with dict objects containing gifts details.
- **Required: `authData`**
- Available options:
  *listed (Default=True):* `True / False.` If False, will return unlisted gifts.

#### listForSale()

```python
listForSale(gift_id: int, price: int | float, authData: str) -> dict
```

- List for sale a gift with known gift_id *(tonnel gift_id, **not telegram gift_num**; can be retrieved from myGifts()/getGifts())*
- Returns dict object with status. Either success or error.
- **Required: `authData, gift_id, price`**

#### cancelSale()

```python
cancelSale(gift_id: int,authData: str) -> dict
```

- Cancel sale of the gift with known gift_id
- Returns dict object with status. Either success or error.
- **Required: `authData, gift_id`**

#### unlockListing()

```python
unlockListing(authData: str, gift_id: int) -> dict:
```

- Unlock listing for a known gift_id (cost 0.1 TON)
- You can check if your gift needs to be unlocked by using `myGifts(listed=False, authData="")`. If `'limited': True` in the response, your gift needs to be unlocked.
- **Requires: `authData, gift_id; 0.1 TON on the balance`**

#### saleHistory()

*idk why but this function requires auth :D you can try putting empty authData, maybe i've done something wrong*

```python
saleHistory(authData: str, page: int, limit: int, type: str, gift_name: str, model: str, backdrop: str, sort: str) -> list
```

- Returns a list with dict objects containing gifts details.
- **Required: `authData`**
- Available options:
  *sort (Default="latest"):* `"latest", "price_asc", "price_desc", "gift_id_asc", "gift_id_desc"`
  *type (Default="ALL"):* `"ALL", "SALE", "INTERNAL_SALE", "BID"`
- limit maximum = 50

#### withdraw()

```python
withdraw(wallet: str, authData: str, amount: int | float, asset: str = "TON") -> dict:
```

- Withdraw amount of asset to specified TON wallet address.
- **Requires: `wallet, authData, amount`**
- *Options:* `asset - "TON", "USDT", "TONNEL"`

#### returnGift()

```python
returnGift(gift_id: int, authData: str) -> dict:
```

*Not tested yet*

- Return gift from Tonnel Marketplace to your Telegram account.
- **Requires: `gift_id, authData`**

#### mintGift()

```python
mintGift(authData: str, wallet: str, gift_id: int) -> dict:
```

*Not tested yet*

- Mints gift to specified TON wallet address.
- **Minting cost 0.3 TON**
- **Requires: `authData, wallet, gift_id; 0.3 TON on the balance`**

#### switchTransfer()

```python
switchTransfer(authData: str, transferGift: bool) -> dict:
```

- Switches internal transfer mode on your Tonnel Marketplace account.
- **Requires: `authData`**

#### info()

```python
info(authData: str) -> dict
```

- Returns a dict object containing your balances, memo, referrer etc.
- **Requires: `authData`**

#### buyGift()

```python
buyGift(gift_id: int, price: int | float, authData: str, receiver: int, anonymously: bool = False, showPrice: bool = False) -> dict
```

- Buy a gift with known gift_id and price in TON. // price - raw price (you dont have to multiply it by 1.1). both params can be retrieved from getGifts()
- *[Not tested yet] Optional*: `receiver` - Telegram user id of the receiver (if you want to send the gift to someone else); `anonymously` - bool value, wether to show user who bought the gift or not; `showPrice` - bool value, wether to show user the price or not
- **Requires: `gift_id, price, authData`**
- Returns dict object with status. Either success or error.

#### createAuction()

```python
createAuction(gift_id: int, starting_bid: int | float, authData: str, duration: int) -> dict
```

- Create auction for the gift with known gift_id.
- **Requires: `gift_id, starting_bid, authData, duration`**
- Returns dict object with status. Either success or error.
- Available options:
  *duration (Default=1):* Duration in hours. Can be one of these options - `[1, 2, 3, 6, 12, 24]`

#### cancelAuction()

```python
cancelAuction(auction_id: str, authData: str) -> dict
```

- Cancel auction with known auction_id (can be retrieved from getAuctions() or mygifts())
- **Requires: `auction_id, authData`**
- Returns dict object with status. Either success or error

#### placeBid()

```python
placeBid(auction_id: str, amount: int|float, authData: str, asset: str="TON") -> dict:
```

*Not tested yet*

- Place a bid on known `auction_id`
- Not recommended to change asset value (i dont think its possible to bid in USDT/TONNEL)
- **Requires: `auction_id, amount, authData`**

#### giveawayInfo()

```python
giveawayInfo(giveaway_id: str, authData: str) -> dict:
```

- Retrieve giveaway info from giveaway_id
- **Requires: `authData, giveaway_id`**

#### joinGiveaway()

```python
joinGiveaway(giveaway_id: str, authData: str, ticketCount: int | None=None) -> dict
```

- Join giveaway with known giveaway_id
- Ticketcount is optional argument. Required if giveaway is paid.
- **Requires: `authData, giveaway_id`**

#### filterStats()

```python
filterStats(authData: str) -> dict:
```

- Completely new function added by Freeman (big W), saves you a lot of `getGifts()` requests if needed floor for model / backdrop etc.
- Returns ungrouped dictionary with all gifts and models splitted by underscore containing raw floorprice and count of the model (with rarity) on the market.
- **Requires: `authData`**
- Return format: `{status: "success/error", "data": {"Toy Bear_Wizard (1.5%)": {"floorprice": int, "howMany": int}}}`

#### filterStatsPretty()

```python
filterStatsPretty(authData: str) -> dict:
```

- Prettier version of `filterStats()`.
- Returns grouped dictionary of all the gifts and models.
- Latest changes: now you dont need to capitalize letters in keys and you dont need rarity in model. Rarity is now included in every model key.
- Example: `filterStatsPretty(authData)['data']['toy bear']['wizard']` - will return `{'floorPrice': int, 'howMany': int, 'rarity': float} `, floorprice is raw (without 10% fee added up). *(rarity and capitalization required !!!)*
- Also now you can get `floorPrice` and `howMany` for gift without model. Example: `filterStatsPretty(authData)['data']['toy bear']['data']` - will return `{'floorPrice': int, 'howMany': int}`
- **Requires: `authData`**

#### giftData()

```python
giftData(gift_id: int | str authData: str) -> dict
```

- Retrieve gift data for gift with known `gift_id`
- If `gift_id` starts with `-` , will return gift data + `bundleData`.
- **Requires: `gift_id, authData`**

## Examples

Getting gift floor for *Toy Bear* with model *Wizard*:

```python
from tonnelmp import Gift, getGifts
gift = Gift(getGifts(gift_name="toy bear", model="wizard", limit=1, sort="price_asc")[0]) 
print(gift.price) # this will print raw price (without 10% fee), remember that
```

Buying gift

```python
from tonnelmp import buyGift
myAuthData = " ... your auth data here ... "
print(buyGift(gift_id=123123, price=123.12, authData=myAuthData)) # will print status. This will buy gift NOT FOR 123.12 TON. Tonnel adds up 10%, so the final price will be 123.12 * 1.1, again, remember that.
```

Listing gift for sale

```python
from tonnelmp import listForSale
myAuthData = " ....... "
print(listForSale(gift_id=123, price=123, authData=myAuthData)
```

## Info

if you use this module please send your feedback [to my telegram](https://t.me/perfectlystill)

donations (will buy some tonnel whiskey thank you):

- ton: `UQC9f1mTuu2hKuBP_0soC5RVkq2mLp8uiPBBhn69vadU7h8W`
