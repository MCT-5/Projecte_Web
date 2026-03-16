import time
import math
import requests
from django.core.management.base import BaseCommand
from tracker.models import Game, Store, PriceListing, PriceHistory
from django.utils.timezone import now

#python manage.py fetch_prices
class Command(BaseCommand):
    help = 'Busca precios actuales en la API de CheapShark usando rate limiting logarítmico.'

    def handle(self, *args, **options):
        self.stdout.write("Obteniendo lista de tiendas...")
        stores_response = requests.get('https://www.cheapshark.com/api/1.0/stores')
        stores_data = stores_response.json()

        store_map = {}
        for store_info in stores_data:
            if store_info['isActive'] == 1:
                store, _ = Store.objects.get_or_create(
                    name=store_info['storeName'],
                    defaults={
                        'website_url': f"https://www.cheapshark.com/redirect?storeID={store_info['storeID']}",
                        'sells_physical': False,
                        'sells_digital': True
                    }
                )
                store_map[store_info['storeID']] = store

        games = Game.objects.all()
        x = games.count()

        if x == 0:
            self.stdout.write(self.style.WARNING("No hay juegos en la base de datos."))
            return

        
        if x > 1:
            batch_size = max(1, int(x / 20))
        else:
            batch_size = 1

        self.stdout.write(f"Buscando precios para {x} juegos...")
        self.stdout.write(self.style.NOTICE(f"Estrategia activada: Pausa de 2 min cada {batch_size} juegos.\n"))

        for index, game in enumerate(games, start=1):
            search_url = f"https://www.cheapshark.com/api/1.0/games?title={game.title}&limit=1"
            res = requests.get(search_url)

            if res.status_code == 200 and res.json():
                game_api_data = res.json()[0]
                game_id_api = game_api_data['gameID']

                deals_url = f"https://www.cheapshark.com/api/1.0/games?id={game_id_api}"
                deals_res = requests.get(deals_url)

                if deals_res.status_code == 200:
                    deals_data = deals_res.json()
                    for deal in deals_data.get('deals', []):
                        store_id_api = deal['storeID']
                        if store_id_api in store_map:
                            store = store_map[store_id_api]
                            current_price = float(deal['price'])
                            product_url = f"https://www.cheapshark.com/redirect?dealID={deal['dealID']}"

                            listing, _ = PriceListing.objects.update_or_create(
                                game=game, store=store, format_type='DIGITAL',
                                defaults={'current_price': current_price, 'product_url': product_url,
                                          'last_updated': now()}
                            )
                            PriceHistory.objects.create(price_listing=listing, recorded_price=current_price)
                            self.stdout.write(f"  Oferta guardada: {game.title} a {current_price}€ en {store.name}")

            # Control de descanso (Rate Limiting)
            if index % batch_size == 0 and index < x:
                self.stdout.write(self.style.WARNING(
                    f"\n[Lote completado: {index}/{x} juegos] -> Descansando 2 minutos para no saturar la API..."))
                time.sleep(60)
                self.stdout.write(self.style.SUCCESS("Descanso finalizado. Retomando la búsqueda...\n"))

        self.stdout.write(self.style.SUCCESS("\n¡Actualización completada!"))
