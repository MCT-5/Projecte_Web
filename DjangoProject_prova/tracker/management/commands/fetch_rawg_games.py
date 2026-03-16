import requests
import time  # Importamos time para hacer pausas entre peticiones
from django.core.management.base import BaseCommand
from django.conf import settings
from tracker.models import Game

#python manage.py fetch_rawg_games --start-page 5 --end-page 5
class Command(BaseCommand):
    help = 'Descarga juegos de la API de RAWG en un rango de páginas específico.'

    def add_arguments(self, parser):
        # Ahora pedimos dos argumentos: dónde empezar y dónde terminar
        parser.add_argument('--start-page', type=int, default=1, help='Página inicial para buscar')
        parser.add_argument('--end-page', type=int, default=1, help='Página final para buscar')

    def handle(self, *args, **options):
        api_key = settings.RAWG_API_KEY
        start_page = options['start_page']
        end_page = options['end_page']

        if not api_key:
            self.stdout.write(self.style.ERROR('ERROR: No se ha encontrado RAWG_API_KEY en el entorno (.env).'))
            return

        if start_page > end_page:
            self.stdout.write(self.style.ERROR('ERROR: La página inicial no puede ser mayor que la página final.'))
            return

        total_created = 0

        # Un bucle que recorrerá desde la start_page hasta la end_page (inclusive)
        for page in range(start_page, end_page + 1):
            url = f"https://api.rawg.io/api/games?key={api_key}&page_size=50&page={page}"
            self.stdout.write(self.style.NOTICE(f'\n--- Consultando página {page} ---'))

            try:
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
                games_data = data.get('results', [])

                if not games_data:
                    self.stdout.write(
                        self.style.WARNING(f'No se encontraron más juegos en la página {page}. Terminando búsqueda.'))
                    break  # Salimos del bucle si ya no hay más resultados en la API

                page_created_count = 0
                for item in games_data:
                    title = item.get('name')
                    cover_image_url = item.get('background_image')

                    platforms_list = item.get('platforms', [])
                    platform = platforms_list[0]['platform']['name'] if platforms_list else 'Desconocida'

                    genres_list = item.get('genres', [])
                    genre = genres_list[0]['name'] if genres_list else 'Varios'

                    game, created = Game.objects.get_or_create(
                        title=title,
                        defaults={
                            'platform': platform,
                            'cover_image_url': cover_image_url,
                            'genre': genre
                        }
                    )

                    if created:
                        page_created_count += 1
                        total_created += 1
                        self.stdout.write(f'  Añadido: {title}')

                self.stdout.write(self.style.SUCCESS(f'Página {page} completada. {page_created_count} juegos nuevos.'))

                # Pausa de 1 segundo antes de la siguiente página para no saturar la API
                if page < end_page:
                    time.sleep(1)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error al conectar con la API en la página {page}: {e}'))
                break  # Si hay un error de conexión, paramos el proceso

        self.stdout.write(
            self.style.SUCCESS(f'\n¡Proceso terminado! Se han importado un total de {total_created} juegos nuevos.'))