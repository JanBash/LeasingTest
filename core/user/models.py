from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    is_staff_member = models.BooleanField(
        default=False,
        verbose_name="Сотрудник компании"
    )
    phone = models.CharField(
        max_length=20,
        verbose_name="Телефон"
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name="Фото клиента"
    )
    passport_front = models.ImageField(
        upload_to='passports/',
        blank=True,
        null=True,
        verbose_name="Паспорт (лицевая сторона)"
    )
    passport_back = models.ImageField(
        upload_to='passports/',
        blank=True,
        null=True,
        verbose_name="Паспорт (Оборотная сторона)"
    )

    # Можно добавить фото аватарки сотрудника, если нужно

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        role = "Сотрудник" if self.is_staff_member else "Клиент"
        return f"{self.username} ({role})"


class ClientProfile(models.Model):
    """
    Анкета клиента.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='client_profile'
    )

    # Основные данные
    full_name = models.CharField(
        max_length=255,
        verbose_name="ФИО / Название компании"
    )
    email = models.EmailField(
        verbose_name="Email"
    )
    phone = models.CharField(
        max_length=20,
        verbose_name="Телефон"
    )

    # Паспортные данные
    passport_series = models.CharField(
        max_length=10,
        verbose_name="Серия паспорта",
        blank=True,
        null=True
    )
    passport_number = models.CharField(
        max_length=20,
        verbose_name="Номер паспорта",
        blank=True,
        null=True
    )
    passport_date = models.DateField(
        verbose_name="Дата выдачи",
        null=True,
        blank=True
    )
    registration_address = models.TextField(
        verbose_name="Адрес регистрации",
        blank=True,
        null=True
    )

    comment = models.TextField(
        blank=True,
        null=True,
        verbose_name="Комментарии"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    class Meta:
        verbose_name = "Профиль клиента"
        verbose_name_plural = "Профили клиентов"

    def __str__(self):
        return self.full_name