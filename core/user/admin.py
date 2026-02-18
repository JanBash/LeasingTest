from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html  # Нужно для отображения картинок
from .models import User, ClientProfile


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Настройка админки для кастомной модели User.
    Теперь с поддержкой фото и сканов документов.
    """
    list_display = ('username', 'email', 'phone', 'avatar_preview', 'is_staff_member', 'is_staff')
    list_filter = ('is_staff_member', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'phone', 'first_name', 'last_name')

    # Делаем поле с картинкой "только для чтения", чтобы видеть превью
    readonly_fields = ('avatar_preview_large',)

    # Настройка формы редактирования (Группируем поля)
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('phone', 'is_staff_member')
        }),
        ('Фотографии и Документы', {
            'fields': (
                'avatar', 'avatar_preview_large',
                'passport_front', 'passport_back'
            ),
            'description': 'Загрузите сканы паспорта и фото профиля здесь.'
        }),
    )

    # Настройка формы создания
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация', {
            'fields': ('phone', 'is_staff_member', 'avatar', 'passport_front', 'passport_back')
        }),
    )

    # --- МЕТОДЫ ДЛЯ ОТОБРАЖЕНИЯ КАРТИНОК ---

    def avatar_preview(self, obj):
        """Маленькая иконка для списка"""
        if obj.avatar:
            return format_html('<img src="{}" style="width: 30px; height: 30px; border-radius: 50%;" />',
                               obj.avatar.url)
        return "-"

    avatar_preview.short_description = "Аватар"

    def avatar_preview_large(self, obj):
        """Большое превью внутри карточки"""
        if obj.avatar:
            return format_html('<img src="{}" style="max-height: 200px; border-radius: 10px;" />', obj.avatar.url)
        return "Фото не загружено"

    avatar_preview_large.short_description = "Предпросмотр фото"


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    """
    Админка для анкет клиентов (текстовые данные).
    """
    list_display = ('full_name', 'phone', 'email', 'passport_series', 'passport_number', 'user_link', 'created_at')
    list_display_links = ('full_name',)
    search_fields = ('full_name', 'phone', 'email', 'passport_number')
    ordering = ('-created_at',)

    # Добавляем поиск по связанному юзеру
    autocomplete_fields = ['user']

    fieldsets = (
        ('Связь с аккаунтом', {
            'fields': ('user',)
        }),
        ('Основные данные', {
            'fields': ('full_name', 'email', 'phone')
        }),
        ('Паспортные данные', {
            'fields': ('passport_series', 'passport_number', 'passport_date', 'registration_address')
        }),
        ('Прочее', {
            'fields': ('comment', 'created_at')
        }),
    )

    readonly_fields = ('created_at',)

    def user_link(self, obj):
        """Ссылка на основной профиль User (где лежат фото)"""
        if obj.user:
            return obj.user.username
        return "-"

    user_link.short_description = "Login (User)"