from datetime import datetime, timedelta
from django.db.models import Q
from .models import Bookings

# Define payment status constants for clarity
PAYMENT_STATUS_PENDING = 0
PAYMENT_STATUS_PAID = 1
PAYMENT_STATUS_APPROVED_UNPAID = 2

# List of payment statuses that should block dates (confirmed bookings)
CONFIRMED_PAYMENT_STATUSES = [PAYMENT_STATUS_PAID, PAYMENT_STATUS_APPROVED_UNPAID]


def get_available_dates(start_date, end_date=None, days=30):
    """
    Get a list of available date ranges between start_date and end_date
    or next [days] days if end_date is not provided.
    """
    if not end_date:
        end_date = start_date + timedelta(days=days)
    
    # Get all confirmed bookings in the date range
    bookings = Bookings.objects.filter(
        Q(paymentStatus__in=CONFIRMED_PAYMENT_STATUSES) &
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


def check_booking_availability(check_in_date, check_out_date, exclude_booking_id=None):
    """
    Check if dates are available for booking.
    Returns (is_available: bool, conflicting_bookings: QuerySet)
    """
    # Look for any confirmed bookings that overlap with the requested period
    conflicts_query = Bookings.objects.filter(
        Q(paymentStatus__in=CONFIRMED_PAYMENT_STATUSES) &
        (
            # Case 1: A booking that starts during the requested period
            (Q(checkInDate__gte=check_in_date) & Q(checkInDate__lt=check_out_date)) |
            # Case 2: A booking that ends during the requested period
            (Q(checkOutDate__gt=check_in_date) & Q(checkOutDate__lte=check_out_date)) |
            # Case 3: A booking that completely spans the requested period
            (Q(checkInDate__lte=check_in_date) & Q(checkOutDate__gte=check_out_date))
        )
    )
    
    # Exclude current booking if updating existing booking
    if exclude_booking_id:
        conflicts_query = conflicts_query.exclude(bookingId=exclude_booking_id)
    
    conflicts = conflicts_query.order_by('checkInDate')
    
    return not conflicts.exists(), conflicts


def generate_alternative_dates(check_in_date, check_out_date, duration):
    """
    Generate alternative date suggestions when requested dates are unavailable.
    Returns dictionary with partial_availability and next_available_periods.
    """
    alternatives = {
        'partial_availability': [],  # Periods within requested timeframe (even if shorter)
        'next_available_periods': []  # Future periods of similar duration
    }
    
    # Get conflicting bookings
    _, conflicts = check_booking_availability(check_in_date, check_out_date)
    
    if not conflicts.exists():
        return alternatives
    
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
    
    available_periods = get_available_dates(search_start, search_end)
    
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
    
    return alternatives


def create_booking_with_validation(booking_data):
    """
    Create a new booking with date validation and automatic field setting.
    Returns (success: bool, data: dict, errors: dict)
    """
    from .serializer import BookingsSerializer
    
    # Set current date as booking date if not already set
    if 'bookingDate' not in booking_data or booking_data['bookingDate'] is None:
        booking_data['bookingDate'] = datetime.now().strftime('%Y-%m-%d')
    
    # Set default payment status to pending (0)
    if 'paymentStatus' not in booking_data:
        booking_data['paymentStatus'] = PAYMENT_STATUS_PENDING
    
    # Validate data with serializer
    serializer = BookingsSerializer(data=booking_data)
    
    if not serializer.is_valid():
        return False, None, serializer.errors
    
    # Extract requested dates and calculate duration
    check_in_date = serializer.validated_data.get('checkInDate')
    check_out_date = serializer.validated_data.get('checkOutDate')
    duration = (check_out_date - check_in_date).days
    
    # Check for availability
    is_available, _ = check_booking_availability(check_in_date, check_out_date)
    
    if not is_available:
        alternatives = generate_alternative_dates(check_in_date, check_out_date, duration)
        return False, {
            'status': 'unavailable',
            'message': 'The property is already booked for these dates.',
            'alternative_dates': alternatives
        }, None
    
    # Save the booking if dates are available
    booking = serializer.save()
    return True, serializer.data, None


def update_booking_payment_status(booking_id, new_status):
    """
    Update a booking's payment status with validation.
    Returns (success: bool, data: dict, error_message: str)
    """
    try:
        booking = Bookings.objects.get(bookingId=booking_id)
    except Bookings.DoesNotExist:
        return False, None, 'Booking not found'
    
    # Validate payment status
    try:
        new_status = int(new_status)
    except (ValueError, TypeError):
        return False, None, 'payment_status must be an integer'
    
    if new_status not in [PAYMENT_STATUS_PENDING, PAYMENT_STATUS_PAID, PAYMENT_STATUS_APPROVED_UNPAID]:
        return False, None, 'Invalid payment status. Use 0 for pending, 1 for paid, 2 for approved but unpaid'
    
    # If changing to approved status, check for availability (excluding current booking)
    if new_status in CONFIRMED_PAYMENT_STATUSES and booking.paymentStatus not in CONFIRMED_PAYMENT_STATUSES:
        is_available, _ = check_booking_availability(
            booking.checkInDate, 
            booking.checkOutDate, 
            exclude_booking_id=booking.bookingId
        )
        
        if not is_available:
            duration = (booking.checkOutDate - booking.checkInDate).days
            alternatives = generate_alternative_dates(booking.checkInDate, booking.checkOutDate, duration)
            return False, {
                'status': 'unavailable',
                'message': 'The property is already booked for these dates.',
                'alternative_dates': alternatives
            }, None
    
    # Update payment status
    booking.paymentStatus = new_status
    booking.save()
    
    return True, {
        'status': 'success',
        'message': f'Booking payment status updated to {new_status}',
        'booking_id': booking.bookingId,
        'payment_status': booking.paymentStatus
    }, None


def get_availability_info(check_in_date, check_out_date):
    """
    Get availability information for given date range.
    Returns availability status and alternatives if unavailable.
    """
    try:
        if isinstance(check_in_date, str):
            check_in_date = datetime.strptime(check_in_date, '%Y-%m-%d').date()
        if isinstance(check_out_date, str):
            check_out_date = datetime.strptime(check_out_date, '%Y-%m-%d').date()
        
        duration = (check_out_date - check_in_date).days
    except (ValueError, TypeError):
        return False, None, 'Invalid date format. Please use YYYY-MM-DD.'
    
    is_available, _ = check_booking_availability(check_in_date, check_out_date)
    alternatives = None
    
    if not is_available:
        alternatives = generate_alternative_dates(check_in_date, check_out_date, duration)
    
    return True, {
        'available': is_available,
        'requested_period': {
            'start_date': check_in_date.strftime('%Y-%m-%d'),
            'end_date': check_out_date.strftime('%Y-%m-%d'),
            'days': duration
        },
        'alternative_dates': alternatives
    }, None