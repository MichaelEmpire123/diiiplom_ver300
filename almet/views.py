import secrets
import string
import pandas as pd
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from .forms import AppealForm, MessageForm, ServiceForm, EmployeeRegistrationForm
from .models import User, Citizen, Street, City, Status, Appeals, Message, Processing_appeals, Category, Sotrudniki, \
    Service
from django.db.models import OuterRef, Subquery, Q
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


# Городская служба
@login_required
def employee_appeals(request):
    # Проверяем, что пользователь является сотрудником
    if not request.user.id_sotrudnik:
        return redirect('profile')  # Перенаправляем, если пользователь не сотрудник

    # Получаем службу, к которой относится сотрудник
    service = request.user.id_sotrudnik.id_service

    # Получаем обращения, назначенные на службу
    appeals = Appeals.objects.filter(id_service=service)
    return render(request, 'service/appeals_service.html', {'appeals': appeals})

@login_required
def view_appeal(request, appeal_id):
    # Получаем обращение
    appeal = get_object_or_404(Appeals, id=appeal_id)

    # Проверяем, что обращение назначено на службу сотрудника
    if appeal.id_service != request.user.id_sotrudnik.id_service:
        messages.error(request, 'У вас нет доступа к этому обращению.')
        return redirect('employee_appeals')

    # Получаем все возможные статусы
    statuses = Status.objects.all()

    # Обработка изменения статуса
    if request.method == 'POST':
        new_status_id = request.POST.get('status')
        if new_status_id:
            new_status = get_object_or_404(Status, id=new_status_id)
            # Создаем новую запись об изменении статуса
            Processing_appeals.objects.create(
                id_appeal=appeal,
                id_status=new_status,
                date_time_setting_status=timezone.now(),
            )
            messages.success(request, f'Статус обращения {appeal.id} изменен на {new_status.name_status}.')
            return redirect('view_appeal', appeal_id=appeal.id)

    # Получаем историю изменений статусов
    status_history = Processing_appeals.objects.filter(id_appeal=appeal).order_by('-date_time_setting_status')

    return render(request, 'service/view_appeal.html', {
        'appeal': appeal,
        'statuses': statuses,
        'status_history': status_history,
    })


# _______________________


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
def appeal_detail(request, appeal_id):
    appeal = get_object_or_404(Appeals, id=appeal_id, id_sitizen=request.user.id_citizen)
    statuses = Processing_appeals.objects.filter(id_appeal=appeal).order_by('-date_time_setting_status')

    return render(request, 'appeals/appeal_detail.html', {'appeal': appeal, 'statuses': statuses})



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

        # Загрузка файла (XML или Excel)
        elif 'upload_file' in request.POST:
            uploaded_file = request.FILES.get('file')
            if uploaded_file:
                file_name = uploaded_file.name.lower()  # Приводим имя файла к нижнему регистру
                try:
                    if file_name.endswith('.xml'):
                        # Обработка XML-файла
                        tree = ET.parse(uploaded_file)
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

                    elif file_name.endswith(('.xlsx', '.xls')):
                        # Обработка Excel-файла
                        df = pd.read_excel(uploaded_file)

                        # Проверяем, что в файле есть необходимая колонка
                        if 'name_official' not in df.columns:
                            messages.error(request, 'В файле отсутствует колонка "name_official".')
                            return redirect('admin_categories')

                        # Обрабатываем каждую строку в файле
                        for index, row in df.iterrows():
                            name_official = row['name_official']
                            name_short = row.get('name_short', None)  # Колонка name_short может отсутствовать

                            if pd.notna(name_official):  # Проверяем, что name_official не пустой
                                Category.objects.create(
                                    name_official=name_official,
                                    name_short=name_short
                                )
                            else:
                                messages.warning(request, f'Найдена категория без названия в строке {index + 1}. Пропущено.')

                        messages.success(request, 'Категории успешно загружены из Excel.')

                    else:
                        messages.error(request, 'Неподдерживаемый формат файла. Разрешены только XML, XLSX или XLS.')

                except ET.ParseError as e:
                    messages.error(request, f'Ошибка при разборе XML: {str(e)}')
                except pd.errors.EmptyDataError:
                    messages.error(request, 'Файл Excel пуст или имеет неправильный формат.')
                except Exception as e:
                    messages.error(request, f'Ошибка при обработке файла: {str(e)}')
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

    # Получаем все категории для отображения
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
    services = Service.objects.all()

    # Фильтр по роли
    role_filter = request.GET.get('role')
    if role_filter == 'citizen':
        users = users.filter(id_sotrudnik__isnull=True, is_staff=False, is_superuser=False)
    elif role_filter == 'employee':
        users = users.filter(id_sotrudnik__isnull=False)

    # Фильтр по службе
    service_filter = request.GET.get('service')
    if service_filter:
        users = users.filter(id_sotrudnik__id_service=service_filter)

    # Поиск по ФИО
    search_query = request.GET.get('search')
    if search_query:
        users = users.filter(
            Q(id_citizen__surname__icontains=search_query) |
            Q(id_citizen__name__icontains=search_query) |
            Q(id_citizen__patronymic__icontains=search_query) |
            Q(id_sotrudnik__surname__icontains=search_query) |
            Q(id_sotrudnik__name__icontains=search_query) |
            Q(id_sotrudnik__patronymic__icontains=search_query)
        )

    return render(request, 'admin/users.html', {
        'users': users,
        'services': services,
        'role_filter': role_filter,
        'service_filter': service_filter,
        'search_query': search_query,
    })


