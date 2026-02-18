from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'app'

urlpatterns = [
    path('', views.HomeRedirectView.as_view(), name='home'),

    # Для клиентов
    path('vehicle/new/', views.VehicleCreationView.as_view(), name='vehicle_create'),
    path('dashboard/', views.ClientDashboardView.as_view(), name='client_dashboard'),
    path('vehicle/<str:pk>/', views.VehicleDetailView.as_view(), name='vehicle_detail'),
    path('vehicle/<str:pk>/edit/', views.VehicleUpdateView.as_view(), name='vehicle_edit'),
    path('vehicle/<str:pk>/delete/', views.VehicleDeleteView.as_view(), name='vehicle_delete'),
    path('vehicle/<str:pk>/add-photo/', views.AddPhotoView.as_view(), name='add_photo'),
    path('vehicle/<str:pk>/add-doc/', views.AddDocumentView.as_view(), name='add_document'),
    path('vehicle/<str:pk>/create-contract/', views.CreateContractView.as_view(), name='contract_create'),
    path('vehicle/<str:pk>/location/', views.vehicle_location_api, name='vehicle_location_api'),
    path('contract/<int:pk>/edit/', views.ContractUpdateView.as_view(), name='contract_edit'),
    path('contract/<int:pk>/print/', views.ContractPrintView.as_view(), name='contract_print'),
    path('clients/', views.ClientListView.as_view(), name='client_list'),
    path('client/<int:pk>/', views.ClientDetailView.as_view(), name='client_detail'),

    path('vehicle/<str:pk>/diagnostic/new/', views.DiagnosticEditView.as_view(), name='diagnostic_create'),
    path('diagnostic/<int:pk>/pdf/', views.diagnostic_pdf_view, name='diagnostic_pdf'),
    path('compare/', views.compare_vehicles, name='compare'),

    # Для сотрудников
    path('search/', views.StaffSearchView.as_view(), name='staff_search'),
    path('dashboard/staff', views.StaffDashboardView.as_view(), name='staff_dashboard'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)