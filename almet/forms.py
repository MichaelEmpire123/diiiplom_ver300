from django import forms
from django.core.exceptions import ValidationError
from .models import Appeals, Message, Service


def validate_image_format(file):
    """Проверяет, что файл является изображением в допустимом формате."""
    valid_formats = ['image/png', 'image/jpeg', 'image/jpg', 'image/bmp']
    if file.content_type not in valid_formats:
        raise ValidationError('Файл должен быть в формате PNG, JPG, JPEG или BMP.')
    max_size = 5 * 1024 * 1024  # 5 МБ
    if file.size > max_size:
        raise ValidationError('Размер файла не должен превышать 5 МБ.')


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

        # Добавляем валидатор для фото
        self.fields['photo'].validators.append(validate_image_format)



class EmployeeRegistrationForm(forms.Form):
    email = forms.EmailField(label='Email')
    surname = forms.CharField(label='Фамилия')
    name = forms.CharField(label='Имя')
    patronymic = forms.CharField(label='Отчество', required=False)
    service = forms.ModelChoiceField(queryset=Service.objects.all(), label='Служба')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Переопределяем labels и добавляем классы Bootstrap
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['surname'].widget.attrs.update({'class': 'form-control'})
        self.fields['name'].widget.attrs.update({'class': 'form-control'})
        self.fields['patronymic'].widget.attrs.update({'class': 'form-control'})
        self.fields['service'].widget.attrs.update({'class': 'form-control'})


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


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['message']