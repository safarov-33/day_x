from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Sum
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    class Role(models.TextChoices):
        OWNER = "owner", _("Owner")
        CASHIER = "cashier", _("Cashier")
        CLIENT = "client", _("Customer")

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.OWNER)


class Shop(models.Model):
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shop")
    name = models.CharField(max_length=150)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField( max_length=50)

    def __str__(self):
        return self.name


class Employee(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="employees")
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="employee")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username


class Customer(models.Model):
    is_archived = models.BooleanField(default=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="customers")
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="customer")
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30)
    address = models.CharField(max_length=255, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_debt(self):
        result = self.debts.exclude(status=Debt.Status.CANCELLED).aggregate(total=Sum("amount"))

        return result["total"] or Decimal("0.00")

    @property
    def total_paid(self):
        result = self.debts.exclude(status=Debt.Status.CANCELLED).aggregate(total=Sum("payments__amount"))

        return result["total"] or Decimal("0.00")

    @property
    def remaining_debt(self):
        return self.total_debt - self.total_paid

    def __str__(self):
        return self.name


class Debt(models.Model):
    class Status(models.TextChoices):
        UNPAID = "unpaid", _("Unpaid")
        PARTIAL = "partial", _("Partially paid")
        PAID = "paid", _("Paid")
        CANCELLED = "cancelled", _("Cancelled")

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="debts")
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_debts")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.UNPAID)

    @property
    def paid_amount(self):
        result = self.payments.aggregate(total=Sum("amount"))
        return result["total"] or Decimal("0.00")

    @property
    def remaining_amount(self):
        if self.status == self.Status.CANCELLED:
            return Decimal("0.00")
        return max(self.amount - self.paid_amount, Decimal("0.00"))

    @property
    def is_overdue(self):
        if not self.due_date:
            return False
        if self.status not in (self.Status.UNPAID, self.Status.PARTIAL):
            return False
        return self.due_date < timezone.localdate()

    def clean(self):
        if self.pk and self.amount is not None and self.amount < self.paid_amount:
            raise ValidationError({
                "amount": _("The debt amount cannot be less than the payments already received.")
            })

        if self.status == self.Status.CANCELLED and self.pk and self.payments.exists():
            raise ValidationError({"status": _("A debt with payments cannot be cancelled.")})

    def refresh_status(self):
        if self.status == self.Status.CANCELLED:
            return

        paid = self.paid_amount

        if paid == 0:
            new_status = self.Status.UNPAID
        elif paid < self.amount:
            new_status = self.Status.PARTIAL
        else:
            new_status = self.Status.PAID

        if self.status != new_status:
            Debt.objects.filter(pk=self.pk).update(status=new_status)
            self.status = new_status

    @transaction.atomic
    def save(self, *args, **kwargs):
        if self.pk:
            Debt.objects.filter(pk=self.pk).update(id=self.pk)
        self.full_clean()
        super().save(*args, **kwargs)
        self.refresh_status()

    def __str__(self):
        return f"{self.customer.name} — {self.amount} TJS"


class Payment(models.Model):
    debt = models.ForeignKey(Debt, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    accepted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="accepted_payments")
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if not self.debt_id:
            return

        if self.debt.status == Debt.Status.CANCELLED:
            raise ValidationError(_("Payments cannot be accepted for a cancelled debt."))

        payments = self.debt.payments.all()

        if self.pk:
            payments = payments.exclude(pk=self.pk)

        already_paid = payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        remaining = self.debt.amount - already_paid

        if self.amount and self.amount > remaining:
            raise ValidationError({"amount": _("The payment cannot exceed the outstanding balance.")})

    @transaction.atomic
    def save(self, *args, **kwargs):
        Debt.objects.filter(pk=self.debt_id).update(id=self.debt_id)
        self.debt = Debt.objects.get(pk=self.debt_id)
        old_debt_id = None

        if self.pk:
            old_debt_id = Payment.objects.filter(pk=self.pk).values_list("debt_id", flat=True).first()

        self.full_clean()
        super().save(*args, **kwargs)
        self.debt.refresh_status()

        if old_debt_id and old_debt_id != self.debt_id:
            Debt.objects.get(pk=old_debt_id).refresh_status()

    def __str__(self):
        return f"{self.amount} TJS — {self.debt.customer.name}"


@receiver(post_delete, sender=Payment)
def refresh_deleted_payment_debt(sender, instance, **kwargs):
    debt = Debt.objects.filter(pk=instance.debt_id).first()
    if debt:
        debt.refresh_status()

class ActionLog(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="actions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="actions")
    action = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def display_action(self):
        from .activity import render_action

        return render_action(self.action, self.details)

    def __str__(self):
        return str(self.display_action)
