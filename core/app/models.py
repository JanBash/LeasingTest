from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import os
import string
import random

from .utils import find_wialon_id_by_imei


class Vehicle(models.Model):
    # --- Справочники (Choices) ---
    class BodyType(models.TextChoices):
        SEDAN = 'sedan', 'Седан'
        HATCHBACK = 'hatchback', 'Хэтчбек'
        SUV = 'suv', 'Кроссовер / Внедорожник'
        WAGON = 'wagon', 'Универсал'
        COUPE = 'coupe', 'Купе'
        MINIVAN = 'minivan', 'Минивэн'
        PICKUP = 'pickup', 'Пикап'
        VAN = 'van', 'Фургон'

    class EngineType(models.TextChoices):
        PETROL = 'petrol', 'Бензин'
        DIESEL = 'diesel', 'Дизель'
        HYBRID = 'hybrid', 'Гибрид'
        ELECTRIC = 'electric', 'Электро'
        GAS = 'GAS', 'Газ'

    class Transmission(models.TextChoices):
        MANUAL = 'manual', 'Механика'
        AUTOMATIC = 'automatic', 'Автомат'
        ROBOT = 'robot', 'Робот'
        CVT = 'cvt', 'Вариатор'

    class DriveType(models.TextChoices):
        FWD = 'fwd', 'Передний (FWD)'
        RWD = 'rwd', 'Задний (RWD)'
        AWD = 'awd', 'Полный (AWD/4WD)'

    # --- Основные поля ---
    vin = models.CharField(
        max_length=17,
        primary_key=True,
        verbose_name="VIN-номер"
    )
    wialon_imei = models.CharField(
        max_length = 50,
        blank = True,
        null = True,
        verbose_name = "Wialon EMEI (Unique ID)",
        help_text = "Введите Unique ID из свойств Wialon"
    )
    wialon_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        editable=False,
        verbose_name="System ID"
    )
    full_name_of_contractor = models.CharField(
        max_length=255,
        verbose_name="ФИО Исполнителя"
    )
    brand = models.CharField(
        max_length=50,
        verbose_name="Марка"
    )
    model_name = models.CharField(
        max_length=50,
        verbose_name="Модель"
    )
    color = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Цвет"
    )
    price = models.PositiveIntegerField(
        verbose_name="Цена"
    )
    year = models.PositiveIntegerField(
        verbose_name="Год выпуска"
    )
    license_plate = models.CharField(
        max_length=15,
        verbose_name="Гос. номер"
    )
    video = models.FileField(
        upload_to='vehicle_videos/',
        blank=True,
        null=True,
        verbose_name="Видео обзор(MP4)"
    )

    # Технические характеристики
    body_type = models.CharField(
        max_length=20,
        choices=BodyType.choices,
        default=BodyType.SEDAN,
        verbose_name="Тип кузова"
    )

    engine_type = models.CharField(
        max_length=20,
        choices=EngineType.choices,
        default=EngineType.PETROL,
        verbose_name="Тип двигателя"
    )

    # null=True, так как у электромобилей нет объема двигателя
    engine_volume = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name="Объём (л)"
    )
    engine_rating = models.PositiveSmallIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Состояние двигателя (1-5)"
    )

    transmission = models.CharField(
        max_length=20,
        choices=Transmission.choices,
        default=Transmission.AUTOMATIC,
        verbose_name="КПП"
    )
    transmission_rating = models.PositiveSmallIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Состояние КПП (1-5)"
    )

    drive_type = models.CharField(
        max_length=10,
        choices=DriveType.choices,
        default=DriveType.FWD,
        verbose_name="Привод"
    )

    mileage = models.PositiveIntegerField(
        verbose_name="Пробег (км)"
    )
    tire_tread = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Протектора шин / состояние резины",
        help_text="Например: 'Летние 5мм' или '80% износа'"
    )

    chassis_rating = models.PositiveSmallIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Состояние ходовой (1-5)"
    )
    computer_assessment = models.FileField(
        upload_to='assessment/',
        blank=True,
        null=True,
        verbose_name="Компьютерная диагностика (PDF)"
    )

    # Статусы
    STATUS_CHOICES = [
        ('ok', 'Исправен'),
        ('repair', 'Требует ремонта'),
        ('broken', 'Неисправен'),
    ]
    overall_status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='ok',
        verbose_name="Общий статус"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Техническое состояние автомобиля
    switching_state_of_transmission = models.BooleanField(
        default=True,
        verbose_name="Работа и состояние переключения МКПП или АКПП"
    )
    noise_in_engine_operation = models.BooleanField(
        default=False,
        verbose_name="Вибрация и посторонние шумы в работе двигателя"
    )
    chassis_steering_of_the_car = models.BooleanField(
        default=True,
        verbose_name="Ходовая и рулевая часть машины"
    )
    window_operation = models.BooleanField(
        default=True,
        verbose_name="Работа стеклоподъемников"
    )
    sound_signal_operation = models.BooleanField(
        default=True,
        verbose_name="Работа звукового сигнала"
    )
    windscreen_wipers_wiper_motor = models.BooleanField(
        default=True,
        verbose_name="Дворники и моторчик стеклоочистителя"
    )
    headlights_sidelights_turn_signals = models.BooleanField(
        default=True,
        verbose_name="Фары, габариты, поворотники"
    )
    stove_in_the_salon = models.BooleanField(
        default=True,
        verbose_name="Печка/Кондиционер салона"
    )
    alarms_locks_keys = models.BooleanField(
        default=True,
        verbose_name="Сигнализация, замки и ключи"
    )

    class Meta:
        verbose_name = "Автомобиль"
        verbose_name_plural = "Автомобили"


    def save(self, *args, **kwargs):
        # Если введен IMEI, но нет ID - пробуем найти ID
        if self.wialon_imei:
            # Небольшая оптимизация: ищем ID, только если он еще не найден 
            # или если мы поменяли IMEI (можно усложнить логику, но пока так)
            found_id = find_wialon_id_by_imei(self.wialon_imei)
            if found_id:
                self.wialon_id = str(found_id)
            else:
                # Если не нашли, можно очистить ID, чтобы не было путаницы
                # self.wialon_id = None 
                print(f"Внимание: Не удалось найти Wialon ID для IMEI {self.wialon_imei}")
        else:
            # Если стерли IMEI, стираем и ID
            self.wialon_id = None
            
        super().save(*args, **kwargs)


    def get_cover_image(self):
        first_photo = self.photos.first()
        if first_photo:
            return first_photo.image.url
        return None

    @property
    def current_contract(self):
        return self.contracts.filter(status='active').first()

    def __str__(self):
        # Пример вывода: BMW X5 (3.0 Diesel) - A123AA77
        engine_info = f"{self.engine_volume}L" if self.engine_volume else self.get_engine_type_display()
        return f"{self.brand} {self.model_name} ({engine_info}) - {self.license_plate}"


