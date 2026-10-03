from django.conf import settings


class DefaultLanguageMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME) not in dict(settings.LANGUAGES):
            request.META["HTTP_ACCEPT_LANGUAGE"] = settings.LANGUAGE_CODE
        return self.get_response(request)
