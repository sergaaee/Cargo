
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

from Cargo import settings

urlpatterns = [
    path('', include('web.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include("django.contrib.auth.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
