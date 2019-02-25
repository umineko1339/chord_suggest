from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_page.as_view(), name='main_page'),
]
