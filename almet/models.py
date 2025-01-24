from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

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
    tel = models.CharField(max_length=20)

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

class Appeals(models.Model):
    id_sitizen = models.ForeignKey(Citizen, on_delete=models.CASCADE)
    date_time = models.DateTimeField()
    id_category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description_problem = models.TextField()
    photo = models.TextField(blank=True, null=True)
    id_sotrudnik = models.ForeignKey(Sotrudniki, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"Appeal {self.id} by {self.id_sitizen}"

class Processing_appeals(models.Model):
    id_appeal = models.ForeignKey(Appeals, on_delete=models.CASCADE)
    id_status = models.ForeignKey(Status, on_delete=models.CASCADE)
    date_time_setting_status = models.DateTimeField()
    photo = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Processing {self.id} for Appeal {self.id_appeal}"

class Message(models.Model):
    id_appeals = models.ForeignKey(Appeals, on_delete=models.CASCADE)
    id_sotrudnik = models.ForeignKey(Sotrudniki, on_delete=models.CASCADE, blank=True, null=True)
    id_sitizen = models.ForeignKey(Citizen, on_delete=models.CASCADE, blank=True, null=True)
    message = models.TextField()
    created_at = models.DateTimeField()

    def __str__(self):
        return f"Message {self.id} by {self.id_sotrudnik or self.id_sitizen}"

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
    # у