from behave import given, when, then
from tracker.models import WishlistItem, Game


@when('I fill in the target price "{price}"')
def step_fill_target_price(context, price):
    context.browser.fill('target_price', price)


@when('I submit the wishlist form')
def step_submit_wishlist(context):
    context.browser.find_by_css('button[type=submit]').first.click()


@then('I should have a wishlist item for "{title}" with target price {price}')
def step_wishlist_item_exists(context, title, price):
    game = Game.objects.get(title=title)
    assert WishlistItem.objects.filter(
        user=context.user, game=game, target_price=float(price)
    ).exists()


@when('I visit my wishlist')
def step_visit_wishlist(context):
    context.browser.visit(context.get_url('my_wishlist'))


@when('I click "Remove" for "{title}"')
def step_click_remove(context, title):
    game = Game.objects.get(title=title)
    item = WishlistItem.objects.get(user=context.user, game=game)
    context.browser.visit(context.get_url('wishlist_delete', pk=item.pk))


@then('I should not have a wishlist item for "{title}"')
def step_no_wishlist_item(context, title):
    game = Game.objects.get(title=title)
    assert not WishlistItem.objects.filter(user=context.user, game=game).exists()
