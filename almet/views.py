import secrets
import string

from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from .forms import AppealForm, MessageForm, ServiceForm, EmployeeRegistrationForm
from .models import User, Citizen, Street, City, Status, Appeals, Message, Processing_appeals, Category, Sotrudniki
from django.db.models import OuterRef, Subquery
import xml.etree.ElementTree as ET

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

        user = None

        # Проверяем, является ли введённое значение email
        if '@' in login_input:
            # Если введён email, проверяем как жителя, так и сотрудника
            print(f"Пытаемся аутентифицировать пользователя с email: {login_input}")
            try:
                # Ищем пользователя по email
                user = User.objects.get(email=login_input)
                print(f"Найден пользователь: {user}")

                # Проверяем пароль вручную
                if user.check_password(password):
                    print("Пароль верный. Аутентификация успешна.")
                    login(request, user)
                    return redirect('profile')
                else:
                    print("Неверный пароль.")
                    messages.error(request, 'Неверный email/телефон или пароль.')
            except User.DoesNotExist:
                print("Пользователь с таким email не найден.")
                messages.error(request, 'Неверный email/телефон или пароль.')
        else:
            # Если введён телефон, проверяем только жителя
            try:
                citizen = Citizen.objects.get(tel=login_input)
                print(f"Найден житель с телефоном: {login_input}")
                user = authenticate(request, email=citizen.email, password=password)
                print(f"Результат аутентификации: {user}")

                if user is not None:
                    login(request, user)
                    return redirect('profile')
                else:
                    messages.error(request, 'Неверный email/телефон или пароль.')
            except Citizen.DoesNotExist:
                # Если телефон не найден, сообщаем об ошибке
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


# Житель
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
            # Создаем обращение
            appeal = form.save(commit=False)
            appeal.id_sitizen = request.user.id_citizen
            appeal.date_time = timezone.now()
            appeal.save()  # Сохраняем обращение, чтобы получить id

            # Получаем статус "Принято" (ID = 1)
            status = Status.objects.get(id=1)  # Или name_status='Принято'

            # Создаем запись в Processing_appeals
            Processing_appeals.objects.create(
                id_appeal=appeal,
                id_status=status,
                date_time_setting_status=timezone.now(),
                # Фото отчета пока не привязываем
            )

            return redirect('profile')
    else:
        form = AppealForm()
    return render(request, 'appeals/create_appeal.html', {'form': form})


@login_required
def view_appeals(request):
    # Получаем последний статус для каждого обращения
    latest_status_subquery = Processing_appeals.objects.filter(
        id_appeal=OuterRef('id')
    ).order_by('-date_time_setting_status').values('id_status__name_status')[:1]

    # Аннотируем обращения последним статусом
    appeals = Appeals.objects.filter(id_sitizen=request.user.id_citizen).annotate(
        latest_status=Subquery(latest_status_subquery)
    )

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


# Администратор
# Проверка, является ли пользователь администратором
def is_admin(user):
    return user.is_staff or user.is_superuser

# Страница управления категориями
@login_required
@user_passes_test(is_admin)
def admin_categories(request):
    if request.method == 'POST':
        # Добавление категории
        if 'add_category' in request.POST:
            name_official = request.POST.get('name_official')
            name_short = request.POST.get('name_short')
            if name_official:
                Category.objects.create(name_official=name_official, name_short=name_short)
                messages.success(request, 'Категория успешно добавлена.')
            else:
                messages.error(request, 'Официальное название обязательно.')

        # Загрузка XML
        elif 'upload_xml' in request.POST:
            xml_file = request.FILES.get('xml_file')
            if xml_file:
                try:
                    tree = ET.parse(xml_file)
                    root = tree.getroot()

                    # Проверяем, что корневой элемент - <categories>
                    if root.tag != 'categories':
                        messages.error(request, 'Некорректный формат XML: ожидается корневой элемент <categories>.')
                        return redirect('admin_categories')

                    # Обрабатываем каждую категорию
                    for item in root.findall('category'):
                        name_official = item.find('name_official')
                        name_short = item.find('name_short')

                        # Проверяем, что элемент <name_official> существует и не пустой
                        if name_official is not None and name_official.text:
                            # Создаем категорию, если название не пустое
                            Category.objects.create(
                                name_official=name_official.text,
                                name_short=name_short.text if name_short is not None else None
                            )
                        else:
                            messages.warning(request, 'Найдена категория без названия. Пропущено.')

                    messages.success(request, 'Категории успешно загружены из XML.')
                except ET.ParseError as e:
                    messages.error(request, f'Ошибка при разборе XML: {str(e)}')
                except Exception as e:
                    messages.error(request, f'Ошибка при обработке XML: {str(e)}')
            else:
                messages.error(request, 'Файл не выбран.')

        # Массовое удаление
        elif 'mass_delete' in request.POST:
            selected_categories = request.POST.getlist('selected_categories')
            if selected_categories:
                Category.objects.filter(id__in=selected_categories).delete()
                messages.success(request, 'Выбранные категории успешно удалены.')
            else:
                messages.error(request, 'Не выбрано ни одной категории для удаления.')

    categories = Category.objects.all()
    return render(request, 'admin/categories.html', {'categories': categories})


