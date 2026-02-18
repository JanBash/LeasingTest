from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy

from .forms import UserLoginForm, ClientSignUpForm, StaffSignUpForm
from django.contrib import messages



def is_staff_check(user):
    return user.is_staff_member or user.is_superuser

def is_superuser_check(user):
    return user.is_superuser


@login_required
@user_passes_test(is_staff_check)
def register_client(request):
    if request.method == 'POST':
        form = ClientSignUpForm(request.POST, request.FILES)

        if form.is_valid():
            user = form.save()
            messages.success(request, f'Клиент {user.username} успешно создан!')
            return redirect('app:staff_search')
        else:
            messages.error(request, 'Ошибка при создании клиента. Проверьте форму.')
    else:
        form = ClientSignUpForm()

    return render(request, 'user/register_client.html', {'form': form})


@login_required
@user_passes_test(is_superuser_check)
def register_staff(request):
    if request.method == 'POST':
        form = StaffSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Новый сотрудник добавлен')
            return redirect('app:staff_search')
        else:
            print("ОШИБКА:", form.errors)
    else:
        form = StaffSignUpForm()

    return render(request, 'user/register_staff.html', {'form': form})


class CustomLoginView(LoginView):
    template_name = 'user/login.html'
    authentication_form = UserLoginForm

    redirect_authenticated_user = True

    def get_success_url(self):

        return reverse_lazy('app:home')


class CustomLogoutView(LogoutView):
    next_page = 'user:login'
