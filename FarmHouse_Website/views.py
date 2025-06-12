from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from django.db.models import Q
from datetime import datetime, timedelta
from .serializers import BookingSerializer, BookingFullSerializer
from .models import Bookings
from .utils import get_available_dates, CONFIRMED_PAYMENT_STATUSES, PAYMENT_STATUS_APPROVED_UNPAID

class Home(APIView):
    def get(self,request):
        return Response({'key':'value'}, content_type="application/json")

# Add these new classes/functions
class BookingViewSet(viewsets.ModelViewSet):
    queryset = Bookings.objects.all()
    serializer_class = BookingSerializer
    
    def get_serializer_class(self):
        """Return different serializers for staff users vs regular users"""
        # For admin operations, use the full serializer
        if self.request.user.is_staff:
            return BookingFullSerializer
        return BookingSerializer
    
    def create(self, request, *args, **kwargs):
        
        request.data['bookingDate'] = datetime.now().strftime('%Y-%m-%d')
        
        
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract requested dates
        check_in_date = serializer.validated_data.get('checkInDate')
        check_out_date = serializer.validated_data.get('checkOutDate')
        
        # Check for availability
        available, next_available = self.check_availability(check_in_date, check_out_date)
        
        if not available:
            return Response({
                'status': 'unavailable',
                'message': 'The property is already booked for these dates.',
                'next_available_date': next_available
            }, status=status.HTTP_409_CONFLICT)
        
        # Save the booking with payment status 0 (pending)
        serializer.validated_data['paymentStatus'] = 0
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def check_availability(self, check_in_date, check_out_date):
        """
        Checks if the property is available for the requested dates.
        Returns a tuple (availability_status, next_available_date)
        """
        
        conflicts = Bookings.objects.filter(
            # Consider a booking confirmed if paymentStatus is in CONFIRMED_PAYMENT_STATUSES (1 or 2)
            Q(paymentStatus__in=CONFIRMED_PAYMENT_STATUSES) &
            (
                #Booking that starts during the requested period
                (Q(checkInDate__gte=check_in_date) & Q(checkInDate__lt=check_out_date)) |
                #Booking that ends during the requested period
                (Q(checkOutDate__gt=check_in_date) & Q(checkOutDate__lte=check_out_date)) |
                #Booking that completely spans the requested period
                (Q(checkInDate__lte=check_in_date) & Q(checkOutDate__gte=check_out_date))
            )
        ).order_by('checkOutDate')
        
        if not conflicts.exists():
            return True, None
        
        # Find the next date
        latest_conflict = conflicts.last()
        next_available = latest_conflict.checkOutDate + timedelta(days=1)
        
        return False, next_available

@api_view(['GET'])
def check_availability(request):
    """Endpoint to check availability without creating a booking"""
    try:
        check_in_date = datetime.strptime(request.query_params.get('check_in_date'), '%Y-%m-%d').date()
        check_out_date = datetime.strptime(request.query_params.get('check_out_date'), '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return Response({
            'error': 'Invalid date format. Please use YYYY-MM-DD.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    booking_viewset = BookingViewSet()
    available, next_available = booking_viewset.check_availability(check_in_date, check_out_date)
    
    return Response({
        'available': available,
        'next_available_date': next_available.strftime('%Y-%m-%d') if next_available else None
    })

@api_view(['GET'])
def available_dates(request):
    """Return a list of available date ranges for booking"""
    try:
        start_date = request.query_params.get('start_date')
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = datetime.now().date()
            
        end_date = request.query_params.get('end_date')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            # show next 90 days
            end_date = start_date + timedelta(days=90)
            
    except ValueError:
        return Response({
            'error': 'Invalid date format. Please use YYYY-MM-DD.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    available_periods = get_available_dates(start_date, end_date)
    
    return Response({
        'available_periods': [
            {
                'start': period['start'].strftime('%Y-%m-%d'),
                'end': period['end'].strftime('%Y-%m-%d'),
                'days': (period['end'] - period['start']).days + 1
            }
            for period in available_periods
        ]
    })

@api_view(['POST'])
def update_payment_status(request, booking_id):
    """Update a booking's payment status"""
    try:
        booking = Bookings.objects.get(bookingId=booking_id)
    except Bookings.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    
  
    new_status = request.data.get('payment_status')
    if new_status is None:
        return Response({'error': 'payment_status is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        new_status = int(new_status)
    except ValueError:
        return Response({'error': 'payment_status must be an integer'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate payment status
    if new_status not in [0, 1, 2]:
        return Response({'error': 'Invalid payment status. Use 0 for pending, 1 for paid, 2 for approved but unpaid'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    
    if new_status in CONFIRMED_PAYMENT_STATUSES and booking.paymentStatus not in CONFIRMED_PAYMENT_STATUSES:
        booking_viewset = BookingViewSet()
        available, next_available = booking_viewset.check_availability(booking.checkInDate, booking.checkOutDate)
        
        if not available:
            return Response({
                'status': 'unavailable',
                'message': 'The property is already booked for these dates.',
                'next_available_date': next_available.strftime('%Y-%m-%d')
            }, status=status.HTTP_409_CONFLICT)
    
    # Update payment status
    booking.paymentStatus = new_status
    booking.save()
    
    return Response({
        'status': 'success',
        'message': f'Booking payment status updated to {new_status}',
        'booking_id': booking.bookingId,
        'payment_status': booking.paymentStatus
    })
