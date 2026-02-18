from django import forms
from .models import Vehicle, VehicleDocument, Contract, DiagnosticReport


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def value_from_datadict(self, data, files, name):
        # Если пришли файлы, берем их списком
        if hasattr(files, 'getlist'):
            return files.getlist(name)
        # Иначе ведем себя как обычно
        return files.get(name)

class MultipleFileField(forms.FileField):
    def to_python(self, data):
        # Стандартное поле пытается сделать из data один файл.
        # Мы просто возвращаем данные как есть (список файлов).
        return data

    def clean(self, data, initial=None):
        # Если поле обязательное, но данных нет — ругаемся
        if self.required and not data:
            raise forms.ValidationError("Обязательно выберите файлы")
        return data

class VehicleCreationForm(forms.ModelForm):
    gallery = MultipleFileField(
        widget=MultipleFileInput(attrs={'class': 'form-control'}),
        label="Галерея (можно выбрать много фото)",
        required=False
    )

    class Meta:
        model = Vehicle
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != 'gallery':
                continue

            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'


class AddPhotoForm(forms.Form):
    # Используем наше кастомное поле для загрузки пачки файлов
    gallery = MultipleFileField(
        widget=MultipleFileInput(attrs={'class': 'form-control'}),
        label="Выберите фотографии",
        required=True
    )


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = '__all__'

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            for field_name, field in self.fields.items():
                if isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs['class'] = 'form-check-input'
                else:
                    field.widget.attrs['class'] = 'form-control'


class VehicleDocumentForm(forms.ModelForm):
    class Meta:
        model = VehicleDocument
        fields = ['title', 'file']

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['title'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Акт осмотра'})
            self.fields['file'].widget.attrs.update({'class': 'form-control'})


class DiagnosticReportForm(forms.ModelForm):
    class Meta:
        model = DiagnosticReport
        exclude = ['vehicle', 'date', 'mechanic']


class ContractCreationForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = [
            'client',
            'start_date',
            'end_date',
            'total_amount',
            'initial_payment_percent',
            'initial_payment',
            'monthly_payment',
            'payment_due_day'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

            if name == 'initial_payment':
                field.widget.attrs['placeholder'] = 'Высчитается автоматически'


class ContractChangeForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = [
            'status',
            'client',
            'start_date',
            'end_date',
            'total_amount',
            'initial_payment_percent',  # <-- Добавлено
            'initial_payment',  # <-- Добавлено
            'monthly_payment',
            'payment_due_day'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Проходимся по всем полям и добавляем класс form-control
        for field_name, field in self.fields.items():
            # Для статуса нужен form-select, для остальных form-control
            if field_name == 'status':
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'
