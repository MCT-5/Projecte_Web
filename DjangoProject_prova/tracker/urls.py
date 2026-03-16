from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    # Vistas de autenticación integradas en Django
    path('login/', auth_views.LoginView.as_view(template_name='tracker/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    # Vista personalizada para el registro
    path('register/', views.register, name='register'),

    # Una página de inicio temporal para ver quetodo funciona

    # Captura el ID del juego en la URL
    path('game/<int:game_id>/', views.game_detail, name='game_detail'),
    path('wishlist/', views.my_wishlist, name='my_wishlist'),
    path('game/<int:game_id>/add-wishlist/', views.add_to_wishlist, name='add_to_wishlist'),
]