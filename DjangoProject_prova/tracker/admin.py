from django.contrib import admin
from .models import Game, Store, WishlistItem, PriceListing, StorePreference, PriceHistory


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('title', 'platform', 'genre')
    search_fields = ('title', 'platform')


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'website_url', 'sells_physical', 'sells_digital')
    list_filter = ('sells_physical', 'sells_digital')


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'game', 'target_price', 'alert_enabled', 'added_on')
    list_filter = ('alert_enabled', 'added_on')
    search_fields = ('user__username', 'game__title')


@admin.register(PriceListing)
class PriceListingAdmin(admin.ModelAdmin):
    list_display = ('game', 'store', 'current_price', 'format_type', 'last_updated')
    list_filter = ('format_type', 'store')
    search_fields = ('game__title',)


@admin.register(StorePreference)
class StorePreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'store', 'show_in_results')
    list_filter = ('show_in_results',)


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ('get_game_title', 'recorded_price', 'timestamp')

    # Un pequeño truco para mostrar el título del juego directamente en el historial
    def get_game_title(self, obj):
        return obj.price_listing.game.title

    get_game_title.short_description = 'Game'