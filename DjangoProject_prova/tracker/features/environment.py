from django.test import Client

def before_scenario(context, scenario):
    from django.contrib.auth.models import User
    from tracker.models import Game

    context.client = Client()   # ← esta línea es la que faltaba

    context.user1, _ = User.objects.get_or_create(
        username='player1',
        defaults={'email': 'p1@test.com'}
    )
    context.user1.set_password('pass1234')
    context.user1.save()

    context.user2, _ = User.objects.get_or_create(
        username='player2',
        defaults={'email': 'p2@test.com'}
    )
    context.user2.set_password('pass1234')
    context.user2.save()

    context.game, _ = Game.objects.get_or_create(
        title='Skyrim',
        defaults={'genre': 'RPG'}
    )