class VehicleDocument(models.Model):
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name="Автомобиль"
    )
    title = models.CharField(
        max_length=100,
        verbose_name="Название документа"
    )
    file = models.FileField(
        upload_to='vehicle_docs/',
        verbose_name="Файл (PDF)"
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def filename(self):
        return os.path.basename(self.file.name)

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"


class VehiclePhoto(models.Model):
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name="Автомобиль"
    )
    image = models.ImageField(
        upload_to='vehicle_gallery/',
        verbose_name="Фотография"
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Фотография авто"
        verbose_name_plural = "Галерея фотографий"


class DiagnosticReport(models.Model):
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='diagnostic_reports',
        verbose_name="Автомобиль"
    )
    mechanic = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Механик"
    )
    date = models.DateField(auto_now_add=True, verbose_name="Дата осмотра")
    created_at = models.DateTimeField(auto_now_add=True)

    # ==================================================
    # 1. ТОРМОЗНАЯ СИСТЕМА
    # ==================================================

    # --- Передняя ---
    brake_front_hose_l = models.BooleanField(default=False, verbose_name="Торм. шланг передний (L)")
    brake_front_hose_r = models.BooleanField(default=False, verbose_name="Торм. шланг передний (R)")

    brake_front_disc_l = models.BooleanField(default=False, verbose_name="Торм. диск передний (L)")
    brake_front_disc_r = models.BooleanField(default=False, verbose_name="Торм. диск передний (R)")

    brake_front_pads_l = models.BooleanField(default=False, verbose_name="Торм. колодки передние (L)")
    brake_front_pads_r = models.BooleanField(default=False, verbose_name="Торм. колодки передние (R)")

    # --- Задняя ---
    brake_rear_hose_l = models.BooleanField(default=False, verbose_name="Торм. шланг задний (L)")
    brake_rear_hose_r = models.BooleanField(default=False, verbose_name="Торм. шланг задний (R)")

    brake_rear_disc_l = models.BooleanField(default=False, verbose_name="Торм. диск задний (L)")
    brake_rear_disc_r = models.BooleanField(default=False, verbose_name="Торм. диск задний (R)")

    brake_rear_pads_l = models.BooleanField(default=False, verbose_name="Торм. колодки задние (L)")
    brake_rear_pads_r = models.BooleanField(default=False, verbose_name="Торм. колодки задние (R)")

    # ==================================================
    # 2. ПОДВЕСКА ПЕРЕДНЯЯ
    # ==================================================

    susp_front_shock_l = models.BooleanField(default=False, verbose_name="Амортизатор передний (L)")
    susp_front_shock_r = models.BooleanField(default=False, verbose_name="Амортизатор передний (R)")

    susp_front_mount_l = models.BooleanField(default=False, verbose_name="Опора стойки аморт. перед (L)")
    susp_front_mount_r = models.BooleanField(default=False, verbose_name="Опора стойки аморт. перед (R)")

    susp_front_boot_l = models.BooleanField(default=False, verbose_name="Пыльник/отбойник перед (L)")
    susp_front_boot_r = models.BooleanField(default=False, verbose_name="Пыльник/отбойник перед (R)")

    susp_front_spring_l = models.BooleanField(default=False, verbose_name="Пружина передняя (L)")
    susp_front_spring_r = models.BooleanField(default=False, verbose_name="Пружина передняя (R)")

    susp_front_ball_lower_l = models.BooleanField(default=False, verbose_name="Шаровая нижняя перед (L)")
    susp_front_ball_lower_r = models.BooleanField(default=False, verbose_name="Шаровая нижняя перед (R)")

    susp_front_ball_upper_l = models.BooleanField(default=False, verbose_name="Шаровая верхняя перед (L)")
    susp_front_ball_upper_r = models.BooleanField(default=False, verbose_name="Шаровая верхняя перед (R)")

    susp_front_bearing_l = models.BooleanField(default=False, verbose_name="Подшипник ступицы перед (L)")
    susp_front_bearing_r = models.BooleanField(default=False, verbose_name="Подшипник ступицы перед (R)")

    # Сайлентблоки ВЕРХНЕГО рычага (перед)
    susp_front_sb_upper_f_l = models.BooleanField(default=False, verbose_name="С/б верх. рыч. передний (L)")
    susp_front_sb_upper_f_r = models.BooleanField(default=False, verbose_name="С/б верх. рыч. передний (R)")

    susp_front_sb_upper_r_l = models.BooleanField(default=False, verbose_name="С/б верх. рыч. задний (L)")
    susp_front_sb_upper_r_r = models.BooleanField(default=False, verbose_name="С/б верх. рыч. задний (R)")

    # Сайлентблоки НИЖНЕГО рычага (перед)
    susp_front_sb_lower_f_l = models.BooleanField(default=False, verbose_name="С/б нижн. рыч. передний (L)")
    susp_front_sb_lower_f_r = models.BooleanField(default=False, verbose_name="С/б нижн. рыч. передний (R)")

    susp_front_sb_lower_r_l = models.BooleanField(default=False, verbose_name="С/б нижн. рыч. задний (L)")
    susp_front_sb_lower_r_r = models.BooleanField(default=False, verbose_name="С/б нижн. рыч. задний (R)")

    # ==================================================
    # 3. ПОДВЕСКА ЗАДНЯЯ
    # ==================================================

    susp_rear_shock_l = models.BooleanField(default=False, verbose_name="Амортизатор задний (L)")
    susp_rear_shock_r = models.BooleanField(default=False, verbose_name="Амортизатор задний (R)")

    susp_rear_mount_l = models.BooleanField(default=False, verbose_name="Опора стойки аморт. зад (L)")
    susp_rear_mount_r = models.BooleanField(default=False, verbose_name="Опора стойки аморт. зад (R)")

    susp_rear_boot_l = models.BooleanField(default=False, verbose_name="Пыльник/отбойник зад (L)")
    susp_rear_boot_r = models.BooleanField(default=False, verbose_name="Пыльник/отбойник зад (R)")

    susp_rear_spring_l = models.BooleanField(default=False, verbose_name="Пружина задняя (L)")
    susp_rear_spring_r = models.BooleanField(default=False, verbose_name="Пружина задняя (R)")

    susp_rear_ball_lower_l = models.BooleanField(default=False, verbose_name="Шаровая нижняя зад (L)")
    susp_rear_ball_lower_r = models.BooleanField(default=False, verbose_name="Шаровая нижняя зад (R)")

    susp_rear_ball_upper_l = models.BooleanField(default=False, verbose_name="Шаровая верхняя зад (L)")
    susp_rear_ball_upper_r = models.BooleanField(default=False, verbose_name="Шаровая верхняя зад (R)")

    susp_rear_bearing_l = models.BooleanField(default=False, verbose_name="Подшипник ступицы зад (L)")
    susp_rear_bearing_r = models.BooleanField(default=False, verbose_name="Подшипник ступицы зад (R)")

    # --- Сайлентблоки ВЕРХНЕГО ПОПЕРЕЧНОГО рычага (Зад) ---
    # Передний/внутренний
    susp_rear_sb_upper_trans_f_l = models.BooleanField(default=False, verbose_name="С/б верх.попереч. перед/внутр (L)")
    susp_rear_sb_upper_trans_f_r = models.BooleanField(default=False, verbose_name="С/б верх.попереч. перед/внутр (R)")
    # Задний/наружный
    susp_rear_sb_upper_trans_r_l = models.BooleanField(default=False, verbose_name="С/б верх.попереч. зад/наруж (L)")
    susp_rear_sb_upper_trans_r_r = models.BooleanField(default=False, verbose_name="С/б верх.попереч. зад/наруж (R)")

    # --- Сайлентблоки НИЖНЕГО ПОПЕРЕЧНОГО рычага (Зад) ---
    # Передний/внутренний
    susp_rear_sb_lower_trans_f_l = models.BooleanField(default=False, verbose_name="С/б нижн.попереч. перед/внутр (L)")
    susp_rear_sb_lower_trans_f_r = models.BooleanField(default=False, verbose_name="С/б нижн.попереч. перед/внутр (R)")
    # Задний/наружный
    susp_rear_sb_lower_trans_r_l = models.BooleanField(default=False, verbose_name="С/б нижн.попереч. зад/наруж (L)")
    susp_rear_sb_lower_trans_r_r = models.BooleanField(default=False, verbose_name="С/б нижн.попереч. зад/наруж (R)")

    # --- Сайлентблоки ВЕРХНЕГО ПРОДОЛЬНОГО рычага (Зад) ---
    susp_rear_sb_upper_long_f_l = models.BooleanField(default=False, verbose_name="С/б верх.продольн. передний (L)")
    susp_rear_sb_upper_long_f_r = models.BooleanField(default=False, verbose_name="С/б верх.продольн. передний (R)")

    susp_rear_sb_upper_long_r_l = models.BooleanField(default=False, verbose_name="С/б верх.продольн. задний (L)")
    susp_rear_sb_upper_long_r_r = models.BooleanField(default=False, verbose_name="С/б верх.продольн. задний (R)")

    # --- Сайлентблоки НИЖНЕГО ПРОДОЛЬНОГО рычага (Зад) ---
    susp_rear_sb_lower_long_f_l = models.BooleanField(default=False, verbose_name="С/б нижн.продольн. передний (L)")
    susp_rear_sb_lower_long_f_r = models.BooleanField(default=False, verbose_name="С/б нижн.продольн. передний (R)")

    susp_rear_sb_lower_long_r_l = models.BooleanField(default=False, verbose_name="С/б нижн.продольн. задний (L)")
    susp_rear_sb_lower_long_r_r = models.BooleanField(default=False, verbose_name="С/б нижн.продольн. задний (R)")

    # ==================================================
    # 4. РУЛЕВОЕ УПРАВЛЕНИЕ И ПРИВОДА (ПЕРЕД)
    # ==================================================

    # Стабилизатор и его компоненты
    susp_front_stabilizer_l = models.BooleanField(default=False, verbose_name="Стабилизатор передний (L)")
    susp_front_stabilizer_r = models.BooleanField(default=False, verbose_name="Стабилизатор передний (R)")

    susp_front_stab_bushing_l = models.BooleanField(default=False, verbose_name="Втулки стабилизатора перед (L)")
    susp_front_stab_bushing_r = models.BooleanField(default=False, verbose_name="Втулки стабилизатора перед (R)")

    # "Солдатик" - это стойка стабилизатора
    susp_front_stab_link_l = models.BooleanField(default=False, verbose_name="Стойка стаб. (Солдатик) перед (L)")
    susp_front_stab_link_r = models.BooleanField(default=False, verbose_name="Стойка стаб. (Солдатик) перед (R)")

    susp_front_stab_link_bushing_l = models.BooleanField(default=False, verbose_name="Втулки стоек стаб. перед (L)")
    susp_front_stab_link_bushing_r = models.BooleanField(default=False, verbose_name="Втулки стоек стаб. перед (R)")

    # Рулевое
    steering_ujoint = models.BooleanField(default=False, verbose_name="Крестовина рул. вала")  # Обычно одна

    steering_rack = models.BooleanField(default=False,
                                        verbose_name="Рулевая рейка")  # Обычно диагностируется целиком, но можно добавить L/R если нужно

    steering_tip_l = models.BooleanField(default=False, verbose_name="Рулевой наконечник (L)")
    steering_tip_r = models.BooleanField(default=False, verbose_name="Рулевой наконечник (R)")

    steering_tie_rod_l = models.BooleanField(default=False, verbose_name="Рулевая тяга (L)")
    steering_tie_rod_r = models.BooleanField(default=False, verbose_name="Рулевая тяга (R)")

    # Гранаты (ШРУС) - Передние
    drive_front_cv_outer_l = models.BooleanField(default=False, verbose_name="Наружный гранат перед (L)")
    drive_front_cv_outer_r = models.BooleanField(default=False, verbose_name="Наружный гранат перед (R)")

    drive_front_cv_inner_l = models.BooleanField(default=False, verbose_name="Внутренний гранат перед (L)")
    drive_front_cv_inner_r = models.BooleanField(default=False, verbose_name="Внутренний гранат перед (R)")

    # Дополнительно из левой колонки
    susp_front_camber_arm_l = models.BooleanField(default=False, verbose_name="Развальный рычаг перед (L)")
    susp_front_camber_arm_r = models.BooleanField(default=False, verbose_name="Развальный рычаг перед (R)")

    brake_front_caliper_l = models.BooleanField(default=False, verbose_name="Суппорт передний (L)")
    brake_front_caliper_r = models.BooleanField(default=False, verbose_name="Суппорт передний (R)")

    # ==================================================
    # 5. ДОПОЛНИТЕЛЬНО (ЗАДНЯЯ ЧАСТЬ)
    # ==================================================

    # Сайлентблоки балки
    susp_rear_beam_bushing_l = models.BooleanField(default=False, verbose_name="Сайлентблок балки (L)")
    susp_rear_beam_bushing_r = models.BooleanField(default=False, verbose_name="Сайлентблок балки (R)")

    # Стабилизатор задний
    susp_rear_stab_bushing_l = models.BooleanField(default=False, verbose_name="Втулки стабилизатора зад (L)")
    susp_rear_stab_bushing_r = models.BooleanField(default=False, verbose_name="Втулки стабилизатора зад (R)")

    susp_rear_stab_link_l = models.BooleanField(default=False, verbose_name="Стойки стабилизатора зад (L)")
    susp_rear_stab_link_r = models.BooleanField(default=False, verbose_name="Стойки стабилизатора зад (R)")

    susp_rear_stab_link_bushing_l = models.BooleanField(default=False, verbose_name="Втулка стоек стаб. зад (L)")
    susp_rear_stab_link_bushing_r = models.BooleanField(default=False, verbose_name="Втулка стоек стаб. зад (R)")

    # Гранаты (ШРУС) - Задние (для 4WD/RWD)
    drive_rear_cv_outer_l = models.BooleanField(default=False, verbose_name="Наружный гранат зад (L)")
    drive_rear_cv_outer_r = models.BooleanField(default=False, verbose_name="Наружный гранат зад (R)")

    drive_rear_cv_inner_l = models.BooleanField(default=False, verbose_name="Внутренний гранат зад (L)")
    drive_rear_cv_inner_r = models.BooleanField(default=False, verbose_name="Внутренний гранат зад (R)")

    # Дополнительно из правой колонки
    susp_rear_camber_arm_l = models.BooleanField(default=False, verbose_name="Развальный рычаг зад (L)")
    susp_rear_camber_arm_r = models.BooleanField(default=False, verbose_name="Развальный рычаг зад (R)")

    # "Солдатик" задний (обычно дублирует стойку стаба, но в листе есть отдельно)
    susp_rear_soldatik_l = models.BooleanField(default=False, verbose_name="Солдатик задний (L)")
    susp_rear_soldatik_r = models.BooleanField(default=False, verbose_name="Солдатик задний (R)")

    brake_rear_caliper_l = models.BooleanField(default=False, verbose_name="Суппорт задний (L)")
    brake_rear_caliper_r = models.BooleanField(default=False, verbose_name="Суппорт задний (R)")

    # ==================================================
    # 6. НАВЕСНОЕ ОБОРУДОВАНИЕ (ОБЩЕЕ)
    # ==================================================

    steering_gur = models.BooleanField(default=False, verbose_name="ГУР (Гидроусилитель)")
    ac_compressor = models.BooleanField(default=False, verbose_name="Кондиционер")
    alternator = models.BooleanField(default=False, verbose_name="Генератор")

    class Meta:
        verbose_name = "Диагностический лист"
        verbose_name_plural = "Диагностические листы"
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"Диагностика {self.vehicle} от {self.date}"

