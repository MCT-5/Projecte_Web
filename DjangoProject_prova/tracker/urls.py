from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Home & auth
    path('', views.home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='tracker/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('register/', views.register, name='register'),

    # Games
    path('game/<int:game_id>/', views.game_detail, name='game_detail'),
    path('game/add/', views.GameCreateView.as_view(), name='game_add'),
    path('game/<int:pk>/edit/', views.GameUpdateView.as_view(), name='game_edit'),
    path('game/<int:pk>/delete/', views.GameDeleteView.as_view(), name='game_delete'),

    # Price listings
    path('game/<int:game_id>/price/add/', views.PriceListingCreateView.as_view(), name='pricelisting_add'),
    path('price/<int:pk>/edit/', views.PriceListingUpdateView.as_view(), name='pricelisting_edit'),
    path('price/<int:pk>/delete/', views.PriceListingDeleteView.as_view(), name='pricelisting_delete'),

    # Wishlist
    path('wishlist/', views.my_wishlist, name='my_wishlist'),
    path('game/<int:game_id>/add-wishlist/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/<int:pk>/edit/', views.WishlistItemUpdateView.as_view(), name='wishlist_edit'),
    path('wishlist/<int:pk>/delete/', views.WishlistItemDeleteView.as_view(), name='wishlist_delete'),

    # AJAX
    path('api/rawg-autocomplete/', views.rawg_autocomplete, name='rawg_autocomplete'),
]