# Администратор:: Изменение данных категорий
@login_required
@user_passes_test(is_admin)
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == 'POST':
        # Получаем данные из формы
        name_official = request.POST.get('name_official')
        name_short = request.POST.get('name_short')

        # Обновляем данные категории
        if name_official:
            category.name_official = name_official
            category.name_short = name_short
            category.save()
            messages.success(request, 'Категория успешно изменена.')
            return redirect('admin_categories')
        else:
            messages.error(request, 'Официальное название обязательно.')

    return render(request, 'admin/edit_category.html', {'category': category})


@login_required
@user_passes_test(is_admin)
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Категория успешно удалена.')
    return redirect('admin_categories')


# Страница управления пользователями
@login_required
@user_passes_test(is_admin)
def admin_users(request):
    users = User.objects.all()
    return render(request, 'admin/users.html', {'users': users})



# Страница создания городской службы на сайте
@login_required
@user_passes_test(is_admin)
def admin_create_service(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Городская служба успешно создана.')
            return redirect('admin_create_service')
    else:
        form = ServiceForm()

    return render(request, 'admin/create_service.html', {'form': form})


# Страница создания сотрудника городской службы
@login_required
@user_passes_test(is_admin)
def admin_create_employee(request):
    if request.method == 'POST':
        form = EmployeeRegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            surname = form.cleaned_data['surname']
            name = form.cleaned_data['name']
            patronymic = form.cleaned_data['patronymic']
            service = form.cleaned_data['service']

            # Генерируем случайный пароль
            alphabet = string.ascii_letters + string.digits
            password = ''.join(secrets.choice(alphabet) for i in range(12))  # Пароль из 12 символов


            # Создаем пользователя и запись в таблице Sotrudniki
            try:
                # Создаем пользователя
                user = User.objects.create_user(email=email, password=password)  # Передаем password, а не hashed_password

                # Создаем запись в таблице Sotrudniki
                employee = Sotrudniki.objects.create(
                    surname=surname,
                    name=name,
                    patronymic=patronymic,
                    id_service=service
                )

                # Связываем пользователя с записью в таблице Sotrudniki
                user.id_sotrudnik = employee
                user.save()

                # Создаем текстовый файл с паролем
                file_content = f"Email: {email}\nФамилия: {surname}\nИмя: {name}\nПароль: {password}"
                response = HttpResponse(file_content, content_type='text/plain')
                response['Content-Disposition'] = f'attachment; filename="employee_{employee.id}_password.txt"'

                # Авторизуем пользователя
                messages.success(request, 'Регистрация сотрудника прошла успешно! Пароль скачан.')
                return response
            except Exception as e:
                messages.error(request, f'Ошибка при регистрации: {str(e)}')
                return render(request, 'auth/register_employee.html', {'form': form})
    else:
        form = EmployeeRegistrationForm()
    return render(request, 'admin/create_employee.html', {'form': form})

# Страница просмотра всех обращений
@login_required
@user_passes_test(is_admin)
def admin_all_appeals(request):
    appeals = Appeals.objects.all()
    return render(request, 'admin/all_appeals.html', {'appeals': appeals})