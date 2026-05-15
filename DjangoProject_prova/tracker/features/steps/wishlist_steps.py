from behave import given, when, then
from django.urls import reverse

@given('the game is in my wishlist with target price {price}')
def step_wishlist_exists(context, price):
    # Use update_or_create to avoid IntegrityError
    item, created = WishlistItem.objects.update_or_create(
        user=context.user1,
        game=context.game,
        defaults={'target_price': float(price)}
    )
    context.wishlist_item = item

@when('I add the game to my wishlist with target price {price}')
def step_add_wishlist(context, price):
    url = reverse('add_to_wishlist', args=[context.game.id])
    context.response = context.client.post(url, {
        'target_price': price
    }, follow=True)

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
    from tracker.models import WishlistItem
    exists = WishlistItem.objects.filter(user=context.user1, game=context.game).exists()
    context.test.assertTrue(exists)

@then('the wishlist item should have target price {price}')
def step_check_price(context, price):
    from tracker.models import WishlistItem
    item = WishlistItem.objects.get(user=context.user1, game=context.game)
    context.test.assertEqual(float(item.target_price), float(price))

@then('the game should no longer be in my wishlist')
def step_not_in_wishlist(context):
    from tracker.models import WishlistItem
    exists = WishlistItem.objects.filter(user=context.user1, game=context.game).exists()
    context.test.assertFalse(exists)