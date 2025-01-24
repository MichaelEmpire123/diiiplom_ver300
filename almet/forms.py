from django import forms
from django.core.exceptions import ValidationError
from .models import Appeals, Message


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
        self.fields['photo'].validators.append(validate_image_format)
class AppealForm(forms.ModelForm):
    class Meta:
        model = Appeals
        fields = ['id_category', 'description_problem', 'photo']

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['message']