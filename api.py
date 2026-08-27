# -*- coding: utf-8 -*-
import requests
import json
import os
import urllib.parse
import urllib.request
import re

CHEAPSHARK_API = "https://www.cheapshark.com/api/1.0/deals"
GAMERPOWER_API = "https://www.gamerpower.com/api/giveaways"
ROBLOX_CODES_API = "https://raw.githubusercontent.com/blox-services/roblox-promocodes/main/codes.json"

REQUEST_TIMEOUT = 10
CACHE_FILE = "gamescache.json"

# Правильные ID: 1(Steam), 3(GMG), 7(GOG), 11(Humble), 15(Fanatical), 25(Epic), 30(IndieGala)
STORE_IDS = "1,3,7,11,15,25,30" 
ALLOWED_STORES = ["1", "3", "7", "11", "15", "25", "30"]
PLACEHOLDER_IMG = "https://via.placeholder.com/320x220/118272/2c55e?text=GAME"

class GameAPI:
    def __init__(self, usegamerpower=True):
        self.usegamerpower = usegamerpower
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "GameGiveawaysPro Bot (https://github.com/TaJIanT/GameGiveawaysPro)",
            "Accept": "application/json"
        })

    def set_use_gamerpower(self, value):
        self.usegamerpower = bool(value)

    def translate_to_ru(self, text):
        if not text or not text.strip():
            return ""
        try:
            clean_text = text[:400] 
            encoded_text = urllib.parse.quote(clean_text)
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ru&dt=t&q={encoded_text}"
            
            # Маскируемся под обычный браузер Chrome, чтобы Google не блокировал переводы
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            # Делаем запрос в обход стандартной сессии бота
            r = requests.get(url, headers=headers, timeout=5)
            
            if r.status_code == 200:
                data = r.json()
                translated = "".join([sentence[0] for sentence in data[0]])
                return translated
        except Exception as e:
            print(f"⚠️ Ошибка перевода: {e}")
        return text 

    def _get_cheapshark(self, target_url):
        try:
            r = self.session.get(target_url, timeout=REQUEST_TIMEOUT)
            if r.status_code == 200:
                return r.json()
        except:
            pass

        try:
            req = urllib.request.Request(target_url, headers={"User-Agent": "python-urllib/3.9"})
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
                if response.status == 200:
                    return json.loads(response.read().decode('utf-8'))
        except:
            pass

        encoded_url = urllib.parse.quote(target_url)
        try:
            r = requests.get(f"https://api.allorigins.win/get?url={encoded_url}", timeout=15)
            if r.status_code == 200:
                wrapper = r.json()
                if "contents" in wrapper and wrapper["contents"]:
                    return json.loads(wrapper["contents"])
        except:
            pass

        try:
            r = requests.get(f"https://api.codetabs.com/v1/proxy/?quest={target_url}", timeout=15)
            if r.status_code == 200:
                return r.json()
        except:
            pass

        print("❌ Ошибка: Серверы CheapShark временно отклонили все попытки доступа.")
        return []

    def fetch_cheapshark_free(self, limit=20):
        url = f"{CHEAPSHARK_API}?storeID={STORE_IDS}&upperPrice=2.0&sortBy=Savings&pageSize=60"
        data = self._get_cheapshark(url)

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
        url = f"{CHEAPSHARK_API}?storeID={STORE_IDS}&upperPrice={max_price}&sortBy=Savings&pageSize=60&onSale=1"
        data = self._get_cheapshark(url)

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

            raw_desc = item.get("description", "") or ""
            ru_desc = self.translate_to_ru(raw_desc)

            games.append({
                "id": f"gp-pc-{item.get('id', '')}",
                "title": item.get("title", ""),
                "platform": p_name,
                "platformkey": p_key,
                "genre": item.get("type", "Giveaway"),
                "developer": "GamerPower",
                "description": ru_desc[:220],
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

            raw_desc = item.get("description", "") or ""
            ru_desc = self.translate_to_ru(raw_desc)

            games.append({
                "id": f"gp-loot-{item.get('id', '')}",
                "title": item.get("title", ""),
                "platform": "Ключи",
                "platformkey": "loot",
                "genre": "Loot",
                "developer": "GamerPower",
                "description": ru_desc[:220],
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
        games = []
        try:
            r = self.session.get(GAMERPOWER_API, params=params, timeout=REQUEST_TIMEOUT)
            if r.status_code == 200:
                data = r.json()
                for item in data:
                    if item.get("status") == "Ended": continue
                    title = item.get("title", "").lower()
                    desc_en = item.get("description", "").lower()
                    
                    if "roblox" in title or "roblox" in desc_en:
                        worth_str = str(item.get("worth", "0")).replace("$", "").replace("N/A", "0").replace(" ", "")
                        worth_val = float(worth_str) if worth_str else 0.0
                        
                        ru_desc = self.translate_to_ru(item.get("description", ""))

                        games.append({
                            "id": f"gp-roblox-{item.get('id', '')}",
                            "title": item.get("title", ""),
                            "platform": "Roblox",
                            "platformkey": "roblox",
                            "genre": "Roblox Халява",
                            "developer": "Roblox",
                            "description": ru_desc[:220],
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
        except Exception:
            pass
        return games

    def fetch_gacha_mobile_loot(self, limit=10):
        params = {"type": "loot", "sort-by": "date"}
        games = []
        try:
            r = self.session.get(GAMERPOWER_API, params=params, timeout=REQUEST_TIMEOUT)
            if r.status_code == 200:
                data = r.json()
                for item in data:
                    if item.get("status") == "Ended": continue
                    
                    title = item.get("title", "").lower()
                    desc_en = item.get("description", "").lower()
                    
                    gacha_kws = ["genshin", "honkai", "star rail", "zenless", "zzz", "hoyoverse", "mihoyo"]
                    mobile_kws = ["pubg", "call of duty mobile", "cod mobile", "mobile legends", "coin master", "free fire", "pokemon go"]
                    
                    is_gacha = any(kw in title or kw in desc_en for kw in gacha_kws)
                    is_mobile = any(kw in title or kw in desc_en for kw in mobile_kws)
                    
                    if not (is_gacha or is_mobile):
                        continue

                    platform_name = "HoYoverse (Гача)" if is_gacha else "Мобильные Игры"
                    platform_key = "gacha" if is_gacha else "mobile"
                    
                    worth_str = str(item.get("worth", "0")).replace("$", "").replace("N/A", "0").replace(" ", "")
                    worth_val = float(worth_str) if worth_str else 0.0

                    ru_desc = self.translate_to_ru(item.get("description", ""))

                    games.append({
                        "id": f"gp-mobile-{item.get('id', '')}",
                        "title": item.get("title", ""),
                        "platform": platform_name,
                        "platformkey": platform_key,
                        "genre": "Промокоды / Лут",
                        "developer": "Mobile Dev",
                        "description": ru_desc[:220],
                        "worth": worth_val,
                        "price": "FREE",
                        "period": item.get("endDate") or "TBD",
                        "image": item.get("image") or PLACEHOLDER_IMG,
                        "link": item.get("openGiveawayURL", "") or item.get("open_giveaway_url", ""),
                        "hot": True,
                        "ratingscore": 10.0,
                        "source": "Mobile Promo",
                        "tags": ["Mobile", "Promo", platform_key],
                        "end_at": item.get("endDate")
                    })
                    if len(games) >= limit: 
                        break
        except Exception as e:
            print(f"❌ Ошибка GamerPower (Mobile/Gacha): {e}")

        return games

    def fetch_steam_new_releases(self, limit=10):
        url = "https://store.steampowered.com/api/featuredcategories/?cc=us&l=ru"
        try:
            r = self.session.get(url, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            data = r.json()
            new_releases = data.get("new_releases", {}).get("items", [])
            
            # Собираем ID топовых игр (Хиты продаж)
            top_sellers = data.get("top_sellers", {}).get("items", [])
            top_seller_ids = {item.get("id") for item in top_sellers}
        except Exception as e:
            print(f"❌ Ошибка Steam New Releases: {e}")
            return []

        games = []
        for item in new_releases:
            game_id = item.get("id")
            title = item.get("name", "Новая игра")
            
            orig_cents = item.get("original_price", 0) or 0
            final_cents = item.get("final_price", 0) or 0
            discount = item.get("discount_percent", 0) or 0
            
            orig_price = orig_cents / 100.0
            final_price = final_cents / 100.0
            
            # ФИЛЬТР: Пропускаем платные игры, если они НЕ входят в хиты продаж
            if final_price > 0 and game_id not in top_seller_ids:
                continue
                
            if final_price == 0 and orig_price == 0:
                price_str = "FREE"
            elif discount > 0:
                price_str = f"${final_price:.2f} (-{discount}%)"
            else:
                price_str = f"${final_price:.2f}"

            desc = "🎮 Свежий релиз, который только что появился в магазине Steam!"
            try:
                det_url = f"https://store.steampowered.com/api/appdetails?appids={game_id}&l=russian"
                det_r = self.session.get(det_url, timeout=5)
                if det_r.status_code == 200:
                    det_data = det_r.json()
                    if det_data and str(game_id) in det_data and det_data[str(game_id)].get("success"):
                        fetched_desc = det_data[str(game_id)]["data"].get("short_description")
                        if fetched_desc:
                            fetched_desc = re.sub(r'<[^>]+>', '', fetched_desc)
                            desc = self.translate_to_ru(fetched_desc)[:220]
            except Exception as e:
                pass

            games.append({
                "id": f"steam-new-{game_id}",
                "title": title,
                "platform": "Steam (Новинка)",
                "platformkey": "steam_new",
                "genre": "Релиз в Steam",
                "developer": "Steam",
                "description": desc,
                "worth": orig_price,
                "price": price_str,
                "period": "Релиз",
                "image": item.get("large_capsule_image") or item.get("header_image") or PLACEHOLDER_IMG,
                "link": f"https://store.steampowered.com/app/{game_id}/",
                "hot": True,
                "ratingscore": 10.0,
                "source": "Steam Store",
                "tags": ["Steam", "NewRelease"],
                "end_at": None,
            })
            if len(games) >= limit:
                break
        return games

    def store_name(self, storeid):
        return {
            "1": "Steam", "2": "GamersGate", "3": "GreenManGaming", 
            "7": "GOG", "11": "Humble Store", "15": "Fanatical", 
            "25": "Epic Games", "30": "IndieGala"
        }.get(storeid, "Store")
     
