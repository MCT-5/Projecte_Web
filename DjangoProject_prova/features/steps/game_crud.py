from behave import given, when, then
from tracker.models import Game


@when('I go to add a new game')
def step_go_add_game(context):
    context.browser.visit(context.get_url('game_add'))


@when('I fill in the game title "{title}" platform "{platform}" genre "{genre}"')
def step_fill_game_form(context, title, platform, genre):
    b = context.browser
    b.fill('title', title)
    b.fill('platform', platform)
    b.fill('genre', genre)


@when('I submit the game form')
def step_submit_game_form(context):
    context.browser.find_by_css('button[type=submit]').first.click()


@then('the game "{title}" should exist in the database')
def step_game_in_db(context, title):
    assert Game.objects.filter(title=title).exists(), f'Game "{title}" not in DB'


@then('the game "{title}" should not exist in the database')
def step_game_not_in_db(context, title):
    assert not Game.objects.filter(title=title).exists(), f'Game "{title}" still in DB'


@when('I visit the game detail for "{title}"')
def step_visit_game_detail(context, title):
    game = Game.objects.get(title=title)
    context.browser.visit(context.get_url('game_detail', game_id=game.pk))


@when('I click "Edit Game"')
def step_click_edit(context):
    context.browser.find_by_text('Edit Game').first.click()


@when('I clear the title and type "{new_title}"')
def step_clear_and_type(context, new_title):
    field = context.browser.find_by_name('title').first
    field.fill(new_title)


@when('I click "Delete Game"')
def step_click_delete_game(context):
    context.browser.find_by_text('Delete Game').first.click()


@when('I confirm deletion')
def step_confirm_delete(context):
    context.browser.find_by_css('button[type=submit]').first.click()
