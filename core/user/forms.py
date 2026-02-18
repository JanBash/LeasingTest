from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db import transaction
from .models import User, ClientProfile


class ClientSignUpForm(UserCreationForm):
    full_name = forms.CharField(label="ФИО / Компания", max_length=255)
    phone = forms.CharField(label="Телефон", max_length=20)
    email = forms.EmailField(label="Email")

    passport_series = forms.CharField(label="Серия паспорта", required=False)
    passport_number = forms.CharField(label="Номер паспорта", required=False)
    passport_date = forms.DateField(
        label="Дата выдачи",
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date'
        }))
    registration_address = forms.CharField(label="Адрес регистрации", required=False)

    avatar = forms.ImageField(label="Фото клиента", required=False)
    passport_front = forms.ImageField(label="Фото паспорта (Лицевая)", required=False)
    passport_back = forms.ImageField(label="Фото паспорта (Оборот)", required=False)


    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'avatar', 'passport_front', 'passport_back')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff_member = False
        user.is_staff = False
        if commit:
            user.save()

            ClientProfile.objects.update_or_create(
                user=user,
                defaults = {
                    'full_name': self.cleaned_data['full_name'],
                    'phone': self.cleaned_data['phone'],
                    'email': self.cleaned_data['email'],
                    'passport_series': self.cleaned_data['passport_series'],
                    'passport_number': self.cleaned_data['passport_number'],
                    'passport_date': self.cleaned_data['passport_date'],
                    'registration_address': self.cleaned_data['registration_address']
                }
            )
        return user


class StaffSignUpForm(UserCreationForm):
    first_name = forms.CharField(
        label='Имя',
        required=True
    )
    last_name = forms.CharField(
        label="Фамилия",
        required=True
    )
    email = forms.EmailField(
        label="Email",
        required=False
    )
    phone = forms.CharField(
        label="Номер телефона",
        required=True
    )

    is_superuser_flag = forms.BooleanField(
        label="Выдать права администратора",
        required=False,
        initial=False,
        help_text="Если отмечено, сотрудник получит полный доступ ко всему сайту."
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name == 'is_superuser_flag':
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=False)

        user.is_staff = True
        user.is_staff_member = True

        if self.cleaned_data['is_superuser_flag']:
            user.is_superuser = True
        else:
            user.is_superuser = False

        if commit:
            user.save()

        return user


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Имя пользователя',
        'id': 'floatingInput'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Пароль',
        'id': 'floatingPassword'
    }))
