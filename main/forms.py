from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from .models import Customer, Debt, Employee, Payment, Shop, User


class DateFilterForm(forms.Form):
    date = forms.DateField(required=False)


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "phone", "address", "note"]
        labels = {
            "name": _("Name"), "phone": _("Phone"),
            "address": _("Address"), "note": _("Note"),
        }
        widgets = {
            "note": forms.Textarea(attrs={"rows": 3}),
            "phone": forms.TextInput(attrs={"type": "tel"}),
        }


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["debt", "amount"]
        labels = {"debt": _("Debt"), "amount": _("Payment amount")}
        widgets = {"amount": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"})}


class ClientAccountForm(UserCreationForm):
    email = forms.EmailField(label=_("Email address"), required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, customer, **kwargs):
        super().__init__(*args, **kwargs)
        self.customer = customer

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.CLIENT
        if not commit:
            return user

        customer = Customer.objects.select_for_update().get(pk=self.customer.pk)
        if customer.user_id:
            raise forms.ValidationError(_("This customer already has an account."))
        user.save()
        customer.user = user
        customer.save(update_fields=["user"])
        return user


class DebtCreateForm(forms.ModelForm):
    class Meta:
        model = Debt
        fields = ["customer", "amount", "description", "due_date"]
        labels = {
            "customer": _("Customer"),
            "amount": _("Amount"),
            "description": _("Description"),
            "due_date": _("Due date"),
        }
        widgets = {
            "amount": forms.NumberInput(attrs={"step": "0.01", "min": "0.01", "placeholder": "0.00"}),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": _("What is this debt for?")}),
            "due_date": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        }


class DebtUpdateForm(DebtCreateForm):
    class Meta(DebtCreateForm.Meta):
        fields = ["amount", "description", "due_date"]


class OwnerRegisterForm(UserCreationForm):
    shop_name = forms.CharField(label=_("Shop name"), max_length=150)
    email = forms.EmailField(label=_("Email address"), required=True)
    phone = forms.CharField(label=_("Phone"), max_length=30, required=False)
    address = forms.CharField(label=_("Address"), max_length=255, required=False)

    class Meta:
        model = User
        fields = ["username", "email", "shop_name", "phone", "address", "password1", "password2"]

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.OWNER

        if commit:
            user.save()
            Shop.objects.create(
                owner=user,
                name=self.cleaned_data["shop_name"],
                phone=self.cleaned_data["phone"],
                address=self.cleaned_data["address"],
            )

        return user


class CashierCreateForm(UserCreationForm):
    email = forms.EmailField(label=_("Email address"), required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, shop=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.shop = shop

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.CASHIER

        if commit:
            user.save()
            Employee.objects.create(shop=self.shop, user=user)

        return user
