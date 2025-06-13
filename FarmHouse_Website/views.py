import base64

from django.http import HttpResponse
from django.shortcuts import render
from django.utils.html import format_html
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from FarmHouse_Website.models import Bookings


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
