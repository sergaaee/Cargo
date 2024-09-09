from django.views.generic import RedirectView
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

from Cargo import settings
from Cargo.views import IndexView

urlpatterns = [
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False)),
    path('', include('web.urls')),
    path('index/', IndexView.as_view(), name='index'),
    path('accounts/', include("django.contrib.auth.urls")),
    path('admin/', admin.site.urls),
    path('incomings/', include('deliveries.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
