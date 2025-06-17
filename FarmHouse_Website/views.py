import base64
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView

from FarmHouse_Website import utils
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

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)#raw data
        print(serializer.initial_data)

        if serializer.is_valid(raise_exception=True): #check if data is valid
            check_in_date = serializer.validated_data['checkInDate']
            check_out_date = serializer.validated_data['checkOutDate']
            validity_status,message = utils.validate_booking_dates(check_in_date, check_out_date)
            print(message)
            print(serializer.validated_data)
            if validity_status:
                conflict_status,conflicting_dates = utils.check_booking_availability(check_in_date, check_out_date)
                if conflict_status:
                    print("hi")
                    return Response(conflicting_dates,status=status.HTTP_409_CONFLICT)
                else :
                    print("hie")
                    if not serializer.validated_data['IDimage'] :
                        print("hello")
                        return Response({'message':'IDimage is required'},status=status.HTTP_206_PARTIAL_CONTENT)
                    else :
                        print("hellow")
                        serializer.validated_data['bookingDate'] = datetime.now()
                        print(serializer.validated_data)
                        serializer.save()
                        return Response(status=status.HTTP_200_OK)
            else :
                return Response(status=status.HTTP_406_NOT_ACCEPTABLE)
        else :
            return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY)

class MenuViewSet(viewsets.ModelViewSet):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer