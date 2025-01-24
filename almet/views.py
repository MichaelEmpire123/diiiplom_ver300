from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .forms import AppealForm, MessageForm
from .models import User, Citizen, Street, City, Status, Appeals, Message


def index(request):
    return render(request, 'almet/index.html')

def login_view(request):
    if request.method == 'POST':
        # Получаем данные из формы
        login_input = request.POST.get('login_input')  # Поле для email или телефона
        password = request.POST.get('password')

        # Проверяем, что все поля заполнены
        if not login_input or not password:
            messages.error(request, 'Пожалуйста, заполните все поля.')
            return render(request, 'auth/login.html')

        # Проверяем, является ли введённое значение email или телефоном
        if '@' in login_input:
            # Если введён email
            user = authenticate(request, email=login_input, password=password)
        else:
            # Если введён телефон
            try:
                citizen = Citizen.objects.get(tel=login_input)
                user = authenticate(request, email=citizen.email, password=password)
            except Citizen.DoesNotExist:
                user = None

        # Проверяем, успешна ли аутентификация
        if user is not None:
            login(request, user)
            return redirect('profile')
        else:
            messages.error(request, 'Неверный email/телефон или пароль.')
            return render(request, 'auth/login.html')

    return render(request, 'auth/login.html')



def register_view(request):
    if request.method == 'POST':
        # Получаем данные из формы
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        surname = request.POST.get('familia')
        name = request.POST.get('name')
        patronymic = request.POST.get('otchestvo')
        tel = request.POST.get('tel')

        # Проверяем, совпадают ли пароли
        if password != password2:
            messages.error(request, 'Пароли не совпадают.')
            return render(request, 'auth/register.html')

        # Проверяем, что все обязательные поля заполнены
        if not email or not password or not surname or not name or not tel:
            messages.error(request, 'Пожалуйста, заполните все обязательные поля.')
            return render(request, 'auth/register.html')

        # Создаем пользователя и запись в таблице Citizen
        try:
            # Создаем пользователя
            user = User.objects.create_user(email=email, password=password)

            # Создаем запись в таблице Citizen
            citizen = Citizen.objects.create(
                surname=surname,
                name=name,
                patronymic=patronymic,
                tel=tel,
                email=email,
                id_city=None,  # Город можно указать позже
                id_street=None,  # Улицу можно указать позже
                house="",  # Указываем пустую строку вместо NULL
                flat=0  # Указываем значение по умолчанию
            )

            # Связываем пользователя с записью в таблице Citizen
            user.id_citizen = citizen
            user.save()

            # Авторизуем пользователя
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('profile')
        except Exception as e:
            messages.error(request, f'Ошибка при регистрации: {str(e)}')
            return render(request, 'auth/register.html')

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
    # Получаем текущего пользователя и связанного с ним жителя
    user = request.user
    citizen = user.id_citizen

    if request.method == 'POST':
        # Получаем данные из формы
        surname = request.POST.get('surname')
        name = request.POST.get('name')
        patronymic = request.POST.get('patronymic')
        tel = request.POST.get('tel')
        email = request.POST.get('email')
        city_name = request.POST.get('city')
        street_name = request.POST.get('street')
        house = request.POST.get('house')
        flat = request.POST.get('flat')

        # Обновляем данные жителя
        citizen.surname = surname
        citizen.name = name
        citizen.patronymic = patronymic
        citizen.tel = tel
        citizen.email = email
        citizen.house = house
        citizen.flat = flat

        # Получаем или создаем город и улицу
        if city_name:
            city, _ = City.objects.get_or_create(name_city=city_name)
            citizen.id_city = city
        if street_name:
            street, _ = Street.objects.get_or_create(name_street=street_name)
            citizen.id_street = street

        # Сохраняем изменения
        citizen.save()
        messages.success(request, 'Профиль успешно обновлён.')
        return redirect('profile')

    # Отображаем форму с текущими данными
    return render(request, 'auth/update_profile.html')


# ОБращения
@login_required
def create_appeal(request):
    if request.method == 'POST':
        form = AppealForm(request.POST, request.FILES)
        if form.is_valid():
            appeal = form.save(commit=False)
            appeal.id_sitizen = request.user.id_citizen
            appeal.status = Status.objects.get(name_status='Принято')
            appeal.date_time = timezone.now()  # Устанавливаем текущее время
            appeal.save()
            return redirect('profile')
    else:
        form = AppealForm()
    return render(request, 'appeals/create_appeal.html', {'form': form})


@login_required
def view_appeals(request):
    appeals = Appeals.objects.filter(id_sitizen=request.user.id_citizen)
    return render(request, 'appeals/view_appeals.html', {'appeals': appeals})


@login_required
def chat(request, appeal_id):
    appeal = get_object_or_404(Appeals, id=appeal_id)
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.id_appeals = appeal
            message.id_sitizen = request.user.id_citizen
            message.save()
            return redirect('chat', appeal_id=appeal_id)
    else:
        form = MessageForm()
    messages = Message.objects.filter(id_appeals=appeal)
    return render(request, 'chat.html', {'appeal': appeal, 'messages': messages, 'form': form})