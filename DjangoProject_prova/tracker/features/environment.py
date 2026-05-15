import os
import django
from django.test.runner import DiscoverRunner
from django.test import Client
from django.test import TestCase

# 1. Configurar la variable de entorno ANTES de importar modelos
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def before_all(context):
    import django
    django.setup()
    from django.test.runner import DiscoverRunner
    context.test_runner = DiscoverRunner()
    context.test_config = context.test_runner.setup_databases()
    # ESTA LÍNEA ES LA IMPORTANTE:
    context.test = TestCase()


def before_scenario(context, scenario):
    # Importamos los modelos AQUÍ adentro, cuando Django ya está cargado
    from django.contrib.auth.models import User
    from tracker.models import Game

    context.client = Client()

    # Crear usuarios de prueba
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

    # Crear juego de prueba
    context.game, _ = Game.objects.get_or_create(
        title='Skyrim',
        defaults={'genre': 'RPG'}
    )


def after_all(context):
    # 4. Destruir la base de datos de test al terminar
    context.test_runner.teardown_databases(context.test_config)