from django.shortcuts import render
from django.utils.translation import gettext as _


def permission_denied(request, exception=None):
    return render(request, "main/error.html", {"page_title": _("Access denied"),
                  "explanation": _("Your account does not have access to this page.")}, status=403)


def not_found(request, exception=None):
    return render(request, "main/error.html", {"page_title": _("Page not found"),
                  "explanation": _("Check the address or return to the home page.")}, status=404)


def server_error(request):
    return render(request, "main/error.html", {"page_title": _("Unable to open this page"),
                  "explanation": _("Please try again later.")}, status=500)


def csrf_failure(request, reason=""):
    return render(request, "main/error.html", {"page_title": _("Refresh the page"),
                  "explanation": _("This form session has expired. Refresh the page and submit it again.")}, status=403)
