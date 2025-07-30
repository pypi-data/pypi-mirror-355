from django.urls import path
from .views import NotifyView

urlpatterns = [
    path('/', NotifyView.as_view(), name='notify'),
]