from django.contrib import admin
from .models import (
    City, Street, Citizen, Service, Sotrudniki,
    Category, Status, Appeals, Processing_appeals,
    Message, User
)

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name_city')
    search_fields = ('name_city',)
@admin.register(Street)
class StreetAdmin(admin.ModelAdmin):
    list_display = ('id', 'name_street')
    search_fields = ('name_street',)
@admin.register(Citizen)
class CitizenAdmin(admin.ModelAdmin):
    list_display = ('id', 'surname', 'name', 'tel', 'email', 'id_city', 'id_street', 'house', 'flat')
    search_fields = ('surname', 'name', 'tel', 'email')
    list_filter = ('id_city', 'id_street')
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'id_city', 'id_street', 'house', 'flat', 'tel', 'description')
    search_fields = ('name', 'tel')
    list_filter = ('id_city', 'id_street')
@admin.register(Sotrudniki)
class SotrudnikiAdmin(admin.ModelAdmin):
    list_display = ('id', 'surname', 'name', 'patronymic', 'id_service')
    search_fields = ('surname', 'name')
    list_filter = ('id_service',)
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name_official', 'name_short')
    search_fields = ('name_official', 'name_short')
@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'name_status')
    search_fields = ('name_status',)
@admin.register(Appeals)
class AppealsAdmin(admin.ModelAdmin):
    list_display = ('id', 'id_sitizen', 'date_time', 'id_category', 'description_problem', 'id_sotrudnik', 'id_service')
    search_fields = ('id_sitizen__surname', 'id_sitizen__name', 'id_category__name_official')
    list_filter = ('id_category', 'id_sotrudnik')
@admin.register(Processing_appeals)
class ProcessingAppealsAdmin(admin.ModelAdmin):
    list_display = ('id', 'id_appeal', 'id_status', 'date_time_setting_status', 'photo')
    search_fields = ('id_appeal__id', 'id_status__name_status')
    list_filter = ('id_status',)
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'id_appeals', 'sender', 'created_at', 'image')
    search_fields = ('id_appeals__id', 'sender__surname', 'sender__name')
    list_filter = ('sender',)
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'id_citizen', 'id_sotrudnik', 'is_active', 'is_staff')
    search_fields = ('email',)
    list_filter = ('id_citizen', 'id_sotrudnik', 'is_active', 'is_staff')
