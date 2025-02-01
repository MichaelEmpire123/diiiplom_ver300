from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Appeals, Message, Service


def validate_image_format(file):
    """Проверяет, что файл является изображением в допустимом формате."""
    valid_formats = ['image/png', 'image/jpeg', 'image/jpg', 'image/bmp']
    if file.content_type not in valid_formats:
        raise ValidationError('Файл должен быть в формате PNG, JPG, JPEG или BMP.')
    max_size = 100 * 1024 * 1024  # 5 МБ
    if file.size > max_size:
        raise ValidationError('Размер файла не должен превышать 100 МБ.')


class AppealForm(forms.ModelForm):
    class Meta:
        model = Appeals
        fields = ['id_category', 'description_problem', 'photo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Переопределяем labels на русский язык
        self.fields['id_category'].label = 'Категория'
        self.fields['description_problem'].label = 'Описание проблемы'
        self.fields['photo'].label = 'Фото проблемы'

        # Добавляем стили Bootstrap к полям
        for field_name, field in self.fields.items():
            if field_name == 'id_category':
                field.widget.attrs.update({
                    'class': 'form-select',  # Для выпадающего меню используем form-select
                    'placeholder': field.label,
                })
            else:
                field.widget.attrs.update({
                    'class': 'form-control',  # Для всех остальных полей — form-control
                    'placeholder': field.label,
                })

        # Добавляем валидатор для фото
        self.fields['photo'].validators.append(validate_image_format)

class Edit_AppealForm(forms.ModelForm):
    class Meta:
        model = Appeals
        fields = ['id_category', 'description_problem', 'photo']
        widgets = {
            'id_category': forms.Select(attrs={'class': 'form-control'}),
            'description_problem': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class EmployeeRegistrationForm(forms.Form):
    email = forms.EmailField(label='Email')
    surname = forms.CharField(label='Фамилия')
    name = forms.CharField(label='Имя')
    patronymic = forms.CharField(label='Отчество', required=False)
    service = forms.ModelChoiceField(queryset=Service.objects.all(), label='Служба')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем классы Bootstrap и плейсхолдеры
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите email'
        })
        self.fields['surname'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите фамилию'
        })
        self.fields['name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите имя'
        })
        self.fields['patronymic'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите отчество (необязательно)'
        })
        self.fields['service'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Выберите службу'
        })


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'id_city', 'id_street', 'house', 'flat', 'tel']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Переопределяем labels на русский язык
        self.fields['name'].label = 'Название службы'
        self.fields['id_city'].label = 'Город'
        self.fields['id_street'].label = 'Улица'
        self.fields['house'].label = 'Дом'
        self.fields['flat'].label = 'Квартира'
        self.fields['tel'].label = 'Телефон'

        # Добавляем классы Bootstrap и плейсхолдеры
        self.fields['name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите название службы'
        })
        self.fields['id_city'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Выберите город'
        })
        self.fields['id_street'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Выберите улицу'
        })
        self.fields['house'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите номер дома'
        })
        self.fields['flat'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите номер квартиры (необязательно)'
        })
        self.fields['tel'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите телефон'
        })



class ChangeRoleForm(forms.Form):
    ROLE_CHOICES = [
        ('user', 'Пользователь'),
        ('employee', 'Сотрудник'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, label='Роль')

class AssignServiceForm(forms.Form):
    service = forms.ModelChoiceField(queryset=Service.objects.all(), label='Служба')



class ReportForm(forms.Form):
    start_date = forms.DateField(
        label="Начальная дата",
        widget=forms.DateInput(attrs={'type': 'date'}),
        initial=timezone.now().replace(day=1)  # По умолчанию начало текущего месяца
    )
    end_date = forms.DateField(
        label="Конечная дата",
        widget=forms.DateInput(attrs={'type': 'date'}),
        initial=timezone.now()  # По умолчанию текущая дата
    )


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['message']



