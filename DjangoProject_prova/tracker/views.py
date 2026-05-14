import json
import requests
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from .models import Game, WishlistItem, PriceListing, Store
from .forms import WishlistItemForm, WishlistItemUpdateForm, GameForm, PriceListingForm
from django.db.models import Min


# ── Auth ──────────────────────────────────────────────────────────────────────

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.username}! Account created.')
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'tracker/register.html', {'form': form})


# ── Home / Browse ─────────────────────────────────────────────────────────────

def home(request):
    query = request.GET.get('q', '')
    games = Game.objects.annotate(lowest_price=Min('price_listings__current_price'))
    if query:
        games = games.filter(title__icontains=query)
    games_with_prices = games.filter(lowest_price__isnull=False)
    games_no_prices = games.filter(lowest_price__isnull=True)
    all_games = list(games_with_prices) + list(games_no_prices)
    return render(request, 'tracker/home.html', {
        'games': all_games,
        'query': query,
    })


def game_detail(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    listings = game.price_listings.all().prefetch_related('price_history', 'store')
    user_wishlist_item = None
    if request.user.is_authenticated:
        user_wishlist_item = WishlistItem.objects.filter(user=request.user, game=game).first()
    return render(request, 'tracker/game_detail.html', {
        'game': game,
        'listings': listings,
        'user_wishlist_item': user_wishlist_item,
    })


# ── WishlistItem CRUD ─────────────────────────────────────────────────────────

@login_required
def my_wishlist(request):
    items = WishlistItem.objects.filter(user=request.user).select_related('game')
    return render(request, 'tracker/wishlist.html', {'items': items})


@login_required
def add_to_wishlist(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    existing = WishlistItem.objects.filter(user=request.user, game=game).first()
    if existing:
        messages.info(request, 'Game already in wishlist. You can edit it.')
        return redirect('wishlist_edit', pk=existing.pk)
    if request.method == 'POST':
        target_price = request.POST.get('target_price')
        try:
            WishlistItem.objects.create(
                user=request.user,
                game=game,
                target_price=float(target_price),
                alert_enabled=True,
            )
            messages.success(request, f'{game.title} added to your wishlist!')
        except (ValueError, TypeError):
            messages.error(request, 'Invalid price.')
        return redirect('my_wishlist')
    return redirect('game_detail', game_id=game.id)


class WishlistItemUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = WishlistItem
    form_class = WishlistItemUpdateForm
    template_name = 'tracker/wishlist_form.html'
    success_url = reverse_lazy('my_wishlist')

    def test_func(self):
        return self.get_object().user == self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Wishlist item updated.')
        return super().form_valid(form)


class WishlistItemDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = WishlistItem
    template_name = 'tracker/wishlist_confirm_delete.html'
    success_url = reverse_lazy('my_wishlist')

    def test_func(self):
        return self.get_object().user == self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Item removed from wishlist.')
        return super().form_valid(form)


# ── Game CRUD (any logged-in user) ───────────────────────────────────────────

class GameCreateView(LoginRequiredMixin, CreateView):
    model = Game
    form_class = GameForm
    template_name = 'tracker/game_form.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        messages.success(self.request, 'Game added successfully!')
        return super().form_valid(form)


class GameUpdateView(LoginRequiredMixin, UpdateView):
    model = Game
    form_class = GameForm
    template_name = 'tracker/game_form.html'

    def get_success_url(self):
        return reverse_lazy('game_detail', kwargs={'game_id': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Game updated.')
        return super().form_valid(form)


class GameDeleteView(LoginRequiredMixin, DeleteView):
    model = Game
    template_name = 'tracker/game_confirm_delete.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        messages.success(self.request, 'Game deleted.')
        return super().form_valid(form)


# ── PriceListing CRUD ─────────────────────────────────────────────────────────

class PriceListingCreateView(LoginRequiredMixin, CreateView):
    model = PriceListing
    form_class = PriceListingForm
    template_name = 'tracker/pricelisting_form.html'

    def get_initial(self):
        initial = super().get_initial()
        game_id = self.kwargs.get('game_id')
        if game_id:
            initial['game'] = get_object_or_404(Game, pk=game_id)
        return initial

    def get_success_url(self):
        game_id = self.object.game.pk
        return reverse_lazy('game_detail', kwargs={'game_id': game_id})

    def form_valid(self, form):
        messages.success(self.request, 'Price listing added.')
        return super().form_valid(form)


class PriceListingUpdateView(LoginRequiredMixin, UpdateView):
    model = PriceListing
    form_class = PriceListingForm
    template_name = 'tracker/pricelisting_form.html'

    def get_success_url(self):
        return reverse_lazy('game_detail', kwargs={'game_id': self.object.game.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Price listing updated.')
        return super().form_valid(form)


class PriceListingDeleteView(LoginRequiredMixin, DeleteView):
    model = PriceListing
    template_name = 'tracker/pricelisting_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('game_detail', kwargs={'game_id': self.object.game.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Price listing removed.')
        return super().form_valid(form)


# ── AJAX: External API (RAWG) autocomplete ────────────────────────────────────

def rawg_autocomplete(request):
    """Returns game suggestions from RAWG API for AJAX search."""
    query = request.GET.get('q', '').strip()
    if not query or len(query) < 2:
        return JsonResponse({'results': []})
    from django.conf import settings
    api_key = getattr(settings, 'RAWG_API_KEY', '')
    if not api_key:
        return JsonResponse({'results': [], 'error': 'No API key configured'})
    try:
        resp = requests.get(
            'https://api.rawg.io/api/games',
            params={'key': api_key, 'search': query, 'page_size': 8},
            timeout=5,
        )
        data = resp.json()
        results = [
            {
                'name': g.get('name', ''),
                'background_image': g.get('background_image', ''),
                'platforms': ', '.join(
                    p['platform']['name'] for p in (g.get('platforms') or [])[:3]
                ),
                'genres': ', '.join(
                    gen['name'] for gen in (g.get('genres') or [])[:2]
                ),
            }
            for g in data.get('results', [])
        ]
        return JsonResponse({'results': results})
    except Exception as e:
        return JsonResponse({'results': [], 'error': str(e)})
