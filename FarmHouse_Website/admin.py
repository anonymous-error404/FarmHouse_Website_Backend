import base64

from django.contrib import admin
from django.utils.html import format_html

from FarmHouse_Website.forms import BookingAdminForm
from FarmHouse_Website.models import Bookings

# Register your models here.

@admin.register(Bookings)
class BookingsAdmin(admin.ModelAdmin):

    form = BookingAdminForm
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.IDimage:
            b64 = base64.b64encode(obj.IDimage.file.read())
            return format_html(f'<img src="data:image/jpeg;base64,{b64}",height=100,width=120>')
        return "No image"

    image_preview.short_description = "Image preview"

