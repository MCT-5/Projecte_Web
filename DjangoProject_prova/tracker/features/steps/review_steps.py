from behave import given, when, then
from django.urls import reverse

@given('I am logged in as player1')
def step_login(context):
    context.client.login(username='player1', password='pass1234')

@given('I am not logged in')
def step_logout(context):
    context.client.logout()

@given('there is a game Skyrim')
def step_game_exists(context):
    from tracker.models import Game
    game, _ = Game.objects.get_or_create(title="Skyrim", defaults={'genre': 'RPG'})
    context.game = game

@given('I have a review with rating {rating:d} and comment "{comment}"')
def step_create_own_review(context, rating, comment):
    from tracker.models import Review
    Review.objects.get_or_create(user=context.user1, game=context.game, defaults={'rating': rating, 'comment': comment})

@given('player2 has a review on the game')
def step_create_other_review(context):
    from tracker.models import Review
    context.other_review = Review.objects.create(
        user=context.user2, game=context.game, rating=3, comment="Player2 review"
    )

@when('I submit a review with rating {rating} and comment "{comment}"')
def step_submit_review(context, rating, comment):
    url = reverse('add_review', args=[context.game.id])  # ← corregido
    context.response = context.client.post(url, {
        'rating': rating,
        'comment': comment
    }, follow=False)

@when('I edit my review with comment "{comment}"')
def step_edit_review(context, comment):
    from tracker.models import Review
    review = Review.objects.get(user=context.user1, game=context.game)
    url = reverse('edit_review', args=[review.id])
    context.response = context.client.post(url, {
        'rating': 5,
        'comment': comment
    }, follow=True)

@when("I try to edit player2's review")
def step_edit_other_review(context):
    url = reverse('edit_review', args=[context.other_review.id])
    context.response = context.client.post(url, {
        'rating': 1,
        'comment': "Hacked"
    }, follow=False)

@when('I delete my review')
def step_delete_review(context):
    from tracker.models import Review
    review = Review.objects.get(user=context.user1, game=context.game)
    url = reverse('delete_review', args=[review.id])
    context.response = context.client.post(url, follow=True)

@when('I click the login button from the review section')
def step_click_login_button(context):
    # Intentar acceder a una vista protegida sin login → redirige a login
    url = reverse('add_review', args=[context.game.id])
    context.response = context.client.get(url, follow=False)

@then('I should see "{text}" on the game page')
def step_see_on_page(context, text):
    # Hacemos un GET a la página del juego para ver el contenido actualizado
    url = reverse('game_detail', args=[context.game.id])
    response = context.client.get(url)
    context.test.assertIn(text.encode(), response.content)

@then('I should be redirected to login')
def step_redirected_login(context):
    context.test.assertEqual(context.response.status_code, 302)
    context.test.assertIn('login', context.response['Location'])

@then('I should get a 302 in my face from the login page')
def step_302_review(context):
    context.test.assertEqual(context.response.status_code, 302)
    context.test.assertIn('login', context.response['Location'])

@then('I should see an error message "{text}"')
def step_see_error(context, text):
    # Buscamos el mensaje en el sistema de mensajes de Django
    from django.contrib.messages import get_messages
    msgs = [str(m) for m in get_messages(context.response.wsgi_request)]
    context.test.assertIn(text, msgs)

@then('I should get a 404')
def step_404(context):
    context.test.assertEqual(context.response.status_code, 404)

@then('the review should no longer exist')
def step_review_deleted(context):
    from tracker.models import Review
    exists = Review.objects.filter(user=context.user1, game=context.game).exists()
    context.test.assertFalse(exists)