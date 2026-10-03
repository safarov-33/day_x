from django.utils.translation import gettext as _, gettext_noop, override

MESSAGES = [
    gettext_noop("Customer created: %(name)s"),
    gettext_noop("Customer updated: %(name)s"),
    gettext_noop("Customer archive status changed: %(name)s"),
    gettext_noop("Debt created: %(amount)s TJS, customer: %(name)s"),
    gettext_noop("Debt updated: %(id)s"),
    gettext_noop("Debt cancelled: %(id)s"),
    gettext_noop("Payment received: %(amount)s TJS, customer: %(name)s"),
    gettext_noop("Cashier created: %(name)s"),
    gettext_noop("Cashier access changed: %(name)s"),
]
LEGACY_PREFIXES = {
    "Created customer: ": MESSAGES[0], "Создан клиент: ": MESSAGES[0],
    "Updated customer: ": MESSAGES[1], "Изменён клиент: ": MESSAGES[1],
    "Изменён архивный статус клиента: ": MESSAGES[2],
    "Updated debt: ": MESSAGES[4], "Изменён долг: ": MESSAGES[4],
    "Cancelled debt: ": MESSAGES[5], "Отменён долг: ": MESSAGES[5],
    "Created cashier: ": MESSAGES[7], "Создан кассир: ": MESSAGES[7],
    "Disabled cashier: ": MESSAGES[8], "Изменён доступ кассира: ": MESSAGES[8],
}


def render_action(action, details):
    if details and action not in MESSAGES:
        with override("en"):
            action = _(action)
    if details and action in MESSAGES:
        try:
            return _(action) % details
        except (KeyError, TypeError, ValueError):
            return action
    for prefix, message in LEGACY_PREFIXES.items():
        if action.startswith(prefix):
            value = action[len(prefix):]
            return _(message) % {"name": value, "id": value}
    for prefix, separator, message in [
        ("Created debt: ", " TJS for ", MESSAGES[3]),
        ("Создан долг: ", " TJS, клиент: ", MESSAGES[3]),
        ("Accepted payment: ", " TJS from ", MESSAGES[6]),
        ("Принят платёж: ", " TJS, клиент: ", MESSAGES[6]),
    ]:
        if action.startswith(prefix):
            amount, found, name = action[len(prefix):].partition(separator)
            if found:
                return _(message) % {"amount": amount, "name": name}
    return action
