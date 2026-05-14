from behave import given, when, then
from django.contrib.auth.models import User
from tracker.models import Game, Store, PriceListing, WishlistItem


@given('a registered user "{username}" with password "{password}"')
def step_create_user(context, username, password):
    User.objects.filter(username=username).delete()
    context.user = User.objects.create_user(username=username, password=password)


@given('a game "{title}" on "{platform}" with genre "{genre}"')
def step_create_game(context, title, platform, genre):
    context.game = Game.objects.get_or_create(title=title, defaults={'platform': platform, 'genre': genre})[0]


@given('a store "{name}"')
def step_create_store(context, name):
    context.store = Store.objects.get_or_create(
        name=name, defaults={'website_url': 'https://example.com', 'sells_digital': True}
    )[0]


@given('I am logged in as "{username}" with password "{password}"')
def step_login(context, username, password):
    b = context.browser
    b.visit(context.get_url('login'))
    b.fill('username', username)
    b.fill('password', password)
    b.find_by_css('button[type=submit]').first.click()


@when('I visit the home page')
def step_visit_home(context):
    context.browser.visit(context.get_url('home'))


@then('I should see "{text}"')
def step_see_text(context, text):
    assert text in context.browser.html, f'"{text}" not found in page'


@then('I should not see "{text}"')
def step_not_see_text(context, text):
    assert text not in context.browser.html, f'"{text}" unexpectedly found in page'
