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


    # Администратор
    path('administrator/categories/', views.admin_categories, name='admin_categories'),
    path('administrator/categories/edit/<int:category_id>/', views.edit_category, name='edit_category'),
    path('administrator/categories/delete/<int:category_id>/', views.delete_category, name='delete_category'),
    path('administrator/users/', views.admin_users, name='admin_users'),
    path('administrator/create_employee/', views.admin_create_employee, name='admin_create_employee'),
    path('administrator/all_appeals/', views.admin_all_appeals, name='admin_all_appeals'),
]