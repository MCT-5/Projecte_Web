from django import forms
from .models import Review, WishlistItem

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, f'{i} ★') for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Escribe tu reseña aquí...'}),
        }
        labels = {
            'rating': 'Puntuación',
            'comment': 'Comentario',
        }

class WishlistItemForm(forms.ModelForm):
    class Meta:
        model = WishlistItem
        fields = ['target_price', 'alert_enabled']
        labels = {
            'target_price': 'Precio objetivo (€)',
            'alert_enabled': 'Activar alerta',
        }