from django.contrib.auth import views as auth_views
from django.urls import path
from django.utils.translation import gettext_lazy as _
from django.views.i18n import set_language

from .views import (
    ActionLogListView,
    ClientAccountCreateView,
    ClientDebtDetailView,
    ClientDebtListView,
    CustomerCreateView,
    CustomerDeleteView,
    CustomerDetailView,
    CustomerListView,
    CustomerUpdateView,
    DebtCancelView,
    DebtCreateView,
    DebtDetailView,
    DebtListView,
    DebtUpdateView,
    EmployeeCreateView,
    EmployeeDeleteView,
    EmployeeListView,
    HomeView,
    PaymentCreateView,
    PaymentListView,
    UserLoginView,
    UserLogoutView,
    UserRegisterView,
)


urlpatterns = [
    path('language/', set_language, name='set_language'),
    path('customers/<int:pk>/access/', ClientAccountCreateView.as_view(), name='client_account_create'),
    path(
        'password/reset/',
        auth_views.PasswordResetView.as_view(
            template_name='main/form_page.html',
            email_template_name='main/password_reset_email.txt',
            subject_template_name='main/password_reset_subject.txt',
            extra_context={'page_title': _('Reset password'), 'back_url': 'login'},
        ),
        name='password_reset',
    ),
    path(
        'password/reset/sent/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='main/form_page.html',
            extra_context={
                'page_title': _('Check your email'),
                'notice': _('If an account with this email exists, you’ll receive a password reset link.'),
                'back_url': 'login',
            },
        ),
        name='password_reset_done',
    ),
    path(
        'password/reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='main/form_page.html',
            extra_context={'page_title': _('New password'), 'back_url': 'login'},
        ),
        name='password_reset_confirm',
    ),
    path(
        'password/reset/complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='main/form_page.html',
            extra_context={
                'page_title': _('Password changed'),
                'notice': _('You can now log in with your new password.'),
                'back_url': 'login',
            },
        ),
        name='password_reset_complete',
    ),
    path('', HomeView.as_view(), name='home'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('register/', UserRegisterView.as_view(), name='register'),
    path('customers/', CustomerListView.as_view(), name='customer_list'),
    path('customers/add/', CustomerCreateView.as_view(), name='customer_create'),
    path('customers/<int:pk>/', CustomerDetailView.as_view(), name='customer_detail'),
    path('customers/<int:pk>/edit/', CustomerUpdateView.as_view(), name='customer_update'),
    path('customers/<int:pk>/delete/', CustomerDeleteView.as_view(), name='customer_delete'),
    path('debts/', DebtListView.as_view(), name='debt_list'),
    path('debts/add/', DebtCreateView.as_view(), name='debt_create'),
    path('debts/<int:pk>/', DebtDetailView.as_view(), name='debt_detail'),
    path('debts/<int:pk>/edit/', DebtUpdateView.as_view(), name='debt_update'),
    path('debts/<int:pk>/cancel/', DebtCancelView.as_view(), name='debt_cancel'),
    path('payments/', PaymentListView.as_view(), name='payment_list'),
    path('payments/add/', PaymentCreateView.as_view(), name='payment_create'),
    path('employees/', EmployeeListView.as_view(), name='employee_list'),
    path('employees/add/', EmployeeCreateView.as_view(), name='employee_create'),
    path('employees/<int:pk>/delete/', EmployeeDeleteView.as_view(), name='employee_delete'),
    path('actions/', ActionLogListView.as_view(), name='action_list'),
    path('my-debts/', ClientDebtListView.as_view(), name='client_debt_list'),
    path('my-debts/<int:pk>/', ClientDebtDetailView.as_view(), name='client_debt_detail'),
]
