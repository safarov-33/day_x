from .models import User


def get_user_shop(user):
    if not user.is_authenticated:
        return None

    if user.role == User.Role.OWNER:
        return getattr(user, "shop", None)

    if user.role == User.Role.CASHIER:
        employee = getattr(user, "employee", None)

        if employee and employee.is_active:
            return employee.shop

    return None
