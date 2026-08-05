# -*- coding: utf-8 -*-
import requests
import json
import os

CHEAPSHARK_API = "https://www.cheapshark.com/api/1.0/deals"
GAMERPOWER_API = "https://www.gamerpower.com/api/giveaways"

REQUEST_TIMEOUT = 10
CACHE_FILE = "gamescache.json"

# Правильные ID магазинов в CheapShark: 
# 1 (Steam), 3 (GMG), 7 (GOG), 11 (Humble Store), 25 (Epic Games), 31 (Fanatical)
STORE_IDS = "1,3,7,11,25,31" 
ALLOWED_STORES = ["1", "3", "7", "11", "25", "31"]
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

    def fetch_cheapshark_free(self, limit=20):
        # Собираем ссылку вручную, чтобы избежать кодирования запятых в %2C
        url = f"{CHEAPSHARK_API}?storeID={STORE_IDS}&upperPrice=2.0&sortBy=Savings&pageSize=60"
        try:
            r = self.session.get(url, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"❌ Ошибка CheapShark (Free): {e}")
            return []

        games = []
        for deal in data[:limit]:
            saleprice = float(deal.get("salePrice", 0) or 0)
            savings = float(deal.get("savings", 0) or 0)
            if saleprice > 0 or savings < 95: continue

            storename = self.store_name(str(deal.get("storeID", 0)))
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
        return games

    def fetch_cheapshark_discounts(self, limit=40, max_price=15.0, min_savings=50.0):
        # Собираем ссылку вручную, чтобы избежать кодирования запятых в %2C
        url = f"{CHEAPSHARK_API}?storeID={STORE_IDS}&upperPrice={max_price}&sortBy=Savings&pageSize=60&onSale=1"
        try:
            r = self.session.get(url, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"❌ Ошибка CheapShark (Discounts): {e}")
            return []

        games = []
        for deal in data:
            try:
                saleprice = float(deal.get("salePrice", 0) or 0)
                normalprice = float(deal.get("normalPrice", 0) or 0)
                savings = float(deal.get("savings", 0) or 0)
            except Exception: continue

            if saleprice <= 0 or savings < min_savings: continue

            storename = self.store_name(str(deal.get("storeID", 0)))
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
            if len(games) >= limit: break
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

    def fetch_vkplay_discounts(self, limit=10, min_savings=50.0):
        url = "https://api.vkplay.ru/play/v2/catalog/?sale=1&page=1"
        try:
            r = self.session.get(url, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"❌ Ошибка VK Play: {e}")
            return []

        games = []
        items = data.get("results", [])
        
        for item in items:
            try:
                title = item.get("name", "Неизвестная игра")
                cost_info = item.get("cost_info", {})
                saleprice = float(cost_info.get("actual_cost", 0))
                normalprice = float(cost_info.get("original_cost", 0))
                savings = float(cost_info.get("discount", 0))
                
                if saleprice <= 0 or normalprice <= 0:
                    continue
                    
                if savings < min_savings: 
                    continue

                slug = item.get("slug", "")
                link = f"https://vkplay.ru/play/game/{slug}/"

                games.append({
                    "id": f"vkplay-{item.get('id', '')}",
                    "title": title,
                    "platform": "VK Play",
                    "platformkey": "vkplay",
                    "genre": "Скидка",
                    "developer": "VK Play",
                    "description": f"Было {normalprice:.0f}₽  стало {saleprice:.0f}₽ ({savings:.0f}%).",
                    "worth": normalprice,
                    "price": f"{saleprice:.0f}₽ (-{savings:.0f}%)",
                    "period": "TBD",
                    "image": item.get("picture_horizontal") or PLACEHOLDER_IMG,
                    "link": link,
                    "hot": True,
                    "ratingscore": float(item.get("avg_rating", 0)),
                    "source": "VK Play",
                    "tags": ["Discount", "VK Play"],
                    "end_at": cost_info.get("date_end")
                })
            except Exception:
                continue
                
            if len(games) >= limit: 
                break
                
        return games

    def fetch_roblox_loot(self, limit=10):
        params = {"type": "loot", "sort-by": "date"}
        try:
            r = self.session.get(GAMERPOWER_API, params=params, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"❌ Ошибка GamerPower (Roblox): {e}")
            return []

        games = []
        for item in data:
            if item.get("status") == "Ended": continue
            
            title = item.get("title", "").lower()
            desc = item.get("description", "").lower()
            
            if "roblox" in title or "roblox" in desc:
                worth_str = str(item.get("worth", "0")).replace("$", "").replace("N/A", "0").replace(" ", "")
                worth_val = float(worth_str) if worth_str else 0.0

                games.append({
                    "id": f"gp-roblox-{item.get('id', '')}",
                    "title": item.get("title", ""),
                    "platform": "Roblox",
                    "platformkey": "roblox",
                    "genre": "Roblox Халява",
                    "developer": "Roblox",
                    "description": (item.get("description", "") or "")[:220],
                    "worth": worth_val,
                    "price": "FREE",
                    "period": item.get("endDate") or "TBD",
                    "image": item.get("image") or PLACEHOLDER_IMG,
                    "link": item.get("openGiveawayURL", "") or item.get("open_giveaway_url", ""),
                    "hot": True,
                    "ratingscore": 9.0,
                    "source": "Roblox Promo",
                    "tags": ["Roblox", "Loot"],
                    "end_at": item.get("endDate")
                })
                if len(games) >= limit: 
                    break
                    
        return games

    def store_name(self, storeid):
        return {
            "1": "Steam", "2": "GamersGate", "3": "GreenManGaming", 
            "7": "GOG", "11": "Humble Store", "25": "Epic Games", 
            "31": "Fanatical"
        }.get(storeid, "Store")
        
