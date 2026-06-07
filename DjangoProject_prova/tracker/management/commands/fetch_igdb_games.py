"""
Comando: fetch_igdb_games

Modos de uso:
    python manage.py fetch_igdb_games --pages 29
    python manage.py fetch_igdb_games --pages 200 --min-rating 60 --min-votes 20
    python manage.py fetch_igdb_games --from-page 30 --to-page 80
    python manage.py fetch_igdb_games --from-page 30 --to-page 80 --min-rating 60
"""

import time
import logging
from django.core.management.base import BaseCommand
from tracker.services import IGDBService, extract_steam_id_from_websites
from tracker.models import Game

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Importa juegos desde IGDB. Con --from-page/--to-page añade sin borrar la BD."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit", type=int, default=50,
            help="Juegos por petición (máx. 500). Default: 50",
        )
        parser.add_argument(
            "--pages", type=int, default=None,
            help="Páginas desde la 1 (borra la BD). Incompatible con --from-page.",
        )
        parser.add_argument(
            "--from-page", type=int, default=None, dest="from_page",
            help="Página de inicio 1-based. NO borra la BD, solo añade.",
        )
        parser.add_argument(
            "--to-page", type=int, default=None, dest="to_page",
            help="Página de fin incluida 1-based. Usar junto a --from-page.",
        )
        parser.add_argument(
            "--min-rating", type=int, default=70, dest="min_rating",
            help="Rating mínimo IGDB (0-100). Default: 70.",
        )
        parser.add_argument(
            "--min-votes", type=int, default=50, dest="min_votes",
            help="Mínimo de votos para considerar el rating fiable. Default: 50.",
        )

    def handle(self, *args, **options):
        limit      = options["limit"]
        from_page  = options["from_page"]
        to_page    = options["to_page"]
        pages_opt  = options["pages"]
        min_rating = options["min_rating"]
        min_votes  = options["min_votes"]

        if from_page is not None:
            start      = from_page - 1
            end        = to_page if to_page else from_page
            page_range = list(range(start, end))
            self.stdout.write(self.style.NOTICE(
                f"Modo AÑADIR: páginas {from_page}–{end} "
                f"(offsets {start*limit}–{(end-1)*limit}). "
                f"Rating >= {min_rating}, votos >= {min_votes}."
            ))
            seen_igdb_ids = set(
                Game.objects.exclude(igdb_id__isnull=True).values_list("igdb_id", flat=True)
            )
            seen_title_platform = {
                (t.lower(), p.lower())
                for t, p in Game.objects.values_list("title", "platform")
            }
        else:
            total_deleted, _ = Game.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Eliminados {total_deleted} juegos existentes."))
            total_pages = pages_opt or 1
            page_range  = list(range(total_pages))
            seen_igdb_ids       = set()
            seen_title_platform = set()
            self.stdout.write(self.style.NOTICE(
                f"Rating >= {min_rating}, votos >= {min_votes}. "
                f"{total_pages} página(s) de {limit} juegos."
            ))

        igdb    = IGDBService()
        created = 0
        skipped = 0
        errors  = 0

        for i, page in enumerate(page_range):
            offset     = page * limit
            page_label = page + 1
            self.stdout.write(self.style.NOTICE(f"\n--- Página {page_label} (offset {offset}) ---"))

            try:
                games = igdb.get_popular_games(
                    limit=limit, offset=offset,
                    min_rating=min_rating, min_votes=min_votes,
                )
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"  Error IGDB: {exc}"))
                break

            if not games:
                self.stdout.write("  Sin más resultados (fin del catálogo para este filtro).")
                break

            for g in games:
                igdb_id = g.get("id")
                name    = (g.get("name") or "").strip()
                if not igdb_id or not name:
                    continue

                if igdb_id in seen_igdb_ids:
                    self.stdout.write(f"  ↷ {name} (ya existe, ignorado)")
                    skipped += 1
                    continue
                seen_igdb_ids.add(igdb_id)

                cover_url = ""
                if g.get("cover") and g["cover"].get("url"):
                    cover_url = "https:" + g["cover"]["url"].replace("t_thumb", "t_cover_big")

                genres_list    = [x["name"] for x in g.get("genres", []) if x.get("name")]
                platforms_list = [x["name"] for x in g.get("platforms", []) if x.get("name")]
                steam_app_id   = extract_steam_id_from_websites(g.get("websites", []))

                genre    = genres_list[0] if genres_list else ""
                platform = platforms_list[0] if platforms_list else ""

                key = (name.lower(), platform.lower())
                if key in seen_title_platform:
                    platform = f"{platform} [{igdb_id}]" if platform else str(igdb_id)
                    key = (name.lower(), platform.lower())
                seen_title_platform.add(key)

                try:
                    Game.objects.create(
                        igdb_id         = igdb_id,
                        title           = name,
                        description     = g.get("summary", ""),
                        cover_image_url = cover_url,
                        genre           = genre,
                        platform        = platform,
                        rating          = g.get("total_rating") or 0,
                        steam_app_id    = steam_app_id,
                    )
                    created += 1
                    steam_info = f" [Steam: {steam_app_id}]" if steam_app_id else " [sin Steam]"
                    self.stdout.write(f"  ✔ {name}{steam_info}")
                except Exception as exc:
                    logger.error("Error guardando '%s': %s", name, exc)
                    self.stdout.write(self.style.ERROR(f"  ✘ {name}: {exc}"))
                    errors += 1

            if i < len(page_range) - 1:
                time.sleep(0.3)

        with_steam    = Game.objects.exclude(steam_app_id__isnull=True).count()
        without_steam = Game.objects.filter(steam_app_id__isnull=True).count()

        self.stdout.write(self.style.SUCCESS(
            f"\n¡Completado! {created} importados · {skipped} ignorados · {errors} errores."
        ))
        self.stdout.write(self.style.NOTICE(
            f"  Total en BD — Con Steam: {with_steam} · Sin Steam: {without_steam}"
        ))
