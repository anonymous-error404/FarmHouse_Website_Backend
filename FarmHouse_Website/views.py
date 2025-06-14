import base64

from django.http import HttpResponse
from django.shortcuts import render
from django.utils.html import format_html
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from FarmHouse_Website.models import Bookings
from FarmHouse_Website.serializer import BookingsSerializer


class Home(APIView):
    def get(self, request):

        # serializer = BookingsSerializer(Bookings.objects.all(), many=True)
        # return Response(serializer.data, content_type='application/json')
        media = base64.b64encode(Bookings.objects.get(bookingId=1).IDimage).decode("utf-8")
        html = f"""
        <html>
        <body>
            <h2>Media</h2>
            <video height="700" width="900" autoplay loop muted controls>
                <source src="data:video/mp4;base64,{media}">
                Your browser does not support the video tag.
            </video>
        </body>
        </html>
        """

        return HttpResponse(html, content_type='text/html')
