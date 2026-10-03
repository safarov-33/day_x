from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ActionLog, Customer, Debt, Employee, Payment, Shop, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Role", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Role", {"fields": ("role",)}),)


admin.site.register([Shop, Employee, Customer, Debt, Payment, ActionLog])
