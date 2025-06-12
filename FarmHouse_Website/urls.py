from FarmHouse_Website import views
from django.urls import path, include
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'bookings', views.BookingViewSet)


urlpatterns = [
    path('home/', views.Home.as_view(), name='home'),
    path('api/', include(router.urls)),
    path('api/check-availability/', views.check_availability, name='check-availability'),
    path('api/available-dates/', views.available_dates, name='available-dates'),
    path('api/update-payment-status/<int:booking_id>/', views.update_payment_status, name='update-payment-status'),

]
