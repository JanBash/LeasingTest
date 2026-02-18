from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template
from django.urls import reverse_lazy, set_urlconf
from django.views.generic import ListView, DetailView, View, UpdateView, DeleteView, CreateView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q, ProtectedError
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import get_user_model

import weasyprint
from django.template.loader import render_to_string

from .models import Vehicle, Contract, Inspection, VehiclePhoto, VehicleDocument, DiagnosticReport
from .forms import VehicleForm, VehicleCreationForm, AddPhotoForm, VehicleDocumentForm, ContractCreationForm, \
    ContractChangeForm, DiagnosticReportForm
from .utils import get_wialon_location, parse_external_url

User = get_user_model()

class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff_member or self.request.user.is_superuser


class VehicleCreationView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Vehicle
    form_class = VehicleCreationForm
    template_name = 'app/vehicle_create.html'

    def get_success_url(self):
        return reverse_lazy('app:vehicle_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        self.object = form.save()

        files = self.request.FILES.getlist('gallery')

        for f in files:

            VehiclePhoto.objects.create(vehicle=self.object, image=f)

        return super().form_valid(form)

    def form_invalid(self, form):
        print("ОШИБКИ: ", form.errors)
        return super().form_invalid(form)


class VehicleUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'app/vehicle_form.html'
    context_object_name = 'vehicle'

    def get_success_url(self):
        return reverse_lazy('app:vehicle_detail', kwargs={'pk': self.object.pk})


class VehicleDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = Vehicle
    template_name = 'app/vehicle_confirm_delete.html'
    context_object_name = 'vehicle'

    success_url = reverse_lazy('app:staff_search')

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError:
            messages.error(
                request,
                "⛔ Ошибка: Нельзя удалить этот автомобиль, так как к нему привязан Договор. Сначала удалите договор или отвяжите машину."
            )
            return redirect('app:vehicle_detail', pk=self.get_object().pk)


class AddDocumentView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = VehicleDocument
    form_class = VehicleDocumentForm
    template_name = 'app/add_document.html'

    def form_valid(self, form):
        vehicle = get_object_or_404(Vehicle, pk=self.kwargs['pk'])
        form.instance.vehicle = vehicle
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('app:vehicle_detail', kwargs={'pk': self.kwargs['pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicle'] = get_object_or_404(Vehicle, pk=self.kwargs['pk'])
        return context


class AddPhotoView(LoginRequiredMixin, StaffRequiredMixin, FormView):
    template_name = 'app/add_photo.html'
    form_class = AddPhotoForm

    def form_valid(self, form):
        vehicle = get_object_or_404(Vehicle, pk=self.kwargs['pk'])
        files = form.cleaned_data['gallery']

        for f in files:
            VehiclePhoto.objects.create(vehicle=vehicle, image=f)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('app:vehicle_detail', kwargs={'pk': self.kwargs['pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicle'] = get_object_or_404(Vehicle, pk=self.kwargs['pk'])
        return context


class HomeRedirectView(LoginRequiredMixin, View):
    """
    Распределительная страница.
    Если зашел сотрудник -> в админку (или рабочий дашборд).
    Если зашел клиент -> в личный кабинет.
    """
    def get(self, request):
        if request.user.is_staff_member or request.user.is_superuser:
            return redirect('app:staff_dashboard')
        else:
            return redirect('app:client_dashboard')

class ClientDashboardView(LoginRequiredMixin, ListView):
    model = Contract
    template_name = 'app/client_dashboard.html'
    context_object_name = 'contracts'

    def get_queryset(self):
        return Contract.objects.filter(client=self.request.user).select_related('vehicle')

class VehicleDetailView(LoginRequiredMixin, DetailView):
    model = Vehicle
    template_name = 'app/vehicle_detail.html'
    context_object_name = 'vehicle'

    def get_object(self):
        vehicle = super().get_object()

        # Разрешаем доступ, если это сотрудник ИЛИ суперпользователь
        is_manager = self.request.user.is_staff_member or self.request.user.is_superuser

        # Если это НЕ менеджер и НЕ админ, то включаем проверку на владельца
        if not is_manager:
            has_contract = Contract.objects.filter(
                vehicle=vehicle,
                client=self.request.user
            ).exists()

            if not has_contract:
                raise PermissionDenied("У вас нет доступа к этому автомобилю")

        return vehicle

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['inspections'] = self.object.inspections.all().order_by('-date')
        context['latest_diagnostic'] = self.object.diagnostic_reports.order_by('-created_at').first()

        return context


class StaffDashboardView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = Vehicle
    template_name = 'app/staff_home.html'
    context_object_name = 'vehicles'
    paginate_by = 20

    def get_queryset(self):
        queryset = Vehicle.objects.all().order_by('-created_at')

        filter_type = self.request.GET.get('filter')

        if filter_type == 'free':
            queryset = queryset.exclude(contracts__status='active').filter(overall_status='ok')
        elif filter_type == 'rented':
            queryset = queryset.filter(contracts__status='active').distinct()
        elif filter_type == 'repair':
            queryset = queryset.exclude(overall_status='ok')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        all_vehicles = Vehicle.objects.all()

        context['total_vehicles'] = all_vehicles.count()
        context['free_vehicles'] = all_vehicles.exclude(contracts__status='active').filter(overall_status='ok').count()
        context['repair_needed'] = all_vehicles.exclude(overall_status='ok').count()
        context['active_contracts'] = Contract.objects.filter(status='active').count()
        context['current_filter'] = self.request.GET.get('filter', 'all')

        return context


class StaffSearchView(LoginRequiredMixin, ListView):
    model = Vehicle
    template_name = 'app/staff_search.html'
    context_object_name = 'vehicles'

    def get_queryset(self):
        if not self.request.user.is_staff_member and not self.request.user.is_superuser:
            raise PermissionDenied

        query = self.request.GET.get('q')

        queryset = Vehicle.objects.all()
        if self.request.GET.get('only_available'):
            queryset = queryset.filter(contracts__isnull=True)

        if query:
            query = query.strip()
            return queryset.filter(
                Q(vin__icontains=query) |
                Q(license_plate__icontains=query) |
                Q(brand__icontains=query) |
                Q(full_name_of_contractor__icontains=query)
            ).distinct()

        if self.request.GET.get('only_available'):
            return queryset


        return Vehicle.objects.none()


class CreateContractView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Contract
    form_class = ContractCreationForm
    template_name = 'app/contract_create.html'

    def dispatch(self, request, *args, **kwargs):
        self.vehicle = get_object_or_404(Vehicle, pk=self.kwargs.get('pk'))

        if self.vehicle.contracts.filter(status='active').exists():
            messages.error(request, f'Автомобиль {self.vehicle.license_plate} уже находится в аренде')
            return redirect('app:vehicle_detail', pk=self.vehicle.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        """
        Автоматически подставляем цену машины в поле total_amount
        """
        initial = super().get_initial()

        initial['total_amount'] = self.vehicle.price

        initial['initial_payment_percent'] = 0
        return initial

    def form_valid(self, form):
        contract = form.save(commit=False)
        contract.vehicle = self.vehicle
        contract.manager = self.request.user

        contract.save()

        messages.success(self.request, f"Договор №{contract.contract_number} успешно создан")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicle'] = self.vehicle
        return context

    def get_success_url(self):
        return reverse_lazy('app:vehicle_detail', kwargs={'pk': self.vehicle.pk})


class ContractUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = Contract
    form_class = ContractChangeForm # Теперь эта форма содержит все нужные поля
    template_name = 'app/contract_edit.html'
    context_object_name = 'contract'

    def get_success_url(self):
        # Перенаправляем на детальную страницу машины после сохранения
        return reverse_lazy('app:vehicle_detail', kwargs={'pk': self.object.vehicle.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicle'] = self.object.vehicle
        return context


def vehicle_location_api(request, pk):
    if not request.user.is_staff_member and not request.user.is_superuser:
        return JsonResponse({'error': 'Forbidden'}, status=403)
    
    vehicle = get_object_or_404(Vehicle, pk=pk)

    if not vehicle.wialon_id:
        return JsonResponse({'error': 'No Wialon ID set'}, status=404)
    
    location = get_wialon_location(vehicle.wialon_id)

    if location:
        return JsonResponse(location)
    else:
        return JsonResponse({'error': 'Could not fetch location'}, status=503)


class ContractPrintView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    model = Contract
    template_name = 'app/contract_print.html'
    context_object_name = 'contract'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['vehicle'] = self.object.vehicle
        return context



class ClientListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = User
    template_name = 'app/client_list.html'
    context_object_name = 'clients'
    paginate_by = 20

    def get_queryset(self):
        queryset = User.objects.filter(is_staff_member=False).select_related('client_profile')

        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(username__icontains=query) |
                Q(email__icontains=query) |
                Q(phone__icontains=query) |
                Q(client_profile__fullname__icontains=query) |
                Q(client_profile__passport_number__icontains=query)
            ).distinct()

        return queryset.order_by('-date_joined')


class ClientDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    model = User
    template_name = 'app/client_detail.html'
    context_object_name = 'client_user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if hasattr(self.object, 'client_profile'):
            context['profile'] = self.object.client_profile
        else:
            context['profile'] = None

        context['contracts'] = Contract.objects.filter(client=self.object).order_by('-created_at')

        return context


class DiagnosticEditView(LoginRequiredMixin, CreateView):
    model = DiagnosticReport
    form_class = DiagnosticReportForm
    template_name = 'app/diagnostic_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.vehicle = get_object_or_404(Vehicle, pk=self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicle'] = self.vehicle
        return context

    def form_valid(self, form):
        form.instance.vehicle = self.vehicle
        form.instance.mechanic = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('app:vehicle_detail', kwargs={'pk': self.vehicle.pk})


def diagnostic_pdf_view(request, pk):
    report = get_object_or_404(DiagnosticReport, pk=pk)

    # Контекст для шаблона
    context = {
        'report': report,
        'vehicle': report.vehicle,
        # WeasyPrint сам найдет статику, если правильно настроен settings.STATIC_ROOT
        # Но для надежности можно передать базовый URL
        'base_url': request.build_absolute_uri('/')
    }

    # 1. Рендерим HTML в строку
    html_string = render_to_string('app/diagnostic_pdf.html', context)

    # 2. Генерируем PDF
    # base_url нужен, чтобы он нашел картинки и стили
    pdf_file = weasyprint.HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()

    # 3. Отдаем файл
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="diagnostica_{report.vehicle.license_plate}.pdf"'

    return response

def compare_vehicles(request):
    my_vehicles = Vehicle.objects.all()

    context = {
        'my_vehicles': my_vehicles,
        'comparison_data': []
    }

    if request.method == 'POST':
        selected_vehicle_id = request.POST.get('vehicle_id')
        urls = request.POST.getlist('urls')

        print(f"DEBUG: Selected ID: {selected_vehicle_id}")  # <-- СМОТРИ В КОНСОЛЬ

        # 1. Добавляем НАШЕ авто
        if selected_vehicle_id:
            try:
                my_car = Vehicle.objects.get(pk=selected_vehicle_id)

                # Безопасное получение картинки
                image_url = my_car.get_cover_image() if hasattr(my_car, 'get_cover_image') else None

                print(f"DEBUG: Found car: {my_car.brand}, Image: {image_url}")  # <-- СМОТРИ В КОНСОЛЬ

                context['comparison_data'].append({
                    'is_mine': True,
                    'source': 'Наш парк',
                    'title': f"{my_car.brand} {my_car.model_name}",
                    'image': image_url,
                    'price': f"{my_car.price} $",  # Убедитесь, что поле price заполнено в админке
                    'year': my_car.year,
                    'mileage': f"{my_car.mileage} км",
                    'engine': f"{my_car.engine_volume} л / {my_car.get_engine_type_display()}",
                    'transmission': my_car.get_transmission_display(),
                    'url': '#'
                })
            except Vehicle.DoesNotExist:
                print("DEBUG: Car does not exist")
            except Exception as e:
                print(f"DEBUG: Error adding my car: {e}")

        # 2. Парсим ссылки
        for url in urls:
            if url.strip():
                print(f"DEBUG: Parsing {url}")
                external_data = parse_external_url(url.strip())
                if external_data:
                    external_data['is_mine'] = False
                    context['comparison_data'].append(external_data)
                else:
                    context['error'] = f"Ошибка чтения: {url}"

    return render(request, 'app/compare.html', context)

