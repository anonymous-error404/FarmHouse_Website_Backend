from datetime import datetime
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from FarmHouse_Website.serializer import *

temporary_otp_storage = {}
class Home(APIView):
    def get(self, request):
        image_bin = Bookings.objects.get(bookingId=10).IDimage
        image = base64.b64encode(image_bin).decode('utf-8')
        html = f"""
        <html>
        <body>
            <h2>ID Image Preview</h2>
            <img src="data:image/jpeg;base64,{image}" height="1000" width="1200">
        </body>
        </html>
        """

        return HttpResponse(html, content_type='text/html')

#gotta create a new url mapping for otp verification and call the bookingviewset.create method after otp is verified

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Bookings.objects.all()
    serializer_class = BookingsSerializer

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)  # raw data

        if serializer.is_valid(raise_exception=True):  # check if data is valid
            check_in_date = serializer.validated_data['checkInDate']
            check_out_date = serializer.validated_data['checkOutDate']
            validity_status, message = utils.validate_booking_dates(check_in_date, check_out_date)
            print(message)

            if validity_status:
                conflict_status, conflicts = utils.check_booking_availability(check_in_date, check_out_date)
                if conflict_status:
                    return Response(data=conflicts, status=status.HTTP_409_CONFLICT)
                else:
                    if 'IDimage' not in serializer.validated_data:
                        return Response({'message': 'IDimage is required'}, status=status.HTTP_206_PARTIAL_CONTENT)
                    else:
                        receiver = serializer.validated_data['guestEmail']
                        request.session['receiver'] = receiver
                        if not utils.sendOtpVerificationMail(receiver) :
                            return Response(status=status.HTTP_424_FAILED_DEPENDENCY)
                        else :
                            serializer.validated_data['bookingDate'] = datetime.today()
                            serializer.save()
                            return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_406_NOT_ACCEPTABLE)
        else:
            return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY)

class MenuViewSet(viewsets.ModelViewSet):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer

class ReviewsViewSet(viewsets.ModelViewSet):
    queryset = Reviews.objects.all()
    serializer_class = ReviewsSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid(raise_exception=True):

            if not Bookings.objects.filter(bookingId=serializer.validated_data['bookingId']).exists():
                return Response(status=status.HTTP_406_NOT_ACCEPTABLE)

            try:
                serializer.validated_data['reviewDate'] = datetime.today()
                saved_review = serializer.save()

                if utils.setMedia(media_list=request.FILES.getlist('media_list'),
                                  review=Reviews.objects.get(reviewId=saved_review.reviewId)):
                    return Response(status=status.HTTP_200_OK)
                else:
                    return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                print(e)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = ReviewsSerializer(queryset, many=True)
        reviews = serializer.data

        for review in reviews:
            review['media_list'] = utils.getMedia(review['reviewId'])

        return Response(data=reviews, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_queryset().get(reviewId=kwargs.get('pk'))
        serializer = ReviewsSerializer(queryset, many=False)
        review = serializer.data
        review['media_list'] = utils.getMedia(review['reviewId'])
        return Response(data=review, status=status.HTTP_200_OK)



