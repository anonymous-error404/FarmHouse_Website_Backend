import base64
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.views import APIView
from FarmHouse_Website.models import *
from FarmHouse_Website.serializer import *


class Home(APIView):
    def get(self, request):
        image_bin = Bookings.objects.get(bookingId=1).IDimage
        image = base64.b64encode(image_bin).decode('utf-8')
        html = f"""
        <html>
        <body>
            <h2>ID Image Preview</h2>
            <img src="data:image/jpeg;base64,{image}" height="100" width="120">
        </body>
        </html>
        """

        return HttpResponse(html, content_type='text/html')

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Bookings.objects.all()
    serializer_class = BookingsSerializer

class MenuViewSet(viewsets.ModelViewSet):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer