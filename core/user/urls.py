from django.urls import path
from .views import CustomLoginView, CustomLogoutView, register_staff, register_client

app_name='user'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('create-client/', register_client, name='create_client'),
    path('create-staff/', register_staff, name='create_staff')

]
