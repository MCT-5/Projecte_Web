from decimal import Decimal, InvalidOperation

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Game, WishlistItem
from django.db.models import Min


# Vista para el registro de usuarios
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'tracker/register.html', {'form': form})


def home(request):
    # 1. Anotamos el precio más bajo para TODOS los juegos primero
    # 2. Filtramos quedándonos solo con los que tienen un precio mínimo válido (lowest_price__isnull=False)
    games = Game.objects.annotate(
        lowest_price=Min('price_listings__current_price')
    ).filter(lowest_price__isnull=False)

    context = {
        'games': games
    }
    return render(request, 'tracker/home.html', context)


def game_detail(request, game_id):
    # Buscamos el juego por su ID, si no existe devuelve un error 404
    game = get_object_or_404(Game, id=game_id)

    # Extraemos todos los listados de precios asociados a este juego
    # Usamos select_related y prefetch_related para optimizar la consulta a la base de datos
    listings = game.price_listings.all().select_related('store').prefetch_related('price_history')

    context = {
        'game': game,
        'listings': listings
    }
    return render(request, 'tracker/game_detail.html', context)


@login_required
def add_to_wishlist(request, game_id):
    game = get_object_or_404(Game, id=game_id)

    if request.method == 'POST':
        # Capturamos el precio objetivo que el usuario escribió en el formulario
        target_price_raw = request.POST.get('target_price', '').strip()

        # Comprobamos que el usuario haya introducido un precio
        if not target_price_raw:
            listings = game.price_listings.all().select_related('store').prefetch_related('price_history')
            return render(request, 'tracker/game_detail.html', {
                'game': game,
                'listings': listings,
                'error': 'Debes introducir un precio objetivo.'
            })

        try:
            # Intentamos convertir el valor introducido a número decimal
            target_price = Decimal(target_price_raw)
        except InvalidOperation:
            listings = game.price_listings.all().select_related('store').prefetch_related('price_history')
            return render(request, 'tracker/game_detail.html', {
                'game': game,
                'listings': listings,
                'error': 'El precio objetivo debe ser un número válido.'
            })

        # Comprobamos que el precio no sea negativo
        if target_price < 0:
            listings = game.price_listings.all().select_related('store').prefetch_related('price_history')
            return render(request, 'tracker/game_detail.html', {
                'game': game,
                'listings': listings,
                'error': 'El precio objetivo no puede ser negativo.'
            })

        # Creamos o actualizamos el item en la wishlist
        WishlistItem.objects.update_or_create(
            user=request.user,
            game=game,
            defaults={
                'target_price': target_price,
                'alert_enabled': True
            }
        )
        return redirect('my_wishlist')

    return redirect('game_detail', game_id=game.id)


@login_required
def my_wishlist(request):
    # Filtramos la tabla WISHLIST_ITEM para que solo muestre los del usuario actual
    items = WishlistItem.objects.filter(user=request.user).select_related('game')
    return render(request, 'tracker/wishlist.html', {'items': items})