from FarmHouse_Website import views
from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'bookings', views.BookingViewSet)
router.register(r'menu', views.MenuViewSet)
urlpatterns = [
    path('NirmalFarms/', views.Home.as_view(), name='home'),
    path('NirmalFarms/api/', include(router.urls)),
    path('NirmalFarms/api/check-availability/', views.check_availability, name='check-availability'),
    path('NirmalFarms/api/update-booking-status/<int:booking_id>/', views.update_booking_status, name='update-booking-status'),

]
