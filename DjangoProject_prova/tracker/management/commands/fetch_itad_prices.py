import time
import math
import requests
import re
from django.core.management.base import BaseCommand
from django.conf import settings
from tracker.models import Game, Store, PriceListing, PriceHistory
from django.utils.timezone import now


def clean_game_title(title):
    """
    Limpia el título del juego para aumentar las coincidencias exactas en ITAD.
    """
    t = title.lower()  # Pasamos todo a minúsculas

    # 1. Fuera marcas registradas
    t = t.replace('™', '').replace('®', '').replace('©', '')

    # 2. ITAD prefiere 'and' en lugar del símbolo '&'
    t = t.replace('&', 'and')

    # 3. Cortamos el título si tiene la palabra "edition" o un guión de subtítulo largo
    t = t.split(' - ')[0]
    t = t.split(' edition')[0]

    # 4. Eliminamos puntuación problemática
    t = re.sub(r'[:\'\-,.!]', '', t)

    # 5. Quitamos espacios dobles
    t = re.sub(r'\s+', ' ', t).strip()

    return t


class Command(BaseCommand):
    help = 'Busca ofertas en ITAD usando rate limiting logarítmico y limpieza de títulos.'

    def handle(self, *args, **options):
        api_key = settings.ITAD_API_KEY
        if not api_key:
            self.stdout.write(self.style.ERROR('Falta ITAD_API_KEY en tu entorno (.env)'))
            return

        games = Game.objects.all()
        x = games.count()

        if x == 0:
            self.stdout.write(self.style.WARNING("No hay juegos en la base de datos."))
            return

        # Aplicamos la fórmula matemática para los descansos
        if x > 1:
            batch_size = max(1, int(x / (8.5 * math.log10(x))))
        else:
            batch_size = 1

        self.stdout.write(f"Buscando precios en ITAD para {x} juegos...")
        self.stdout.write(self.style.NOTICE(f"Estrategia activada: Pausa de 2 min cada {batch_size} juegos.\n"))

        for index, game in enumerate(games, start=1):

            #  Usamos la función para limpiar el título antes de buscarlo
            clean_name = clean_game_title(game.title)

            # Construimos la URL con el título ya limpio
            lookup_url = f"https://api.isthereanydeal.com/games/lookup/v1?key={api_key}&title={clean_name}"

            try:
                res = requests.get(lookup_url)

                if res.status_code != 200:
                    self.stdout.write(self.style.WARNING(
                        f"  [Ignorado] {game.title} (buscado como '{clean_name}'): HTTP {res.status_code}"))
                else:
                    try:
                        data = res.json()
                        if data.get('found'):
                            itad_id = data['game']['id']
                            prices_url = f"https://api.isthereanydeal.com/games/prices/v2?key={api_key}&nondeals=true&games={itad_id}"
                            prices_res = requests.get(prices_url)

                            if prices_res.status_code == 200:
                                try:
                                    prices_data = prices_res.json()
                                    ofertas_encontradas = 0
                                    for item in prices_data:
                                        for deal in item.get('deals', []):
                                            store_name = deal['shop']['name']
                                            current_price = deal['price']['amount']
                                            product_url = deal['url']

                                            store, _ = Store.objects.get_or_create(
                                                name=store_name,
                                                defaults={
                                                    'website_url': f"https://{store_name.lower().replace(' ', '')}.com",
                                                    'sells_digital': True}
                                            )

                                            listing, _ = PriceListing.objects.update_or_create(
                                                game=game, store=store, format_type='DIGITAL',
                                                defaults={'current_price': current_price, 'product_url': product_url,
                                                          'last_updated': now()}
                                            )
                                            PriceHistory.objects.create(price_listing=listing,
                                                                        recorded_price=current_price)
                                            ofertas_encontradas += 1
                                            self.stdout.write(self.style.SUCCESS(
                                                f"    ✔ OFERTA: {game.title} - {current_price}€ en {store.name}"))

                                    if ofertas_encontradas == 0:
                                        self.stdout.write(self.style.NOTICE(
                                            f"  [Sin ofertas] {game.title} no tiene descuentos ahora mismo."))
                                except ValueError:
                                    self.stdout.write(
                                        self.style.ERROR(f"  [Error] {game.title}: Fallo al leer JSON de precios."))
                        else:
                            self.stdout.write(self.style.NOTICE(
                                f"  [No encontrado] {game.title} (buscado como '{clean_name}') no existe en ITAD."))
                    except ValueError:
                        self.stdout.write(
                            self.style.ERROR(f"  [Error] {game.title}: La API no devolvió un JSON válido."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  [Fallo de conexión] Error con {game.title}: {e}"))

            # Control de descanso (Rate Limiting matemático)
            if index % batch_size == 0 and index < x:
                self.stdout.write(self.style.WARNING(
                    f"\n[Lote completado: {index}/{x} juegos] -> Descansando 1 minutos para no saturar la API..."))
                time.sleep(100)
                self.stdout.write(self.style.SUCCESS("Descanso finalizado. Retomando la búsqueda...\n"))

        self.stdout.write(self.style.SUCCESS("\n¡Actualización de IsThereAnyDeal completada!"))
