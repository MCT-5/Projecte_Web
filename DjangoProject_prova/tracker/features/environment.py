from django.contrib.auth.models import User
from django.test.client import Client
from tracker.models import Game # Importa tu modelo de juegos

def before_scenario(context, scenario):
    context.client = Client()

    # 1. Crear/Obtener usuarios y guardarlos en context
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

    # 2. Crear el juego Skyrim (usando 'title' en lugar de 'name')
    # Guardarlo en context.game para que los steps lo encuentren
    context.game, _ = Game.objects.get_or_create(
        title='Skyrim',
        defaults={'genre': 'RPG'} # Añade los campos obligatorios que tenga tu modelo
    )