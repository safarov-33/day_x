from django.contrib import admin
from django.urls import path , include

handler403 = "main.error_views.permission_denied"
handler404 = "main.error_views.not_found"
handler500 = "main.error_views.server_error"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('' , include('main.urls'))
]
