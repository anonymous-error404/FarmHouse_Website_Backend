import base64

from django.http import HttpResponse
from django.shortcuts import render
from django.utils.html import format_html
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from django.db.models import Q
from datetime import datetime, timedelta

from FarmHouse_Website.models import Bookings
from FarmHouse_Website.serializer import BookingsSerializer as BookingSerializer


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

# Add these new classes/functions
class BookingViewSet(viewsets.ModelViewSet):
    queryset = Bookings.objects.all()
    serializer_class = BookingSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new booking with the current date as booking date"""
        # Create a mutable copy of the data
        mutable_data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        
        # Set current date as booking date if not already set
        if 'bookingDate' not in mutable_data:
            mutable_data['bookingDate'] = datetime.now().strftime('%Y-%m-%d')
        
        # Set default payment status to pending (0)
        if 'paymentStatus' not in mutable_data:
            mutable_data['paymentStatus'] = 0
        
        # Create a new serializer with our modified data
        serializer = self.get_serializer(data=mutable_data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract requested dates and calculate duration
        check_in_date = serializer.validated_data.get('checkInDate')
        check_out_date = serializer.validated_data.get('checkOutDate')
        requested_duration = (check_out_date - check_in_date).days
        
        # Check for availability
        available, alternatives = self.check_availability_with_alternatives(
            check_in_date, check_out_date, requested_duration)
        
        if not available:
            return Response({
                'status': 'unavailable',
                'message': 'The property is already booked for these dates.',
                'alternative_dates': alternatives
            }, status=status.HTTP_409_CONFLICT)
        
        # Save the booking if dates are available
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def check_availability_with_alternatives(self, check_in_date, check_out_date, duration):
        """
        Checks if property is available for requested dates.
        Returns a tuple (availability_status, alternative_dates)
        Alternative dates include:
        1. Available periods within the requested timeframe (even partial)
        2. Next available periods for the same or similar duration
        """
        # Define confirmed booking statuses
        CONFIRMED_STATUSES = [1, 2]  # Paid or Approved
        
        # Look for any confirmed bookings that overlap with the requested period
        conflicts = Bookings.objects.filter(
            Q(paymentStatus__in=CONFIRMED_STATUSES) &
            (
                # Case 1: A booking that starts during the requested period
                (Q(checkInDate__gte=check_in_date) & Q(checkInDate__lt=check_out_date)) |
                # Case 2: A booking that ends during the requested period
                (Q(checkOutDate__gt=check_in_date) & Q(checkOutDate__lte=check_out_date)) |
                # Case 3: A booking that completely spans the requested period
                (Q(checkInDate__lte=check_in_date) & Q(checkOutDate__gte=check_out_date))
            )
        ).order_by('checkInDate')
        
        if not conflicts.exists():
            return True, None
        
        # Generate alternative dates
        alternatives = {
            'partial_availability': [],  # Periods within requested timeframe (even if shorter)
            'next_available_periods': []  # Future periods of similar duration
        }
        
        # 1. Find available periods within the requested timeframe (even if partial)
        current_date = check_in_date
        for booking in conflicts:
            if current_date < booking.checkInDate:
                available_days = (booking.checkInDate - current_date).days
                # Include even if it's shorter than requested
                if available_days >= 1:
                    alternatives['partial_availability'].append({
                        'start_date': current_date.strftime('%Y-%m-%d'),
                        'end_date': (booking.checkInDate - timedelta(days=1)).strftime('%Y-%m-%d'),
                        'days': available_days
                    })
            current_date = max(current_date, booking.checkOutDate + timedelta(days=1))
        
        if current_date < check_out_date:
            available_days = (check_out_date - current_date).days
            if available_days >= 1:
                alternatives['partial_availability'].append({
                    'start_date': current_date.strftime('%Y-%m-%d'),
                    'end_date': check_out_date.strftime('%Y-%m-%d'),
                    'days': available_days
                })
        
        # 2. Find next available periods for the same or similar duration
        # Start looking from the day after the last conflict ends
        latest_conflict = conflicts.last()
        search_start = latest_conflict.checkOutDate + timedelta(days=1)
        search_end = search_start + timedelta(days=90)  # Look 90 days ahead
        
        available_periods = self.get_available_date_ranges(search_start, search_end)
        
        # Find periods that are at least 50% of the requested duration
        min_acceptable_duration = max(2, duration // 2)  # At least 2 days or half the requested duration
        
        for period in available_periods:
            period_duration = (period['end'] - period['start']).days + 1
            
            # If period is exactly the requested duration, add it directly
            if period_duration == duration:
                alternatives['next_available_periods'].append({
                    'start_date': period['start'].strftime('%Y-%m-%d'),
                    'end_date': period['end'].strftime('%Y-%m-%d'),
                    'days': period_duration
                })
            
            # If period is longer than needed, offer multiple options
            elif period_duration > duration:
                for i in range(0, min(5, period_duration - duration + 1), 1):
                    start = period['start'] + timedelta(days=i)
                    end = start + timedelta(days=duration - 1)
                    
                    alternatives['next_available_periods'].append({
                        'start_date': start.strftime('%Y-%m-%d'),
                        'end_date': end.strftime('%Y-%m-%d'),
                        'days': duration
                    })
            
            # If period is shorter but at least the minimum acceptable duration
            elif period_duration >= min_acceptable_duration:
                alternatives['next_available_periods'].append({
                    'start_date': period['start'].strftime('%Y-%m-%d'),
                    'end_date': period['end'].strftime('%Y-%m-%d'),
                    'days': period_duration
                })
            
            # Limit to 10 total alternatives
            if len(alternatives['next_available_periods']) >= 10:
                break
        
        # Sort alternatives by days (highest first)
        alternatives['partial_availability'].sort(key=lambda x: x['days'], reverse=True)
        alternatives['next_available_periods'].sort(key=lambda x: x['days'], reverse=True)
        
        return False, alternatives
    
    def get_available_date_ranges(self, start_date, end_date):
        """Gets available date ranges between start_date and end_date"""
        CONFIRMED_STATUSES = [1, 2]
        
        # Get all confirmed bookings in the date range
        bookings = Bookings.objects.filter(
            Q(paymentStatus__in=CONFIRMED_STATUSES) &
            (
                (Q(checkInDate__gte=start_date) & Q(checkInDate__lte=end_date)) |
                (Q(checkOutDate__gte=start_date) & Q(checkOutDate__lte=end_date)) |
                (Q(checkInDate__lte=start_date) & Q(checkOutDate__gte=end_date))
            )
        ).order_by('checkInDate')
        
        # If no bookings, the whole period is available
        if not bookings:
            return [{'start': start_date, 'end': end_date}]
        
        available_periods = []
        current_date = start_date
        
        # Add periods between bookings
        for booking in bookings:
            if current_date < booking.checkInDate:
                available_periods.append({
                    'start': current_date,
                    'end': booking.checkInDate - timedelta(days=1)
                })
            current_date = booking.checkOutDate + timedelta(days=1)
        
        # Add period after the last booking
        if current_date <= end_date:
            available_periods.append({
                'start': current_date,
                'end': end_date
            })
        
        return available_periods


@api_view(['GET'])
def check_availability(request):
    """Endpoint to check availability with alternative date suggestions"""
    try:
        check_in_date = datetime.strptime(request.query_params.get('check_in_date'), '%Y-%m-%d').date()
        check_out_date = datetime.strptime(request.query_params.get('check_out_date'), '%Y-%m-%d').date()
        duration = (check_out_date - check_in_date).days
    except (ValueError, TypeError):
        return Response({
            'error': 'Invalid date format. Please use YYYY-MM-DD.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    booking_viewset = BookingViewSet()
    available, alternatives = booking_viewset.check_availability_with_alternatives(
        check_in_date, check_out_date, duration)
    
    return Response({
        'available': available,
        'requested_period': {
            'start_date': check_in_date.strftime('%Y-%m-%d'),
            'end_date': check_out_date.strftime('%Y-%m-%d'),
            'days': duration
        },
        'alternative_dates': alternatives if not available else None
    })


@api_view(['POST'])
def update_booking_status(request, booking_id):
    """Update a booking's payment status"""
    try:
        booking = Bookings.objects.get(bookingId=booking_id)
    except Bookings.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get the new payment status from request data
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
    
    # If changing to approved status, check for availability
    CONFIRMED_STATUSES = [1, 2]
    if new_status in CONFIRMED_STATUSES and booking.paymentStatus not in CONFIRMED_STATUSES:
        booking_viewset = BookingViewSet()
        available, alternatives = booking_viewset.check_availability_with_alternatives(
            booking.checkInDate, booking.checkOutDate, 
            (booking.checkOutDate - booking.checkInDate).days)
        
        if not available:
            return Response({
                'status': 'unavailable',
                'message': 'The property is already booked for these dates.',
                'alternative_dates': alternatives
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


# BookingViewSet emei jo Bookings model ke liye CRUD operations handle karega
# Ismein filtering, validation aur save logic manage kiya 

# check_availability function ek API endpoint hai jo utils.py ka get_available_dates use karke frontend ko availability deta hai.
# update_booking_status ek function-based API view hai jo kisi booking ka payment status update karta hai based on booking ID.

# Har ek view securely aur efficiently request handle karta hai, aur relevant response deta hai.
# Agar koi invalid data aaye to proper error message return hota hai, jo debugging mein help karega
