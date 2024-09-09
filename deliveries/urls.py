from django.urls import path
from .views import incoming_new, ListIncomingView, UnidentifiedIncomingView

app_name = "deliveries"

urlpatterns = [
    path('new-incoming/', incoming_new, name='new-incoming'),
    path('list-incoming/', ListIncomingView.as_view(), name='list-incoming'),
    path('unidentified/', UnidentifiedIncomingView.as_view(), name='unidentified-incoming'),
]