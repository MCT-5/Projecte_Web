"""
Comando: fetch_steamspy_stats
Uso:
    python manage.py fetch_steamspy_stats --mode top100
    python manage.py fetch_steamspy_stats --mode all_games
"""

import time
import logging
from django.core.management.base import BaseCommand
from tracker.services import SteamSpyService
from tracker.models import Game

logger = logging.getLogger(__name__)


def _update_game(game: Game, data: dict):
    owners_raw = data.get("owners", "0 .. 0")
    owners_min = owners_raw.split("..")[0].strip().replace(",", "").replace(" ", "")

    game.steamspy_owners     = int(owners_min) if owners_min.isdigit() else 0
    game.steamspy_positive   = data.get("positive", 0)
    game.steamspy_negative   = data.get("negative", 0)
    game.steamspy_playtime   = data.get("average_forever", 0)
    game.steamspy_players_2w = data.get("players_2weeks", 0)

    tags = data.get("tags", {})
    if isinstance(tags, dict):
        game.steamspy_tags = ", ".join(
            tag for tag, _ in sorted(tags.items(), key=lambda x: -x[1])[:10]
        )

    game.save(update_fields=[
        "steamspy_owners", "steamspy_positive", "steamspy_negative",
        "steamspy_playtime", "steamspy_players_2w", "steamspy_tags",
    ])


class Command(BaseCommand):
    help = "Obtiene estadísticas de SteamSpy para los juegos con steam_app_id."

    def add_arguments(self, parser):
        parser.add_argument(
            "--mode",
            choices=["top100", "all_games"],
            default="all_games",
            help="top100 → solo top 100 propietarios. all_games → todos (1 req/s).",
        )

    def handle(self, *args, **options):
        service = SteamSpyService()
        mode    = options["mode"]
        updated = 0
        errors  = 0

        if mode == "top100":
            self.stdout.write("[SteamSpy] Descargando Top 100 por propietarios...")
            try:
                top100 = service.get_top100_by_owners()
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"Error: {exc}"))
                return

            for appid_str, data in top100.items():
                try:
                    game = Game.objects.filter(steam_app_id=int(appid_str)).first()
                    if game:
                        _update_game(game, data)
                        updated += 1
                        self.stdout.write(f"  ✔ {game.title} — {game.steamspy_owners:,} propietarios")
                except Exception as exc:
                    logger.error("Error top100 appid=%s: %s", appid_str, exc)
                    errors += 1

        else:
            games_qs = Game.objects.exclude(steam_app_id__isnull=True)
            total    = games_qs.count()
            self.stdout.write(f"[SteamSpy] Actualizando {total} juegos (1 req/s)...")

            for i, game in enumerate(games_qs.iterator(), start=1):
                try:
                    data = service.get_app_details(int(game.steam_app_id))
                    _update_game(game, data)
                    updated += 1
                    if i % 10 == 0:
                        self.stdout.write(f"  {i}/{total}...")
                except Exception as exc:
                    logger.error("Error appid=%s: %s", game.steam_app_id, exc)
                    errors += 1
                finally:
                    time.sleep(1.1)

        self.stdout.write(self.style.SUCCESS(
            f"\n[SteamSpy] Hecho — {updated} actualizados · {errors} errores."
        ))
