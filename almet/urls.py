from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('update_profile/', views.update_profile, name='update_profile'),  # Новый маршрут2


    # обращения
    path('create_appeal/', views.create_appeal, name='create_appeal'),
    path('view_appeals/', views.view_appeals, name='view_appeals'),
    # чат
    path('chat/<int:appeal_id>/', views.chat, name='chat'),
]