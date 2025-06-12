from FarmHouse_Website import views
from django.urls import path

urlpatterns = [
    path('home/', views.Home.as_view(), name='home'),

]
