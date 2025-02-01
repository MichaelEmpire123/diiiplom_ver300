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
    path('view_appeals/detail/<int:appeal_id>/', views.appeal_detail, name='appeal_detail'),
    path('view_appeals/detail/<int:appeal_id>/edit/', views.edit_appeal, name='edit_appeal'),
    path('view_appeals/detail/<int:appeal_id>/delete/', views.delete_appeal, name='delete_appeal'),

    # чат
    path('chat/<int:appeal_id>/', views.chat, name='chat'),

    # Служба
    path('employee/appeals/', views.employee_appeals, name='employee_appeals'),
    path('employee/appeals/<int:appeal_id>/', views.view_appeal, name='view_appeal'),
    path('employee/create-report/', views.create_report, name='create_report'),

    # Администратор
    path('administrator/categories/', views.admin_categories, name='admin_categories'),
    path('administrator/categories/edit/<int:category_id>/', views.edit_category, name='edit_category'),
    path('administrator/categories/delete/<int:category_id>/', views.delete_category, name='delete_category'),
    path('administrator/users/', views.admin_users, name='admin_users'),
    path('administrator/users/change_role/<int:user_id>/', views.change_role, name='change_role'),
    path('administrator/users/delete_user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('administrator/create_service/', views.admin_create_service, name='admin_create_service'),  # Новый маршрут
    path('administrator/edit_service/<int:service_id>', views.admin_edit_service, name='admin_edit_service'),  # Новый маршрут
    path('administrator/delete_service/<int:service_id>/', views.admin_delete_service, name='admin_delete_service'),
    path('administrator/create_employee/', views.admin_create_employee, name='admin_create_employee'),
    path('administrator/all_appeals/', views.admin_all_appeals, name='admin_all_appeals'),
    path('administrator/all_appeals/<int:appeal_id>/', views.admin_view_appeal, name='admin_view_appeal'),

    path('administrator/assign_service/<int:appeal_id>/', views.assign_service, name='assign_service')
]




