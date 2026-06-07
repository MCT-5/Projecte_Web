"""
Comando: fetch_ggdeals_prices
Uso:
    python manage.py fetch_ggdeals_prices
    python manage.py fetch_ggdeals_prices --region eu

Actualiza PriceListing y PriceHistory para todos los juegos que tienen
steam_app_id, usando GG.deals. Distingue entre tiendas retail oficiales
y keyshops (G2A, Kinguin, etc.).

Requiere GGDEALS_API_KEY en el .env.
"""

import logging
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.timezone import now
from tracker.services import GGDealsService
from tracker.models import Game, Store, PriceListing, PriceHistory

logger = logging.getLogger(__name__)

# Nombres de tienda que se guardarán en la BD
STORE_RETAIL   = "GG.deals Retail"
STORE_KEYSHOPS = "GG.deals Keyshops"


def _get_or_create_store(name: str) -> Store:
    store, _ = Store.objects.get_or_create(
        name=name,
        defaults={
            "website_url":    "https://gg.deals",
            "sells_physical": False,
            "sells_digital":  True,
        },
    )
    return store


def _save_price(game: Game, store: Store, price_raw, url: str):
    """Crea o actualiza PriceListing y añade snapshot a PriceHistory."""
    price = Decimal(str(price_raw)).quantize(Decimal("0.01"))
    listing, _ = PriceListing.objects.update_or_create(
        game=game,
        store=store,
        format_type="DIGITAL",
        defaults={
            "current_price": price,
            "product_url":   url or "https://gg.deals",
            "last_updated":  now(),
        },
    )
    PriceHistory.objects.create(
        price_listing  = listing,
        recorded_price = price,
    )
    return price


class Command(BaseCommand):
    help = "Obtiene precios de GG.deals (retail + keyshops) para juegos con steam_app_id."

    def add_arguments(self, parser):
        parser.add_argument(
            "--region", type=str, default="eu",
            help="Código de región (eu, us, gb…). Default: eu",
        )

    def handle(self, *args, **options):
        region  = options["region"]
        service = GGDealsService()

        games_qs  = Game.objects.exclude(steam_app_id__isnull=True)
        steam_ids = list(games_qs.values_list("steam_app_id", flat=True))

        if not steam_ids:
            self.stdout.write(self.style.WARNING("No hay juegos con steam_app_id en la BD."))
            return

        self.stdout.write(
            f"[GG.deals] Buscando precios para {len(steam_ids)} juegos (región: {region})..."
        )

        try:
            prices = service.get_prices_by_steam_ids(steam_ids, region=region)
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"Error al llamar a GG.deals: {exc}"))
            return

        store_retail   = _get_or_create_store(STORE_RETAIL)
        store_keyshops = _get_or_create_store(STORE_KEYSHOPS)

        saved  = 0
        skipped = 0

        for game in games_qs:
            data = prices.get(str(game.steam_app_id))
            if not data or not data.get("prices"):
                skipped += 1
                continue

            p   = data["prices"]
            url = data.get("url", "https://gg.deals")

            try:
                retail_price = p.get("currentRetail")
                if retail_price:
                    price = _save_price(game, store_retail, retail_price, url)
                    self.stdout.write(f"  ✔ {game.title} — Retail: {price} EUR")

                keyshop_price = p.get("currentKeyshops")
                if keyshop_price:
                    price = _save_price(game, store_keyshops, keyshop_price, url)
                    self.stdout.write(f"  ✔ {game.title} — Keyshop: {price} EUR")

                if retail_price or keyshop_price:
                    saved += 1
                else:
                    skipped += 1

            except Exception as exc:
                logger.error("Error guardando precio para %s: %s", game, exc)

        self.stdout.write(
            self.style.SUCCESS(
                f"\n[GG.deals] Hecho — {saved} juegos actualizados · {skipped} sin datos."
            )
        )
