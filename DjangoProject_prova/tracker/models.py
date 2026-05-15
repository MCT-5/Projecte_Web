from django.db import models
from django.contrib.auth.models import User


class Game(models.Model):
    title = models.CharField(max_length=255)
    platform = models.CharField(max_length=100)
    cover_image_url = models.URLField(max_length=500, blank=True, null=True)
    genre = models.CharField(max_length=100)

    class Meta:
        unique_together = ('title', 'platform')

    def __str__(self):
        return f"{self.title} ({self.platform})"


class Store(models.Model):
    name = models.CharField(max_length=100, unique=True)
    website_url = models.URLField(max_length=500)
    sells_physical = models.BooleanField(default=False)
    sells_digital = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class WishlistItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_items')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='wishlisted_by')
    target_price = models.DecimalField(max_digits=10, decimal_places=2)
    alert_enabled = models.BooleanField(default=True)
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'game')

    def __str__(self):
        return f"{self.user.username} - {self.game.title} (Target: {self.target_price})"


class PriceListing(models.Model):
    FORMAT_CHOICES = [
        ('FISICO', 'Físico'),
        ('DIGITAL', 'Digital'),
    ]

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='price_listings')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='price_listings')
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    format_type = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    product_url = models.URLField(max_length=500)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('game', 'store', 'format_type')

    def __str__(self):
        return f"{self.game.title} at {self.store.name} - {self.current_price}"


class StorePreference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='store_preferences')
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    show_in_results = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'store')  # Evita que un usuario tenga preferencias duplicadas para una misma tienda

    def __str__(self):
        return f"{self.user.username} pref: {self.store.name} (Show: {self.show_in_results})"


class PriceHistory(models.Model):
    price_listing = models.ForeignKey(PriceListing, on_delete=models.CASCADE, related_name='price_history')
    recorded_price = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.price_listing.game.title} - {self.recorded_price} on {self.timestamp.strftime('%Y-%m-%d')}"

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1 a 5 estrellas
    comment = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'game')  # Un usuario solo puede reseñar un juego una vez

    def __str__(self):
        return f"{self.user.username} - {self.game.title} ({self.rating}★)"