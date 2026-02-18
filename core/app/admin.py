from django.contrib import admin
from .models import Vehicle, Contract, Inspection, VehiclePhoto, VehicleDocument


# --- ИНЛАЙНЫ (Вставки внутри карточки авто) ---

class VehiclePhotoInline(admin.TabularInline):
    model = VehiclePhoto
    extra = 1
    verbose_name = "Фотография"
    verbose_name_plural = "Фотогалерея"


class VehicleDocumentInline(admin.TabularInline):
    model = VehicleDocument
    extra = 0
    verbose_name = "Документ"
    verbose_name_plural = "Документы (PDF/Word)"


# --- АДМИНКА АВТОМОБИЛЕЙ ---

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    # Столбцы в списке
    list_display = ('brand', 'model_name', 'license_plate', 'year', 'overall_status', 'wialon_imei_display')
    # Кликабельные ссылки
    list_display_links = ('brand', 'model_name')
    # Поиск
    search_fields = ('vin', 'brand', 'model_name', 'license_plate', 'wialon_imei')
    # Фильтры справа
    list_filter = ('overall_status', 'body_type', 'transmission')

    # Поле ID Wialon делаем "только для чтения", чтобы случайно не сломать связь
    readonly_fields = ('wialon_id',)

    # Красивая группировка полей
    fieldsets = (
        ('Основные данные', {
            'fields': ('brand', 'model_name', 'year', 'color', 'vin', 'license_plate')
        }),
        ('Медиа', {
            'fields': ('video', 'computer_assessment'),
        }),
        ('GPS Мониторинг', {
            'fields': ('wialon_imei', 'wialon_id'),
        }),
        ('Характеристики', {
            'fields': ('mileage', 'engine_volume', 'engine_type', 'transmission', 'drive_type', 'body_type')
        }),
        # --- ОБНОВЛЕННЫЙ БЛОК ОЦЕНОК ---
        ('Техническое состояние (Рейтинг)', {
            'fields': (
                'engine_rating',
                'transmission_rating',
                'chassis_rating',
                'tire_tread',  # Шины сюда же
                'overall_status'
            )
        }),
        ('Владелец', {
            'fields': ('full_name_of_contractor',)
        }),
        # Сюда можно оставить остальные мелкие галочки, если вы их не удалили (свет, дворники и т.д.)
        ('Прочее оборудование', {
            'classes': ('collapse',),
            'fields': (
                'window_operation', 'sound_signal_operation',
                'windscreen_wipers_wiper_motor', 'headlights_sidelights_turn_signals',
                'stove_in_the_salon', 'Alarms_locks_keys'
            )
        }),
    )

    inlines = [VehiclePhotoInline, VehicleDocumentInline]

    # Красивое отображение IMEI в списке
    def wialon_imei_display(self, obj):
        return obj.wialon_imei if obj.wialon_imei else "-"

    wialon_imei_display.short_description = "GPS IMEI"


# --- АДМИНКА ДОГОВОРОВ ---

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    # ИСПРАВЛЕНО: заменили 'status_badge' на 'status'
    list_display = ('contract_number', 'vehicle', 'client', 'status', 'start_date', 'payment_due_day')

    # Теперь это сработает, так как поле 'status' есть в списке выше
    list_editable = ('status',)

    list_filter = ('status', 'start_date', 'payment_due_day')
    search_fields = (
    'contract_number', 'client__username', 'client__first_name', 'client__last_name', 'vehicle__license_plate')
    date_hierarchy = 'created_at'
    autocomplete_fields = ['vehicle', 'client']


# --- АДМИНКА ОСМОТРОВ ---

@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'date', 'inspector', 'short_comment')
    list_filter = ('date', 'inspector')
    search_fields = ('vehicle__license_plate', 'vehicle__vin')

    def short_comment(self, obj):
        return (obj.comment[:50] + '...') if obj.comment else "-"

    short_comment.short_description = "Комментарий"