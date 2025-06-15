import base64

from django.contrib import admin
from django.utils.html import format_html

from FarmHouse_Website.forms import *
from FarmHouse_Website.models import *

# Register your models here.

@admin.register(Bookings)
class BookingsAdmin(admin.ModelAdmin):
    form = BookingAdminForm

@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    form = MenuAdminForm
