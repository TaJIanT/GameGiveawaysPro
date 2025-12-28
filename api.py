# -*- coding: utf-8 -*-
import requests
import json
import os

CHEAPSHARK_API = "https://www.cheapshark.com/api/1.0/deals"
GAMERPOWER_API = "https://www.gamerpower.com/api/giveaways"

REQUEST_TIMEOUT = 5
CACHE_FILE = "gamescache.json"

STORE_IDS = "1,3,7,25"  # Steam, GMG, GOG, Epic

PLACEHOLDER_IMG = "https://via.placeholder.com/320x220/118272/2c55e?text=GAME"

class GameAPI:
    def __init__(self, usegamerpower=True):
        self.usegamerpower = usegamerpower
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

    def set_use_gamerpower(self, value):
        self.usegamerpower = bool(value)

    def fetch_all_games(self, limit=40):
        games = []

        # Бесплатные (почти free) от CheapShark
        try:
            games.extend(self.fetch_cheapshark_free(12))
        except Exception as e:
            print(f"CHEAPSHARK FREE ERROR: {e}")

        # Giveaway от GamerPower (Steam)
        if self.usegamerpower:
            try:
                games.extend(self.fetch_gamerpower_steam(10))
            except Exception as e:
                print(f"GAMERPOWER ERROR: {e}")

        # Скидки (отдельно) от CheapShark
        try:
            games.extend(self.fetch_cheapshark_discounts(35))
        except Exception as e:
            print(f"CHEAPSHARK DISCOUNTS ERROR: {e}")

        if not games:
            cache = self.load_cache()
            return cache[:limit] if cache else []

        out = self.deduplicate_games(games)[:limit]
        self.save_cache(out)
        return out

    def fetch_cheapshark_free(self, limit=20):
        params = {
            "storeID": STORE_IDS,
            "upperPrice": 2.0,
            "sortBy": "Savings",
            "pageSize": 60,
        }
        r = self.session.get(CHEAPSHARK_API, params=params, timeout=3)
        data = r.json()

        games = []
        for deal in data[:limit]:
            saleprice = float(deal.get("salePrice", 0) or 0)
            savings = float(deal.get("savings", 0) or 0)
            if saleprice > 0 or savings < 95:
                continue

            title = deal.get("title", "Game")
            storeid = str(deal.get("storeID", 0))
            storename = self.store_name(storeid)
            img = deal.get("thumb") or PLACEHOLDER_IMG
            link = f"https://www.cheapshark.com/redirect?dealID={deal.get('dealID', '')}"

            games.append({
                "id": f"cs-free-{deal.get('dealID','')}",
                "title": title,
                "platform": storename,
                "platformkey": storename.lower().replace(" ", ""),
                "genre": "Раздача/почти бесплатно",
                "developer": storename,
                "description": f"Скидка {savings:.0f}% (CheapShark).",
                "price": "FREE",
                "period": "TBD",
                "image": img,
                "link": link,
                "hot": True,
                "ratingscore": float(deal.get("dealRating", 0) or 0),
                "source": "CheapShark",
                "tags": ["Deal", storename],
                "end_at": None,
            })
        return games

    def fetch_cheapshark_discounts(self, limit=40, max_price=15.0, min_savings=50.0):
        params = {
            "storeID": STORE_IDS,
            "upperPrice": max_price,
            "sortBy": "Savings",
            "pageSize": 60,
            "onSale": 1,
        }
        r = self.session.get(CHEAPSHARK_API, params=params, timeout=3)
        data = r.json()

        games = []
        for deal in data:
            try:
                saleprice = float(deal.get("salePrice", 0) or 0)
                normalprice = float(deal.get("normalPrice", 0) or 0)
                savings = float(deal.get("savings", 0) or 0)
            except Exception:
                continue

            if saleprice <= 0:
                continue
            if savings < min_savings:
                continue

            title = deal.get("title", "Game")
            storeid = str(deal.get("storeID", 0))
            storename = self.store_name(storeid)
            img = deal.get("thumb") or PLACEHOLDER_IMG
            link = f"https://www.cheapshark.com/redirect?dealID={deal.get('dealID', '')}"

            # price НЕ FREE => попадёт во вкладку "Скидки"
            price_text = f"{saleprice:.2f}$ (-{savings:.0f}%)"

            games.append({
                "id": f"cs-disc-{deal.get('dealID','')}",
                "title": title,
                "platform": storename,
                "platformkey": storename.lower().replace(" ", ""),
                "genre": "Скидка",
                "developer": storename,
                "description": f"Было {normalprice:.2f}$  стало {saleprice:.2f}$ ({savings:.0f}%).",
                "price": price_text,
                "period": "TBD",
                "image": img,
                "link": link,
                "hot": True,
                "ratingscore": float(deal.get("dealRating", 0) or 0),
                "source": "CheapShark",
                "tags": ["Discount", storename],
                "end_at": None,
            })

            if len(games) >= limit:
                break

        return games

    def fetch_gamerpower_steam(self, limit=10):
        params = {"platform": "steam", "type": "game", "sort-by": "date"}
        r = self.session.get(GAMERPOWER_API, params=params, timeout=3)
        data = r.json()

        games = []
        for item in data[:limit]:
            if item.get("status") == "Ended":
                continue
            title = item.get("title", "")
            img = item.get("image") or PLACEHOLDER_IMG
            link = item.get("openGiveawayURL", "") or item.get("open_giveaway_url", "")

            games.append({
                "id": f"gp-steam-{item.get('id', '')}",
                "title": title,
                "platform": "Steam",
                "platformkey": "steam",
                "genre": item.get("type", "Giveaway"),
                "developer": "GamerPower",
                "description": (item.get("description", "") or "")[:220],
                "price": "FREE",
                "period": item.get("endDate") or "TBD",
                "image": img,
                "link": link,
                "hot": item.get("status") == "Active",
                "ratingscore": 9.0,
                "source": "GamerPower Steam",
                "tags": ["Giveaway", "Steam"],
                "end_at": item.get("endDate"),
            })
        return games

    def store_name(self, storeid):
        return {
            "1": "Steam",
            "2": "GamersGate",
            "3": "GreenManGaming",
            "7": "GOG",
            "25": "Epic Games",
        }.get(storeid, "Store")

    def deduplicate_games(self, games):
        seen = set()
        out = []
        for g in games:
            gid = g.get("id")
            if gid and gid not in seen:
                seen.add(gid)
                out.append(g)
        return out

    def load_cache(self):
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def save_cache(self, games):
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(games, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
