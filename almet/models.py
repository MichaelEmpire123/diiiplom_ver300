import shutil
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import os

class City(models.Model):
    name_city = models.CharField(max_length=100)

    def __str__(self):
        return self.name_city

class Street(models.Model):
    name_street = models.CharField(max_length=255)

    def __str__(self):
        return self.name_street

class Citizen(models.Model):
    surname = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    patronymic = models.CharField(max_length=255, blank=True, null=True)
    tel = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    id_city = models.ForeignKey('City', on_delete=models.SET_NULL, null=True, blank=True)
    id_street = models.ForeignKey('Street', on_delete=models.SET_NULL, null=True, blank=True)
    house = models.CharField(max_length=50, blank=True, null=True)  # Делаем поле необязательным
    flat = models.IntegerField(blank=True, null=True)  # Делаем поле необязательным

    def __str__(self):
        return f"{self.surname} {self.name}"

class Service(models.Model):
    name = models.CharField(max_length=255)
    id_city = models.ForeignKey(City, on_delete=models.CASCADE)
    id_street = models.ForeignKey(Street, on_delete=models.CASCADE)
    house = models.CharField(max_length=100)
    flat = models.IntegerField(blank=True, null=True)
    tel = models.TextField()

    def __str__(self):
        return self.name

class Sotrudniki(models.Model):
    surname = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    patronymic = models.CharField(max_length=100, blank=True, null=True)
    id_service = models.ForeignKey(Service, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.surname} {self.name}"

class Category(models.Model):
    name_official = models.CharField(max_length=255)
    name_short = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name_official

class Status(models.Model):
    name_status = models.CharField(max_length=100)

    def __str__(self):
        return self.name_status




def get_upload_path(instance, filename):
    """Генерация пути загрузки фото"""
    if isinstance(instance, Appeals):
        citizen = instance.id_sitizen
        appeal_id = instance.id
        date = timezone.now().strftime("%Y-%m-%d")
        return os.path.join('appeals', f'{appeal_id}_{citizen.id}_{citizen.surname}_{date}', filename)


def get_upload_path_processing(instance, filename):
    """Генерация пути загрузки фото для обработки обращений"""
    if instance.photo:
        return get_upload_path(instance.id_appeal, filename)
    return None  # Чтобы избежать ошибки


class Appeals(models.Model):
    id_sitizen = models.ForeignKey('Citizen', on_delete=models.CASCADE)
    date_time = models.DateTimeField()
    id_category = models.ForeignKey('Category', on_delete=models.CASCADE)
    description_problem = models.TextField()
    photo = models.ImageField(upload_to=get_upload_path, blank=True, null=True)
    id_sotrudnik = models.ForeignKey('Sotrudniki', on_delete=models.CASCADE, blank=True, null=True)
    id_service = models.ForeignKey('Service', on_delete=models.CASCADE, blank=True, null=True)  # Связь с городской службой

    def __str__(self):
        return f"Обращение {self.id} by {self.id_sitizen}"

    def delete(self, *args, **kwargs):
        """Удаление фото и папки обращения при удалении записи"""
        if self.photo:
            appeal_folder = os.path.dirname(self.photo.path)
            if os.path.exists(appeal_folder):
                shutil.rmtree(appeal_folder)  # Удаляем всю папку
        super().delete(*args, **kwargs)


class Processing_appeals(models.Model):
    id_appeal = models.ForeignKey(Appeals, on_delete=models.CASCADE)
    id_status = models.ForeignKey('Status', on_delete=models.CASCADE)
    date_time_setting_status = models.DateTimeField()
    photo = models.ImageField(upload_to=get_upload_path_processing, blank=True, null=True)

    def __str__(self):
        return f"Обработка {self.id} для обращения {self.id_appeal}"



class Message(models.Model):
    id_appeals = models.ForeignKey(Appeals, on_delete=models.CASCADE)
    id_sotrudnik = models.ForeignKey(Sotrudniki, on_delete=models.CASCADE, blank=True, null=True)
    id_sitizen = models.ForeignKey(Citizen, on_delete=models.CASCADE, blank=True, null=True)
    message = models.TextField()
    created_at = models.DateTimeField()

    def __str__(self):
        return f"Сообщение {self.id} by {self.id_sotrudnik or self.id_sitizen}"

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    id_citizen = models.ForeignKey('Citizen', on_delete=models.CASCADE, blank=True, null=True)
    id_sotrudnik = models.ForeignKey('Sotrudniki', on_delete=models.CASCADE, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email