"""
Comando: fetch_prices (CheapShark)

Estrategia:
  1. Juegos con steam_app_id → busca por Steam ID en lotes de 100 (exacto)
  2. Juegos sin steam_app_id → busca por título como fallback
"""

import time
import requests
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.timezone import now
from tracker.models import Game, Store, PriceListing, PriceHistory

CHEAPSHARK_BASE = "https://www.cheapshark.com/api/1.0"


def get_or_create_store(store_info: dict) -> Store:
    store, _ = Store.objects.get_or_create(
        name=store_info["storeName"],
        defaults={
            "website_url":    f"https://www.cheapshark.com/redirect?storeID={store_info['storeID']}",
            "sells_physical": False,
            "sells_digital":  True,
        },
    )
    return store


def save_deal(game: Game, store: Store, price: float, deal_id: str, stdout):
    listing, _ = PriceListing.objects.update_or_create(
        game=game,
        store=store,
        format_type="DIGITAL",
        defaults={
            "current_price": Decimal(str(price)).quantize(Decimal("0.01")),
            "product_url":   f"https://www.cheapshark.com/redirect?dealID={deal_id}",
            "last_updated":  now(),
        },
    )
    PriceHistory.objects.create(
        price_listing  = listing,
        recorded_price = listing.current_price,
    )
    stdout.write(f"  ✔ {game.title} — {price}€ en {store.name}")


class Command(BaseCommand):
    help = "Obtiene precios de CheapShark para todos los juegos."

    def handle(self, *args, **options):
        # ── 1. Cargar tiendas ──────────────────────────────────────────────
        self.stdout.write("Cargando tiendas de CheapShark...")
        try:
            resp = requests.get(f"{CHEAPSHARK_BASE}/stores", timeout=10)
            resp.raise_for_status()
            stores_data = resp.json()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error al conectar con CheapShark: {e}"))
            return

        store_map = {}
        for s in stores_data:
            if s["isActive"] == 1:
                store_map[s["storeID"]] = get_or_create_store(s)
        self.stdout.write(f"  {len(store_map)} tiendas activas.")

        # ── 2. Separar juegos con y sin steam_app_id ───────────────────────
        games_with_steam    = list(Game.objects.exclude(steam_app_id__isnull=True))
        games_without_steam = list(Game.objects.filter(steam_app_id__isnull=True))
        saved  = 0
        errors = 0

        # ── 3. Lotes de 100 por Steam ID ───────────────────────────────────
        self.stdout.write(
            f"\n[1/2] Buscando por Steam ID: {len(games_with_steam)} juegos..."
        )
        steam_id_to_game = {str(g.steam_app_id): g for g in games_with_steam}

        # Lotes de 10 IDs para no disparar el rate limit de CheapShark
        BATCH = 10
        for i in range(0, len(games_with_steam), BATCH):
            batch   = games_with_steam[i:i + BATCH]
            ids_str = "%2C".join(str(g.steam_app_id) for g in batch)
            deals = None
            for attempt in range(5):
                try:
                    resp = requests.get(
                        f"{CHEAPSHARK_BASE}/deals?steamAppID={ids_str}&pageSize={BATCH}",
                        timeout=15,
                    )
                    if resp.status_code == 429:
                        wait = 10 * (attempt + 1)
                        self.stdout.write(self.style.WARNING(
                            f"  Rate limit (429), esperando {wait}s..."
                        ))
                        time.sleep(wait)
                        continue
                    resp.raise_for_status()
                    deals = resp.json()
                    break
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Error lote {i}: {e}"))
                    errors += 1
                    time.sleep(5)
                    break
            if not deals:
                continue

            for deal in deals:
                steam_id = deal.get("steamAppID")
                game     = steam_id_to_game.get(str(steam_id))
                store    = store_map.get(deal.get("storeID", ""))
                if not game or not store:
                    continue
                try:
                    save_deal(game, store, float(deal["salePrice"]), deal["dealID"], self.stdout)
                    saved += 1
                except Exception as e:
                    errors += 1

            # Progreso cada 100 juegos procesados
            if (i // BATCH) % 10 == 0 and i > 0:
                self.stdout.write(self.style.NOTICE(
                    f"  [{i}/{len(games_with_steam)} procesados]"
                ))
            time.sleep(2)  # pausa entre lotes

        # ── 4. Búsqueda por título para juegos sin Steam ID ────────────────
        self.stdout.write(
            f"\n[2/2] Buscando por título: {len(games_without_steam)} juegos..."
        )
        for game in games_without_steam:
            try:
                resp = requests.get(
                    f"{CHEAPSHARK_BASE}/games?title={game.title}&limit=1",
                    timeout=10,
                )
                if resp.status_code != 200 or not resp.json():
                    continue

                game_id_api = resp.json()[0]["gameID"]
                resp2 = requests.get(
                    f"{CHEAPSHARK_BASE}/games?id={game_id_api}",
                    timeout=10,
                )
                if resp2.status_code != 200:
                    continue

                for deal in resp2.json().get("deals", []):
                    store = store_map.get(deal["storeID"])
                    if not store:
                        continue
                    save_deal(game, store, float(deal["price"]), deal["dealID"], self.stdout)
                    saved += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Error {game.title}: {e}"))
                errors += 1
                time.sleep(3)

            time.sleep(0.5)

        self.stdout.write(self.style.SUCCESS(
            f"\n¡Completado! {saved} precios guardados · {errors} errores."
        ))
