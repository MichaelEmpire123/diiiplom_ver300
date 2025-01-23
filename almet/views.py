from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import User, Citizen, Street, City


def index(request):
    return render(request, 'almet/index.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('profile')
        else:
            return render(request, 'auth/login.html', {'error': 'Invalid credentials'})
    return render(request, 'auth/login.html')

def register_view(request):
    if request.method == 'POST':
        # Получаем данные из формы
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']
        surname = request.POST['familia']
        name = request.POST['name']
        patronymic = request.POST['otchestvo']
        tel = request.POST['tel']

        # Проверяем, совпадают ли пароли
        if password != password2:
            return render(request, 'auth/register.html', {'error': 'Пароли не совпадают'})

        # Создаем пользователя
        try:
            user = User.objects.create_user(email=email, password=password)
            # Создаем запись в таблице Citizen без города и улицы
            citizen = Citizen.objects.create(
                surname=surname,
                name=name,
                patronymic=patronymic,
                tel=tel,
                email=email,
                house="",  # Пустое значение
                flat=None  # Пустое значение
            )
            user.id_citizen = citizen
            user.save()

            # Авторизуем пользователя
            login(request, user)
            return redirect('profile')
        except Exception as e:
            return render(request, 'auth/register.html', {'error': str(e)})

    return render(request, 'auth/register.html')

@login_required
def profile_view(request):
    return render(request, 'auth/profile.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы.')
    return redirect('index')


@login_required
def update_profile(request):
    if request.method == 'POST':
        # Получаем данные из формы
        city_name = request.POST.get('city')
        street_name = request.POST.get('street')
        house = request.POST.get('house')
        flat = request.POST.get('flat')

        # Получаем или создаем город и улицу
        city, _ = City.objects.get_or_create(name_city=city_name)
        street, _ = Street.objects.get_or_create(name_street=street_name)

        # Обновляем данные пользователя
        citizen = request.user.id_citizen
        citizen.id_city = city
        citizen.id_street = street
        citizen.house = house
        citizen.flat = flat
        citizen.save()

        return redirect('profile')

    return render(request, 'auth/update_profile.html')

