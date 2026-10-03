from decimal import Decimal

from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import OperationalError, transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import (
    CreateView, DeleteView, DetailView, FormView, ListView, TemplateView, UpdateView,
)

from .forms import (
    CashierCreateForm,
    ClientAccountForm,
    CustomerForm,
    DateFilterForm,
    DebtCreateForm,
    DebtUpdateForm,
    OwnerRegisterForm,
    PaymentForm,
)
from .models import ActionLog, Customer, Debt, Employee, Payment, User
from .utils import get_user_shop


class ShopAccessMixin(LoginRequiredMixin):
    allowed_roles = (User.Role.OWNER, User.Role.CASHIER)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if request.user.role not in self.allowed_roles:
            raise PermissionDenied

        self.shop = get_user_shop(request.user)

        if not self.shop:
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def log_action(self, action, details=None):
        ActionLog.objects.create(
            shop=self.shop,
            user=self.request.user,
            action=action,
            details=details or {},
        )


class OwnerAccessMixin(ShopAccessMixin):
    allowed_roles = (User.Role.OWNER,)


class ClientAccessMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if request.user.role != User.Role.CLIENT:
            raise PermissionDenied

        self.customer = getattr(request.user, "customer", None)

        if not self.customer:
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)


class HomeView(TemplateView):
    template_name = "main/home.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == User.Role.CLIENT:
            return redirect("client_debt_list")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if not self.request.user.is_authenticated:
            return context

        shop = get_user_shop(self.request.user)
        context["shop"] = shop
        context["customer_count"] = 0
        context["active_debt_count"] = 0
        context["total_debt"] = Decimal("0.00")
        context["total_paid"] = Decimal("0.00")
        context["remaining_debt"] = Decimal("0.00")
        context["payment_percent"] = Decimal("0.0")
        context["recent_actions"] = []

        if not shop:
            return context

        debts = Debt.objects.filter(customer__shop=shop).exclude(status=Debt.Status.CANCELLED)
        total_debt = debts.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        payments = Payment.objects.filter(debt__in=debts)
        total_paid = payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        context["customer_count"] = shop.customers.filter(is_archived=False).count()
        context["active_debt_count"] = debts.filter(status__in=[Debt.Status.UNPAID, Debt.Status.PARTIAL]).count()
        context["total_debt"] = total_debt
        context["total_paid"] = total_paid
        context["remaining_debt"] = total_debt - total_paid
        if total_debt:
            context["payment_percent"] = round(total_paid * 100 / total_debt, 1)
        context["recent_actions"] = ActionLog.objects.filter(shop=shop).select_related("user")[:10]

        return context


class UserLoginView(LoginView):
    template_name = "main/login.html"
    redirect_authenticated_user = True
    next_page = reverse_lazy("home")

    def get_success_url(self):
        next_url = self.get_redirect_url()
        if next_url:
            return next_url
        if self.request.user.role == User.Role.CLIENT:
            return reverse("client_debt_list")

        return super().get_success_url()


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("home")


class UserRegisterView(CreateView):
    form_class = OwnerRegisterForm
    template_name = "main/form_page.html"
    extra_context = {"page_title": _("Register your shop"), "back_url": "home", "submit_label": _("Sign up")}
    success_url = reverse_lazy("home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


class CustomerListView(ShopAccessMixin, ListView):
    model = Customer
    template_name = "main/customer_list.html"
    context_object_name = "customers"
    paginate_by = 20

    def get_queryset(self):
        show_archived = self.request.GET.get("archived") == "1"
        queryset = Customer.objects.filter(
            shop=self.shop, is_archived=show_archived
        ).select_related("user")
        search = self.request.GET.get("q")

        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(phone__icontains=search))

        return queryset.order_by("-created_at")


