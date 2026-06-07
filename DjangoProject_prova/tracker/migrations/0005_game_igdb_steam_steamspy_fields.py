# Migración manual: añade igdb_id, steam_app_id, description, rating
# y todos los campos steamspy al modelo Game.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0004_review'),
    ]

    operations = [
        # Nuevos IDs externos
        migrations.AddField(
            model_name='game',
            name='igdb_id',
            field=models.IntegerField(blank=True, db_index=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='game',
            name='steam_app_id',
            field=models.IntegerField(blank=True, db_index=True, null=True),
        ),
        # Campos enriquecidos de IGDB
        migrations.AddField(
            model_name='game',
            name='description',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='game',
            name='rating',
            field=models.FloatField(default=0),
        ),
        # Hacer platform y genre opcionales (ya vienen vacíos de IGDB a veces)
        migrations.AlterField(
            model_name='game',
            name='platform',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='game',
            name='genre',
            field=models.CharField(blank=True, max_length=100),
        ),
        # Campos SteamSpy
        migrations.AddField(
            model_name='game',
            name='steamspy_owners',
            field=models.BigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='game',
            name='steamspy_positive',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='game',
            name='steamspy_negative',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='game',
            name='steamspy_playtime',
            field=models.IntegerField(default=0, help_text='Minutos de juego medio (histórico)'),
        ),
        migrations.AddField(
            model_name='game',
            name='steamspy_players_2w',
            field=models.IntegerField(default=0, help_text='Jugadores activos últimas 2 semanas'),
        ),
        migrations.AddField(
            model_name='game',
            name='steamspy_tags',
            field=models.CharField(blank=True, max_length=500),
        ),
    ]