@login_required
@user_passes_test(is_admin)
def change_role(request, user_id):
    user = get_object_or_404(User, id=user_id)
    services = Service.objects.all()

    if request.method == 'POST':
        role = request.POST.get('role')
        service_id = request.POST.get('service')

        if role == 'employee':
            # Превращаем пользователя в сотрудника
            if not user.id_sotrudnik:
                service = get_object_or_404(Service, id=service_id)
                employee = Sotrudniki.objects.create(
                    surname=user.id_citizen.surname if user.id_citizen else 'Unknown',
                    name=user.id_citizen.name if user.id_citizen else 'Unknown',
                    id_service=service
                )
                user.id_sotrudnik = employee
                user.save()
                messages.success(request, f'Пользователь {user.email} теперь сотрудник.')
        elif role == 'user':
            # Превращаем сотрудника в пользователя
            if user.id_sotrudnik:
                user.id_sotrudnik.delete()
                user.id_sotrudnik = None
                user.save()
                messages.success(request, f'Сотрудник {user.email} теперь пользователь.')

        return redirect('admin_users')

    return render(request, 'admin/change_role.html', {
        'user': user,
        'services': services,
    })

@login_required
@user_passes_test(is_admin)
def delete_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)

        # Удаляем связанного жителя, если он существует
        if user.id_citizen:
            user.id_citizen.delete()

        # Удаляем связанного сотрудника, если он существует
        if user.id_sotrudnik:
            user.id_sotrudnik.delete()

        # Удаляем самого пользователя
        user.delete()

        messages.success(request, 'Пользователь и связанные данные успешно удалены.')
        return redirect('admin_users')  # Перенаправляем на страницу управления пользователями

    messages.error(request, 'Неверный запрос.')
    return redirect('admin_users')


# Страница создания городской службы на сайте
@login_required
@user_passes_test(is_admin)
def admin_create_service(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Городская служба успешно создана.')
            return redirect('admin_manage_services')
    else:
        form = ServiceForm()

        # Получаем все городские службы
    services = Service.objects.all()

    return render(request, 'admin/create_service.html', {'form': form, 'services': services})


@login_required
@user_passes_test(is_admin)
def admin_service_list(request):
    services = Service.objects.all()  # Получаем все городские службы
    return render(request, 'admin/create_service.html', {'services': services})


@login_required
@user_passes_test(is_admin)
def admin_edit_service(request, service_id):
    service = get_object_or_404(Service, id=service_id)  # Получаем службу по ID

    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)  # Используем instance для редактирования
        if form.is_valid():
            form.save()
            messages.success(request, 'Городская служба успешно обновлена.')
            return redirect('admin_create_service')  # Перенаправляем на список служб
    else:
        form = ServiceForm(instance=service)  # Передаём существующую службу в форму

    return render(request, 'admin/edit_service.html', {'form': form, 'service': service})


@login_required
@user_passes_test(is_admin)
def admin_delete_service(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    service.delete()
    messages.success(request, 'Городская служба успешно удалена.')
    return redirect('admin_create_service')



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
    services = Service.objects.all()  # Получаем все городские службы
    return render(request, 'admin/all_appeals.html', {
        'appeals': appeals,
        'services': services,  # Передаем службы в шаблон
    })

@login_required
@user_passes_test(is_admin)
def assign_service(request, appeal_id):
    appeal = get_object_or_404(Appeals, id=appeal_id)
    if request.method == 'POST':
        service_id = request.POST.get('service')
        if service_id:
            service = get_object_or_404(Service, id=service_id)
            appeal.id_service = service
            appeal.save()
            messages.success(request, f'Обращение {appeal.id} назначено на службу {service.name}.')
        else:
            appeal.id_service = None
            appeal.save()
            messages.success(request, f'Обращение {appeal.id} больше не назначено на службу.')
    return redirect('admin_all_appeals')





