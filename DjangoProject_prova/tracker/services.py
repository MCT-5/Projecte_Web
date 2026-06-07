"""
Clientes para las APIs externas usadas por el tracker:
  - IGDB       → metadatos de juegos (Twitch OAuth2)
  - GG.deals   → precios retail y keyshops por Steam App ID
  - SteamSpy   → estadísticas de Steam (sin API key)
"""

import re
import time
import logging
import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

_STEAM_URL_RE = re.compile(r"store\.steampowered\.com/app/(\d+)", re.IGNORECASE)


def extract_steam_id_from_websites(websites: list) -> int | None:
    """Extrae el steam_app_id buscando una URL de Steam en la lista de websites de IGDB."""
    for w in (websites or []):
        url = w.get("url", "")
        m = _STEAM_URL_RE.search(url)
        if m:
            return int(m.group(1))
    return None


class IGDBService:
    TOKEN_URL = "https://id.twitch.tv/oauth2/token"
    BASE_URL  = "https://api.igdb.com/v4"
    CACHE_KEY = "igdb_access_token"

    def __init__(self):
        self.client_id     = getattr(settings, "IGDB_CLIENT_ID", "")
        self.client_secret = getattr(settings, "IGDB_CLIENT_SECRET", "")
        if not self.client_id or not self.client_secret:
            raise ValueError("IGDB_CLIENT_ID e IGDB_CLIENT_SECRET son obligatorios.")
        self.session = requests.Session()

    def _get_access_token(self) -> str:
        token = cache.get(self.CACHE_KEY)
        if token:
            return token
        resp = requests.post(
            self.TOKEN_URL,
            params={
                "client_id":     self.client_id,
                "client_secret": self.client_secret,
                "grant_type":    "client_credentials",
            },
            timeout=10,
        )
        resp.raise_for_status()
        body       = resp.json()
        token      = body["access_token"]
        expires_in = body.get("expires_in", 3600) - 60
        cache.set(self.CACHE_KEY, token, timeout=expires_in)
        logger.info("IGDB: token obtenido, expira en %s s", expires_in)
        return token

    def _post(self, endpoint: str, body: str) -> list:
        token = self._get_access_token()
        resp  = self.session.post(
            f"{self.BASE_URL}/{endpoint}",
            data=body,
            headers={
                "Client-ID":     self.client_id,
                "Authorization": f"Bearer {token}",
                "Accept":        "application/json",
            },
            timeout=15,
        )
        if resp.status_code == 429:
            logger.warning("IGDB rate limit alcanzado, esperando 1 s...")
            time.sleep(1)
            return self._post(endpoint, body)
        resp.raise_for_status()
        return resp.json()

    def get_popular_games(
        self,
        limit: int = 50,
        offset: int = 0,
        min_rating: int = 70,
        min_votes: int = 50,
    ) -> list:
        body = (
            f"fields id,name,summary,cover.url,genres.name,"
            f"platforms.name,first_release_date,total_rating,total_rating_count,"
            f"websites.url; "
            f"where total_rating >= {min_rating} & total_rating_count >= {min_votes}; "
            f"sort total_rating desc; "
            f"limit {limit}; offset {offset};"
        )
        return self._post("games", body)

    def search_games(self, query: str, limit: int = 8) -> list:
        body = (
            f'search "{query}"; '
            f'fields id,name,summary,cover.url,genres.name,'
            f'platforms.name,first_release_date,total_rating,websites.url; '
            f'limit {limit};'
        )
        return self._post("games", body)


class GGDealsService:
    BASE_URL = "https://api.gg.deals/v1"

    def __init__(self):
        self.api_key = getattr(settings, "GGDEALS_API_KEY", "")
        if not self.api_key:
            raise ValueError("GGDEALS_API_KEY no está definida.")
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def _get(self, endpoint: str, params: dict) -> dict:
        params["key"] = self.api_key
        url  = f"{self.BASE_URL}/{endpoint}/"
        resp = self.session.get(url, params=params, timeout=15)
        if not resp.ok:
            logger.error("GG.deals error %s — %s", resp.status_code, resp.text[:300])
        resp.raise_for_status()
        return resp.json()

    def get_prices_by_steam_ids(self, steam_app_ids: list, region: str = "eu") -> dict:
        if not steam_app_ids:
            return {}
        results = {}
        for i in range(0, len(steam_app_ids), 100):
            batch   = steam_app_ids[i:i + 100]
            ids_str = ",".join(str(x) for x in batch)
            try:
                data = self._get("prices/by-steam-app-id", {"ids": ids_str, "region": region})
                if data.get("success"):
                    results.update(data.get("data", {}))
            except Exception as exc:
                logger.error("GG.deals batch %d-%d falló: %s", i, i + len(batch), exc)
            time.sleep(0.7)
        return results


class SteamSpyService:
    BASE_URL = "https://steamspy.com/api.php"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def _get(self, params: dict, timeout: int = 15) -> dict:
        resp = self.session.get(self.BASE_URL, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    def get_app_details(self, steam_app_id: int) -> dict:
        return self._get({"request": "appdetails", "appid": steam_app_id})

    def get_top100_by_owners(self) -> dict:
        return self._get({"request": "top100owned"})