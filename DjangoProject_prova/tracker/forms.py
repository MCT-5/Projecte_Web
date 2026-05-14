from django import forms
from .models import WishlistItem, Game, PriceListing, Store


class WishlistItemForm(forms.ModelForm):
    class Meta:
        model = WishlistItem
        fields = ['game', 'target_price', 'alert_enabled']
        widgets = {
            'target_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }


class WishlistItemUpdateForm(forms.ModelForm):
    class Meta:
        model = WishlistItem
        fields = ['target_price', 'alert_enabled']
        widgets = {
            'target_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }


class GameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ['title', 'platform', 'genre', 'cover_image_url']
        widgets = {
            'cover_image_url': forms.URLInput(attrs={'placeholder': 'https://...'}),
        }


class PriceListingForm(forms.ModelForm):
    class Meta:
        model = PriceListing
        fields = ['game', 'store', 'current_price', 'format_type', 'product_url']
        widgets = {
            'current_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'product_url': forms.URLInput(attrs={'placeholder': 'https://...'}),
        }