class CustomerCreateView(ShopAccessMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = "main/form_page.html"
    extra_context = {"page_title": _("Customer"), "back_url": "customer_list"}
    success_url = reverse_lazy("customer_list")

    def form_valid(self, form):
        form.instance.shop = self.shop
        response = super().form_valid(form)
        self.log_action("Customer created: %(name)s", {"name": self.object.name})
        return response


class CustomerDetailView(ShopAccessMixin, DetailView):
    model = Customer
    template_name = "main/customer_detail.html"
    context_object_name = "customer"

    def get_queryset(self):
        return Customer.objects.filter(shop=self.shop).prefetch_related("debts__payments")


class CustomerUpdateView(ShopAccessMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = "main/form_page.html"
    extra_context = {"page_title": _("Customer"), "back_url": "customer_list"}

    def get_queryset(self):
        return Customer.objects.filter(shop=self.shop)

    def form_valid(self, form):
        response = super().form_valid(form)
        self.log_action("Customer updated: %(name)s", {"name": self.object.name})
        return response

    def get_success_url(self):
        return reverse("customer_detail", kwargs={"pk": self.object.pk})


class CustomerDeleteView(OwnerAccessMixin, DeleteView):
    model = Customer
    template_name = "main/confirm_delete.html"
    success_url = reverse_lazy("customer_list")

    def get_queryset(self):
        return Customer.objects.filter(shop=self.shop)

    def form_valid(self, form):
        self.object.is_archived = not self.object.is_archived
        self.object.save(update_fields=["is_archived"])
        self.log_action("Customer archive status changed: %(name)s", {"name": self.object.name})
        return redirect(self.success_url)


class DebtListView(ShopAccessMixin, ListView):
    model = Debt
    template_name = "main/debt_list.html"
    context_object_name = "debts"
    paginate_by = 20

    def get_queryset(self):
        queryset = Debt.objects.filter(customer__shop=self.shop)
        queryset = queryset.select_related("customer", "created_by").order_by("-created_at")
        search = self.request.GET.get("q", "").strip()
        if search:
            queryset = queryset.filter(customer__name__icontains=search)
        status = self.request.GET.get("status")
        if status == "overdue":
            queryset = queryset.filter(
                due_date__lt=timezone.localdate(),
                status__in=[Debt.Status.UNPAID, Debt.Status.PARTIAL],
            )
        elif status == "active":
            queryset = queryset.filter(status__in=[Debt.Status.UNPAID, Debt.Status.PARTIAL])
        elif status in Debt.Status.values:
            queryset = queryset.filter(status=status)
        for parameter, lookup in (("from", "due_date__gte"), ("to", "due_date__lte")):
            date_form = DateFilterForm({"date": self.request.GET.get(parameter)})
            if date_form.is_valid() and date_form.cleaned_data["date"]:
                queryset = queryset.filter(**{lookup: date_form.cleaned_data["date"]})
        return queryset


class DebtCreateView(ShopAccessMixin, CreateView):
    model = Debt
    form_class = DebtCreateForm
    template_name = "main/form_page.html"
    extra_context = {"page_title": _("Debt"), "back_url": "debt_list"}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["customer"].queryset = Customer.objects.filter(shop=self.shop, is_archived=False)
        return form

    def get_initial(self):
        initial = super().get_initial()
        customer_id = self.request.GET.get("customer")

        if customer_id and customer_id.isdecimal():
            customers = Customer.objects.filter(shop=self.shop, is_archived=False)
            if customers.filter(pk=customer_id).exists():
                initial["customer"] = customer_id

        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        self.log_action(
            "Debt created: %(amount)s TJS, customer: %(name)s",
            {"amount": str(self.object.amount), "name": self.object.customer.name},
        )
        return response

    def get_success_url(self):
        return reverse("debt_detail", kwargs={"pk": self.object.pk})


class DebtDetailView(ShopAccessMixin, DetailView):
    model = Debt
    template_name = "main/debt_detail.html"
    context_object_name = "debt"

    def get_queryset(self):
        return Debt.objects.filter(customer__shop=self.shop).select_related(
            "customer", "created_by"
        ).prefetch_related("payments")


class DebtUpdateView(ShopAccessMixin, UpdateView):
    model = Debt
    form_class = DebtUpdateForm
    template_name = "main/form_page.html"
    extra_context = {"page_title": _("Debt"), "back_url": "debt_list"}

    def get_queryset(self):
        return Debt.objects.filter(customer__shop=self.shop).exclude(status=Debt.Status.CANCELLED)

    def form_valid(self, form):
        response = super().form_valid(form)
        self.log_action("Debt updated: %(id)s", {"id": self.object.pk})
        return response

    def get_success_url(self):
        return reverse("debt_detail", kwargs={"pk": self.object.pk})


class DebtCancelView(ShopAccessMixin, View):
    def post(self, request, pk):
        debt = get_object_or_404(Debt, pk=pk, customer__shop=self.shop)

        if debt.status == Debt.Status.CANCELLED or debt.payments.exists():
            return render(request, "main/error.html", {
                "page_title": _("Debt"),
                "explanation": _("This debt cannot be cancelled."),
            }, status=400)

        debt.status = Debt.Status.CANCELLED
        debt.save()
        self.log_action("Debt cancelled: %(id)s", {"id": debt.pk})
        return redirect("debt_detail", pk=debt.pk)


class PaymentListView(ShopAccessMixin, ListView):
    model = Payment
    template_name = "main/payment_list.html"
    context_object_name = "payments"
    paginate_by = 20

    def get_queryset(self):
        queryset = Payment.objects.filter(debt__customer__shop=self.shop)
        queryset = queryset.select_related("debt__customer", "accepted_by").order_by("-created_at")
        search = self.request.GET.get("q", "").strip()
        if search:
            queryset = queryset.filter(debt__customer__name__icontains=search)
        return queryset


class PaymentCreateView(ShopAccessMixin, CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = "main/form_page.html"
    extra_context = {"page_title": _("Accept payment"), "back_url": "payment_list", "payment_form": True}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["debt"].queryset = Debt.objects.filter(customer__shop=self.shop).exclude(
            status__in=[Debt.Status.PAID, Debt.Status.CANCELLED]
        )
        return form

    def get_initial(self):
        initial = super().get_initial()
        debt_id = self.request.GET.get("debt")

        if debt_id and debt_id.isdecimal():
            debts = Debt.objects.filter(customer__shop=self.shop).exclude(
                status__in=[Debt.Status.PAID, Debt.Status.CANCELLED]
            )
            if debts.filter(pk=debt_id).exists():
                initial["debt"] = debt_id

        return initial

    def form_valid(self, form):
        form.instance.accepted_by = self.request.user
        try:
            with transaction.atomic():
                response = super().form_valid(form)
                self.log_action(
                    "Payment received: %(amount)s TJS, customer: %(name)s",
                    {"amount": str(self.object.amount), "name": self.object.debt.customer.name},
                )
            return response
        except ValidationError as exc:
            form.add_error(None, exc)
        except OperationalError:
            form.add_error(None, _("The payment was not saved because the database is busy. Refresh the balance and try again."))
        return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        balances = {}
        for debt in context["form"].fields["debt"].queryset:
            balances[str(debt.pk)] = str(debt.remaining_amount)
        context["debt_balances"] = balances
        return context

    def get_success_url(self):
        return reverse("debt_detail", kwargs={"pk": self.object.debt_id})


class EmployeeListView(OwnerAccessMixin, ListView):
    model = Employee
    template_name = "main/employee_list.html"
    context_object_name = "employees"

    def get_queryset(self):
        queryset = Employee.objects.filter(shop=self.shop).select_related("user")
        search = self.request.GET.get("q", "").strip()
        if search:
            queryset = queryset.filter(user__username__icontains=search)
        return queryset


class EmployeeCreateView(OwnerAccessMixin, FormView):
    form_class = CashierCreateForm
    template_name = "main/form_page.html"
    extra_context = {"page_title": _("New staff member"), "back_url": "employee_list"}
    success_url = reverse_lazy("employee_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["shop"] = self.shop
        return kwargs

    def form_valid(self, form):
        user = form.save()
        self.log_action("Cashier created: %(name)s", {"name": user.username})
        return super().form_valid(form)


class EmployeeDeleteView(OwnerAccessMixin, View):
    def post(self, request, pk):
        employee = get_object_or_404(Employee, pk=pk, shop=self.shop)
        employee.is_active = not employee.is_active
        employee.save(update_fields=["is_active"])
        self.log_action("Cashier access changed: %(name)s", {"name": employee.user.username})
        return redirect("employee_list")


class ActionLogListView(OwnerAccessMixin, ListView):
    model = ActionLog
    template_name = "main/action_log_list.html"
    context_object_name = "actions"
    paginate_by = 30

    def get_queryset(self):
        return ActionLog.objects.filter(shop=self.shop).select_related("user")


class ClientDebtListView(ClientAccessMixin, ListView):
    model = Debt
    template_name = "main/debt_list.html"
    context_object_name = "debts"
    paginate_by = 20

    def get_queryset(self):
        return Debt.objects.filter(customer=self.customer).select_related(
            "customer", "created_by"
        ).prefetch_related("payments").order_by("-created_at")


class ClientDebtDetailView(ClientAccessMixin, DetailView):
    model = Debt
    template_name = "main/debt_detail.html"
    context_object_name = "debt"

    def get_queryset(self):
        return Debt.objects.filter(customer=self.customer).select_related(
            "customer", "created_by"
        ).prefetch_related("payments")


class ClientAccountCreateView(OwnerAccessMixin, FormView):
    form_class = ClientAccountForm
    template_name = "main/form_page.html"
    extra_context = {"page_title": _("Customer access"), "back_url": "customer_list"}
    success_url = reverse_lazy("customer_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["customer"] = get_object_or_404(
            Customer, pk=self.kwargs["pk"], shop=self.shop, user__isnull=True
        )
        return kwargs

    def form_valid(self, form):
        try:
            form.save()
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return super().form_valid(form)
