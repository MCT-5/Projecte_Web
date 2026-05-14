from behave import given, when, then
from django.urls import reverse
from tracker.models import WishlistItem

@given('the game is in my wishlist with target price {price}')
def step_wishlist_exists(context, price):
    context.wishlist_item = WishlistItem.objects.create(
        user=context.user1,
        game=context.game,
        target_price=float(price)
    )

@when('I add the game to my wishlist with target price {price}')
def step_add_wishlist(context, price):
    url = reverse('add_to_wishlist', args=[context.game.id])
    # Si el usuario no está logueado, NO seguimos la redirección para evitar el 404
    is_logged_in = '_auth_user_id' in context.client.session
    context.response = context.client.post(url, {
        'target_price': price
    }, follow=is_logged_in)

@when('I edit the wishlist item with target price {price}')
def step_edit_wishlist(context, price):
    url = reverse('edit_wishlist_item', args=[context.wishlist_item.id])
    context.response = context.client.post(url, {
        'target_price': price,
        'alert_enabled': True
    }, follow=True)

@when('I delete the wishlist item')
def step_delete_wishlist(context):
    url = reverse('delete_wishlist_item', args=[context.wishlist_item.id])
    context.response = context.client.post(url, follow=True)

@then('the game should be in my wishlist')
def step_in_wishlist(context):
    exists = WishlistItem.objects.filter(
        user=context.user1, game=context.game
    ).exists()
    context.test.assertTrue(exists)

@then('the wishlist item should have target price {price}')
def step_check_price(context, price):
    item = WishlistItem.objects.get(user=context.user1, game=context.game)
    context.test.assertEqual(float(item.target_price), float(price))

@then('the game should not be in my wishlist')
def step_not_in_wishlist(context):
    exists = WishlistItem.objects.filter(
        user=context.user1, game=context.game
    ).exists()
    context.test.assertFalse(exists)