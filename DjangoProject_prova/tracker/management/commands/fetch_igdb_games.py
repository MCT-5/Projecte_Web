"""
Comando: fetch_igdb_games
Uso:
    python manage.py fetch_igdb_games
    python manage.py fetch_igdb_games --limit 100 --pages 3

Borra todos los juegos existentes y los recarga desde IGDB con datos
más ricos: portada en alta resolución, géneros, rating, descripción
y el steam_app_id (necesario para GG.deals y SteamSpy).

Requiere IGDB_CLIENT_ID e IGDB_CLIENT_SECRET en el .env.
"""

import time
import logging
from django.core.management.base import BaseCommand
from tracker.services import IGDBService
from tracker.models import Game

logger = logging.getLogger(__name__)

# Categoría 1 = Steam en external_games de IGDB
IGDB_STEAM_CATEGORY = 1


def _extract_steam_id(external_games: list) -> int | None:
    """Extrae el steam_app_id de la lista external_games de IGDB."""
    for eg in (external_games or []):
        if eg.get("category") == IGDB_STEAM_CATEGORY:
            try:
                return int(eg["uid"])
            except (KeyError, ValueError, TypeError):
                pass
    return None


class Command(BaseCommand):
    help = "Borra los juegos existentes y los recarga desde IGDB."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit", type=int, default=50,
            help="Juegos por petición (máx. 500). Default: 50",
        )
        parser.add_argument(
            "--pages", type=int, default=1,
            help="Número de páginas a descargar. Default: 1",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        pages = options["pages"]

        # ── 1. Borrar datos existentes ─────────────────────────────────────
        total_deleted, _ = Game.objects.all().delete()
        self.stdout.write(
            self.style.WARNING(f"Eliminados {total_deleted} juegos existentes.")
        )

        # ── 2. Descargar desde IGDB ────────────────────────────────────────
        igdb    = IGDBService()
        created = 0
        errors  = 0

        for page in range(pages):
            offset = page * limit
            self.stdout.write(
                self.style.NOTICE(f"\n--- IGDB página {page + 1}/{pages} (offset {offset}) ---")
            )

            try:
                games = igdb.get_popular_games(limit=limit, offset=offset)
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"  Error al llamar a IGDB: {exc}"))
                break

            if not games:
                self.stdout.write("  Sin más resultados.")
                break

            for g in games:
                igdb_id = g.get("id")
                name    = (g.get("name") or "").strip()
                if not igdb_id or not name:
                    continue

                # Portada en alta resolución
                cover_url = ""
                if g.get("cover") and g["cover"].get("url"):
                    cover_url = "https:" + g["cover"]["url"].replace("t_thumb", "t_cover_big")

                # Géneros (primer valor como campo genre, todos en descripción)
                genres_list = [genre["name"] for genre in g.get("genres", []) if genre.get("name")]
                genre_str   = genres_list[0] if genres_list else ""

                # Plataformas (primera como campo platform)
                platforms_list = [p["name"] for p in g.get("platforms", []) if p.get("name")]
                platform_str   = platforms_list[0] if platforms_list else ""

                # Steam App ID
                steam_app_id = _extract_steam_id(g.get("external_games", []))

                try:
                    Game.objects.create(
                        igdb_id         = igdb_id,
                        title           = name,
                        description     = g.get("summary", ""),
                        cover_image_url = cover_url,
                        genre           = genre_str,
                        platform        = platform_str,
                        rating          = g.get("total_rating") or 0,
                        steam_app_id    = steam_app_id,
                    )
                    created += 1
                    steam_info = f" [Steam: {steam_app_id}]" if steam_app_id else ""
                    self.stdout.write(f"  ✔ {name}{steam_info}")
                except Exception as exc:
                    logger.error("Error guardando '%s': %s", name, exc)
                    errors += 1

            # Pausa entre páginas para respetar el rate limit de IGDB (4 req/s)
            if page < pages - 1:
                time.sleep(0.3)

        self.stdout.write(
            self.style.SUCCESS(
                f"\n¡Completado! {created} juegos importados · {errors} errores."
            )
        )
        with_steam = Game.objects.exclude(steam_app_id__isnull=True).count()
        self.stdout.write(
            self.style.NOTICE(
                f"{with_steam} juegos tienen steam_app_id "
                f"(disponibles para GG.deals y SteamSpy)."
            )
        )
