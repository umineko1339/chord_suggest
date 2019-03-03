from django.urls import path
from . import views
from django.conf.urls import url

urlpatterns = [
    path('', views.main_page.as_view(), name='main_page'),
]
