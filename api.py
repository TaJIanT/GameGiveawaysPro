# -*- coding: utf-8 -*-
import requests
import json
import os
import urllib.parse

CHEAPSHARK_API = "https://www.cheapshark.com/api/1.0/deals"
GAMERPOWER_API = "https://www.gamerpower.com/api/giveaways"

REQUEST_TIMEOUT = 10
CACHE_FILE = "gamescache.json"

# ДОБАВЛЕНЫ НОВЫЕ МАГАЗИНЫ: 11 (Humble Bundle), 15 (Fanatical), 35 (IndieGala)
STORE_IDS = "1,3,7,11,15,25,35" 
ALLOWED_STORES = ["1", "3", "7", "11", "15", "25", "35"]
PLACEHOLDER_IMG = "https://via.placeholder.com/320x220/118272/2c55e?text=GAME"

class GameAPI:
    def __init__(self, usegamerpower=True):
        self.usegamerpower = usegamerpower
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json"
        })

    def set_use_gamerpower(self, value):
        self.usegamerpower = bool(value)

    def _get_cheapshark(self, params):
        try:
            r = self.session.get(CHEAPSHARK_API, params=params, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"⚠️ Прямой запрос к CheapShark заблокирован: {e}")
            print("🔄 Пробуем обойти блокировку IP через прокси-сервер...")

        query_string = urllib.parse.urlencode(params)
        target_url = f"{CHEAPSHARK_API}?{query_string}"
        
        try:
            proxy1 = f"https://api.allorigins.win/raw?url={urllib.parse.quote(target_url)}"
            r1 = self.session.get(proxy1, timeout=15)
            r1.raise_for_status()
            return r1.json()
        except Exception as e1:
            print(f"⚠️ Ошибка первого прокси: {e1}")
            try:
                proxy2 = f"https://api.codetabs.com/v1/proxy/?quest={urllib.parse.quote(target_url)}"
                r2 = self.session.get(proxy2, timeout=15)
                r2.raise_for_status()
                return r2.json()
            except Exception as e2:
                print(f"❌ Ошибка CheapShark: не удалось пробиться даже через прокси.")
                return []

    def fetch_cheapshark_free(self, limit=20):
        params = {"upperPrice": 0, "sortBy": "Savings", "pageSize": 60}
        data = self._get_cheapshark(params)

        games = []
        for deal in data:
            store_id = str(deal.get("storeID", 0))
            if store_id not in ALLOWED_STORES:
                continue

            saleprice = float(deal.get("salePrice", 0) or 0)
            savings = float(deal.get("savings", 0) or 0)
            if saleprice > 0 and savings < 95: 
                continue

            storename = self.store_name(store_id)
            games.append({
                "id": f"cs-free-{deal.get('dealID','')}",
                "title": deal.get("title", "Game"),
                "platform": storename,
                "platformkey": storename.lower().replace(" ", ""),
                "genre": "Раздача/почти бесплатно",
                "developer": storename,
                "description": f"Скидка {savings:.0f}% (CheapShark).",
                "worth": float(deal.get("normalPrice", 0) or 0),
                "price": "FREE",
                "period": "TBD",
                "image": deal.get("thumb") or PLACEHOLDER_IMG,
                "link": f"https://www.cheapshark.com/redirect?dealID={deal.get('dealID', '')}",
                "hot": True,
                "ratingscore": float(deal.get("dealRating", 0) or 0),
                "source": "CheapShark",
                "tags": ["Deal", storename],
                "end_at": None,
            })
            if len(games) >= limit: 
                break
        return games

    def fetch_cheapshark_discounts(self, limit=40, max_price=15.0, min_savings=50.0):
        params = {"upperPrice": int(max_price), "sortBy": "Savings", "pageSize": 60, "onSale": 1}
        data = self._get_cheapshark(params)

        games = []
        for deal in data:
            store_id = str(deal.get("storeID", 0))
            if store_id not in ALLOWED_STORES:
                continue

            try:
                saleprice = float(deal.get("salePrice", 0) or 0)
                normalprice = float(deal.get("normalPrice", 0) or 0)
                savings = float(deal.get("savings", 0) or 0)
            except Exception: 
                continue

            if saleprice <= 0 or savings < min_savings: 
                continue

            storename = self.store_name(store_id)
            games.append({
                "id": f"cs-disc-{deal.get('dealID','')}",
                "title": deal.get("title", "Game"),
                "platform": storename,
                "platformkey": storename.lower().replace(" ", ""),
                "genre": "Скидка",
                "developer": storename,
                "description": f"Было {normalprice:.2f}$  стало {saleprice:.2f}$ ({savings:.0f}%).",
                "worth": normalprice,
                "price": f"{saleprice:.2f}$ (-{savings:.0f}%)",
                "period": "TBD",
                "image": deal.get("thumb") or PLACEHOLDER_IMG,
                "link": f"https://www.cheapshark.com/redirect?dealID={deal.get('dealID', '')}",
                "hot": True,
                "ratingscore": float(deal.get("dealRating", 0) or 0),
                "source": "CheapShark",
                "tags": ["Discount", storename],
                "end_at": None,
            })
            if len(games) >= limit: 
                break
        return games

    def fetch_gamerpower_pc(self, limit=15):
        params = {"platform": "pc", "type": "game", "sort-by": "date"}
        try:
            r = self.session.get(GAMERPOWER_API, params=params, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"❌ Ошибка GamerPower (PC): {e}")
            return []

        games = []
        for item in data[:limit]:
            if item.get("status") == "Ended": continue
            
            gp_plat = str(item.get("platforms", "")).lower()
            if "epic" in gp_plat: p_name, p_key = "Epic Games", "epicgames"
            elif "gog" in gp_plat: p_name, p_key = "GOG", "gog"
            elif "steam" in gp_plat: p_name, p_key = "Steam", "steam"
            else: p_name, p_key = "PC", "pc"

            worth_str = str(item.get("worth", "0")).replace("$", "").replace("N/A", "0").replace(" ", "")
            worth_val = float(worth_str) if worth_str else 0.0

            games.append({
                "id": f"gp-pc-{item.get('id', '')}",
                "title": item.get("title", ""),
                "platform": p_name,
                "platformkey": p_key,
                "genre": item.get("type", "Giveaway"),
                "developer": "GamerPower",
                "description": (item.get("description", "") or "")[:220],
                "worth": worth_val,
                "price": "FREE",
                "period": item.get("endDate") or "TBD",
                "image": item.get("image") or PLACEHOLDER_IMG,
                "link": item.get("openGiveawayURL", "") or item.get("open_giveaway_url", ""),
                "hot": item.get("status") == "Active",
                "ratingscore": 9.0,
                "source": f"GamerPower {p_name}",
                "tags": ["Giveaway", p_name],
                "end_at": item.get("endDate"),
            })
        return games

    def fetch_gamerpower_loot(self, limit=15):
        params = {"type": "loot", "sort-by": "date"}
        try:
            r = self.session.get(GAMERPOWER_API, params=params, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"❌ Ошибка GamerPower (Loot): {e}")
            return []
        
        games = []
        for item in data[:limit]:
            if item.get("status") == "Ended": continue
            
            worth_str = str(item.get("worth", "0")).replace("$", "").replace("N/A", "0").replace(" ", "")
            worth_val = float(worth_str) if worth_str else 0.0

            games.append({
                "id": f"gp-loot-{item.get('id', '')}",
                "title": item.get("title", ""),
                "platform": "Ключи",
                "platformkey": "loot",
                "genre": "Loot",
                "developer": "GamerPower",
                "description": (item.get("description", "") or "")[:220],
                "worth": worth_val,
                "price": "FREE",
                "period": item.get("endDate") or "TBD",
                "image": item.get("image") or PLACEHOLDER_IMG,
                "link": item.get("openGiveawayURL", "") or item.get("open_giveaway_url", ""),
                "hot": item.get("status") == "Active",
                "ratingscore": 9.0,
                "source": "GamerPower Loot",
                "tags": ["Loot", "Software"],
                "end_at": item.get("endDate")
            })
        return games

    def store_name(self, storeid):
        # ОБНОВЛЕННЫЙ СЛОВАРЬ ИМЕН
        return {
            "1": "Steam", "2": "GamersGate", "3": "GreenManGaming", 
            "7": "GOG", "11": "Humble Bundle", "15": "Fanatical", 
            "25": "Epic Games", "35": "IndieGala"
        }.get(storeid, "Store")