class Contract(models.Model):
    """
    Договор лизинга.
    """

    STATUS_CHOICES = (
        ('active', 'Действует'),
        ('completed', 'Завершен успешно'),
        ('terminated', 'Расторгнут досрочно'),
        ('debt', 'Есть задолженность'),
    )

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.PROTECT,
        related_name='contracts',
        verbose_name="Автомобиль"
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='contracts',
        verbose_name="Клиент",
        limit_choices_to={'is_staff_member': False}
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='managed_contracts',
        verbose_name="Менеджер"
    )

    contract_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        editable=False,
        verbose_name="Номер договора"
    )
    start_date = models.DateField(
        verbose_name="Дата начала"
    )
    end_date=models.DateField(
        verbose_name="Дата конца"
    )
    initial_payment_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Процент первоначального взноса (%)",
        help_text="Введите процент (например 20)"
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Полная стоимость авто"
    )
    initial_payment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Первоначальный взнос",
        blank=True,
        null=True
    )
    monthly_payment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Ежемесячный платеж"
    )
    payment_due_day = models.PositiveSmallIntegerField(
        verbose_name="День оплаты (число месяца)",
        default=1
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="Статус договора"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    @property
    def is_active(self):
        return self.status == 'active'

    class Meta:
        verbose_name = "Договор лизинга"
        verbose_name_plural = "Договоры лизинга"


    def generate_unique_number(self):
        while True:
            date_str = timezone.now().strftime('%d%m%Y')
            random_digits = ''.join(random.choices(string.digits, k=4))
            new_number = f"L-{date_str}-{random_digits}"

            if not Contract.objects.filter(contract_number=new_number).exists():
                return new_number

    def save(self, *args, **kwargs):
        if not self.contract_number:
            self.contract_number = self.generate_unique_number()


        if self.vehicle:
            if self.initial_payment_percent > 0:
                vehicle_price = Decimal(self.vehicle.price)
                percent = Decimal(self.initial_payment_percent)

                calculated_payment = vehicle_price * (percent / 100)

                self.initial_payment = calculated_payment.quantize(Decimal("0.01"))

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Договор №{self.contract_number} ({self.client.username})"

class Inspection(models.Model):
    """
    История осмотров
    """
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='inspections',
        verbose_name="Автомобиль"
    )

    # Кто проводил осмотр
    inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Сотрудник"
    )

    date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата осмотра"
    )

    # Комментарии к состоянию авто
    engine_summary = models.TextField(
        verbose_name="Двигатель",
        blank=True
    )
    body_summary = models.TextField(
        verbose_name="Кузов",
        blank=True
    )
    suspension_summary = models.TextField(
        verbose_name="Подвеска",
        blank=True
    )

    comment = models.TextField(
        verbose_name="Комментарий",
        blank=True
    )

    class Meta:
        verbose_name = "Осмотр"
        verbose_name_plural = "Осмотры"
        ordering = ['-date']

    def __str__(self):
        return f"Осмотр {self.vehicle.vin} от {self.date.strftime('%d.%m.%Y')}"
