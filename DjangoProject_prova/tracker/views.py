from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Min
from .models import Game, WishlistItem, Review
from .forms import ReviewForm, WishlistItemForm


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
    games = Game.objects.annotate(
        lowest_price=Min('price_listings__current_price')
    ).filter(lowest_price__isnull=False)
    return render(request, 'tracker/home.html', {'games': games})


def game_detail(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    listings = game.price_listings.all().select_related('store').prefetch_related('price_history')
    reviews = game.reviews.all().select_related('user')
    user_review = None
    review_form = None

    if request.user.is_authenticated:
        user_review = Review.objects.filter(user=request.user, game=game).first()
        if not user_review:
            review_form = ReviewForm()

    return render(request, 'tracker/game_detail.html', {
        'game': game,
        'listings': listings,
        'reviews': reviews,
        'user_review': user_review,
        'review_form': review_form,
    })


@login_required
def add_review(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.game = game
            review.save()
    return redirect('game_detail', game_id=game.id)


@login_required
def edit_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            return redirect('game_detail', game_id=review.game.id)
    else:
        form = ReviewForm(instance=review)
    return render(request, 'tracker/edit_review.html', {'form': form, 'review': review})


@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    game_id = review.game.id
    if request.method == 'POST':
        review.delete()
    return redirect('game_detail', game_id=game_id)


@login_required
def add_to_wishlist(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    if request.method == 'POST':
        target_price = request.POST.get('target_price')
        WishlistItem.objects.update_or_create(
            user=request.user,
            game=game,
            defaults={'target_price': float(target_price), 'alert_enabled': True}
        )
        return redirect('my_wishlist')
    return redirect('game_detail', game_id=game.id)


@login_required
def my_wishlist(request):
    items = WishlistItem.objects.filter(user=request.user).select_related('game')
    return render(request, 'tracker/wishlist.html', {'items': items})


@login_required
def edit_wishlist_item(request, item_id):
    item = get_object_or_404(WishlistItem, id=item_id, user=request.user)
    if request.method == 'POST':
        form = WishlistItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('my_wishlist')
    else:
        form = WishlistItemForm(instance=item)
    return render(request, 'tracker/edit_wishlist_item.html', {'form': form, 'item': item})


@login_required
def delete_wishlist_item(request, item_id):
    item = get_object_or_404(WishlistItem, id=item_id, user=request.user)
    if request.method == 'POST':
        item.delete()
    return redirect('my_wishlist')