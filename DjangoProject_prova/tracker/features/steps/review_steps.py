from behave import given, when, then
from django.urls import reverse
from tracker.models import Review, Game
from django.contrib import messages

@given('I am logged in as player1')
def step_login(context):
    context.client.login(username='player1', password='pass1234')

@given('I am not logged in')
def step_logout(context):
    context.client.logout()

@given('there is a game Skyrim')
def step_game_exists(context):
    # El juego ya debería estar en context.game desde environment.py
    # Pero nos aseguramos por si acaso
    game, _ = Game.objects.get_or_create(title="Skyrim")
    context.game = game

@given('I have a review with rating {rating:d} and comment "{comment}"')
def step_create_own_review(context, rating, comment):
    Review.objects.create(
        user=context.user1,
        game=context.game,
        rating=rating,
        comment=comment
    )

@given('player2 has a review on the game')
def step_create_other_review(context):
    context.other_review = Review.objects.create(
        user=context.user2,
        game=context.game,
        rating=3,
        comment="Player2 review"
    )


@when('I submit a review with rating {rating} and comment "{comment}"')
def step_submit_review(context, rating, comment):
    url = reverse('add_review', args=[context.game.id])

    # Aseguramos que rating sea un entero para el POST
    try:
        rating_val = int(rating)
    except:
        rating_val = 5

    # Verificamos si estamos logueados para decidir si seguir redirecciones
    is_logged_in = '_auth_user_id' in context.client.session

    context.response = context.client.post(url, {
        'rating': rating_val,
        'comment': comment,
    }, follow=is_logged_in)

@when('I edit my review with comment "{comment}"')
def step_edit_own_review(context, comment):
    review = Review.objects.get(user=context.user1, game=context.game)
    url = reverse('edit_review', args=[review.id])
    context.response = context.client.post(url, {
        'rating': review.rating,
        'comment': comment,
    }, follow=True)

@when("I try to edit player2's review")
def step_edit_other_review(context):
    url = reverse('edit_review', args=[context.other_review.id])
    context.response = context.client.post(url, {
        'rating': 5,
        'comment': "Hacked review"
    })

@when('I delete my review')
def step_delete_review(context):
    review = Review.objects.get(user=context.user1, game=context.game)
    url = reverse('delete_review', args=[review.id])
    context.response = context.client.post(url, follow=True)

@then('I should see "{text}" on the game page')
def step_see_on_page(context, text):
    url = reverse('game_detail', args=[context.game.id])
    response = context.client.get(url)
    context.test.assertIn(text.encode(), response.content)

@then('I should be redirected to login')
def step_redirected_login(context):
    # Si la vista tiene @login_required, devuelve un 302
    context.test.assertEqual(context.response.status_code, 302)
    context.test.assertIn('login', context.response['Location'])

@then('I should get a 404')
def step_404(context):
    context.test.assertEqual(context.response.status_code, 404)

@then('the review should no longer exist')
def step_review_deleted(context):
    exists = Review.objects.filter(user=context.user1, game=context.game).exists()
    context.test.assertFalse(exists)

@then('I should see an error message "{expected_message}"')
def step_should_see_error_message(context, expected_message):
    # Buscamos el mensaje en el contenido de la respuesta
    context.test.assertIn(expected_message.encode(), context.response.content)