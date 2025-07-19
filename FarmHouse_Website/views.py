from datetime import datetime, date
from rest_framework import viewsets, status
from rest_framework.response import Response
from FarmHouse_Website.serializer import *

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Bookings.objects.all()
    serializer_class = BookingsSerializer

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            check_in_date = serializer.validated_data['checkInDate']
            check_out_date = serializer.validated_data['checkOutDate']

            validity_status, message = utils.validate_booking_dates(check_in_date, check_out_date)
            print(message)

            if not validity_status:
                return Response({'error': message}, status=status.HTTP_406_NOT_ACCEPTABLE)

            conflict_status, conflicts = utils.check_booking_availability(check_in_date, check_out_date)
            if conflict_status:
                return Response(data=conflicts, status=status.HTTP_409_CONFLICT)

            serializer.validated_data['bookingDate'] = date.today()
            confirmed_booking = serializer.save()
            if  confirmed_booking :
                if utils.sendConfirmationEmail(confirmed_booking.guestEmail,confirmed_booking.guestName ,confirmed_booking.checkInDate, confirmed_booking.checkOutDate, confirmed_booking.guestPhone) :
                    return Response(serializer.data, status=status.HTTP_200_OK)
                else :
                    return Response("Error sending confirmation email", status = status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

class MenuViewSet(viewsets.ModelViewSet):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer

class ReviewsViewSet(viewsets.ModelViewSet):
    queryset = Reviews.objects.all()
    serializer_class = ReviewsSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid(raise_exception=True):

            if not Bookings.objects.filter(guestPhone = request.data['guestPhone']).exists():
                return Response(status=status.HTTP_406_NOT_ACCEPTABLE)

            try:
                serializer.validated_data['bookingId'] = Bookings.objects.filter(guestPhone=request.data['guestPhone']).last().bookingId
                serializer.validated_data['reviewDate'] = datetime.today()
                saved_review = serializer.save()
                
                if utils.setMedia(media_list=request.FILES.getlist('media_list'),
                    review=Reviews.objects.get(reviewId=saved_review.reviewId)):
                    return Response(status=status.HTTP_200_OK)
                else:
                    return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                print(e)
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
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
