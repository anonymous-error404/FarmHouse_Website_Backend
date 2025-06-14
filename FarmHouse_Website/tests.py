from datetime import date

from django.test import TestCase
from .models import *
from .views import *

class modelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        try:
            dummy_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x12IDATx\x9cc```bPPP\x00\x02\xac\xea\x05\xc1\x1e\x1d\x00\x00\x00\x00IEND\xaeB`\x82'

            cls.booking = Bookings.objects.create(
                bookingDate=date(2025, 6, 12),
                checkInDate=date(2025, 6, 15),
                checkOutDate=date(2025, 6, 20),
                paymentStatus=1,
                paymentType="Credit Card",
                paymentAmount=5000,
                guestName="John Doe",
                guestEmail="john@example.com",
                guestPhone="9876543210",
                guestAddress="123 Main Street, City",
                totalGuestsAdults=2,
                totalGuestsChildren=1,
                IDtype="Aadhaar",
                IDnumber="1234-5678-9012",
                IDimage=dummy_image_data,
                purposeOfStay="Vacation"
            )

            print(f"Created booking with ID: {cls.booking.bookingId}")

            cls.review = Reviews.objects.create(
                bookingId=cls.booking,  # Use the booking object directly
                reviewDate=date(2025, 6, 21),
                rating=4,
                reviewContent="Great stay, friendly staff!"
            )
            print(f"Created review with ID: {cls.review.reviewId}")

            cls.reviewMedia = ReviewsMedia.objects.create(
                reviewId=cls.review,  # Use the review object directly
                mediaType="image",
                media=dummy_image_data,
            )
            print(f"Created review media with ID: {cls.reviewMedia.reviewMediaId}")

        except Exception as e:
            print(f"Something went wrong in setUpTestData: {e}")
            # Re-raise the exception so the test setup failure is visible
            raise

    def test_getBookingobjectTest(self):
        # Use the booking ID that was actually created
        booking = Bookings.objects.get(bookingId=self.booking.bookingId)
        print(f"Retrieved booking date: {booking.bookingDate}")
        
        # Add some assertions to make this a proper test
        self.assertEqual(booking.guestName, "John Doe")
        self.assertEqual(booking.paymentStatus, 1)
        self.assertEqual(booking.paymentAmount, 5000)


from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from datetime import date, timedelta
from .models import Bookings
from .views import BookingViewSet
import json

class BookingSystemTests(TestCase):
    """Test class specifically for the booking system with alternative date suggestions"""
    
    @classmethod
    def setUpTestData(cls):
        """Create test bookings for availability testing"""
        # Create a confirmed booking for next week
        today = date.today()
        cls.next_week = today + timedelta(days=7)
        cls.two_weeks = today + timedelta(days=14)
        
        # Use dummy image data instead of trying to read from file
        dummy_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x12IDATx\x9cc```bPPP\x00\x02\xac\xea\x05\xc1\x1e\x1d\x00\x00\x00\x00IEND\xaeB`\x82'
        
        cls.confirmed_booking = Bookings.objects.create(
            bookingDate=today,
            checkInDate=cls.next_week,
            checkOutDate=cls.next_week + timedelta(days=3),  # 3-day booking
            paymentStatus=1,  # Confirmed/paid
            paymentType="Credit Card",
            paymentAmount=3000,
            guestName="Test Guest",
            guestEmail="test@example.com",
            guestPhone="1234567890",
            guestAddress="Test Address",
            totalGuestsAdults=2,
            totalGuestsChildren=0,
            IDtype="Passport",
            IDnumber="TEST123",
            IDimage=dummy_image_data,
            purposeOfStay="Testing"
        )
        
        # Create a pending booking for the day after
        cls.pending_booking = Bookings.objects.create(
            bookingDate=today,
            checkInDate=cls.next_week + timedelta(days=4),
            checkOutDate=cls.next_week + timedelta(days=6),  # 2-day booking
            paymentStatus=0,  # Pending
            paymentType="Cash",
            paymentAmount=2000,
            guestName="Pending Guest",
            guestEmail="pending@example.com",
            guestPhone="9876543210",
            guestAddress="Pending Address",
            totalGuestsAdults=1,
            totalGuestsChildren=1,
            IDtype="Driver License",
            IDnumber="PENDING456",
            IDimage=dummy_image_data,
            purposeOfStay="Pending Test"
        )
        
        print(f"Created test bookings: confirmed {cls.confirmed_booking.bookingId}, pending {cls.pending_booking.bookingId}")
    
    def test_availability_check_api(self):
        """Test the check-availability endpoint with different scenarios"""
        client = Client()
        today = date.today()
        next_week = today + timedelta(days=7)
        
        # Case 1: Available dates (before any bookings)
        response = client.get(
            f'/api/check-availability/?check_in_date={today}&check_out_date={today + timedelta(days=3)}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertTrue(data['available'])
        print("✓ Available dates test passed")
        
        # Case 2: Unavailable dates (conflict with confirmed booking)
        conflict_start = next_week + timedelta(days=1)  # Inside confirmed booking
        conflict_end = next_week + timedelta(days=5)    # Extends beyond confirmed booking
        
        response = client.get(
            f'/api/check-availability/?check_in_date={conflict_start.isoformat()}&check_out_date={conflict_end.isoformat()}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertFalse(data['available'])
        self.assertIn('alternative_dates', data)
        
        # Check if partial availability suggestions are present
        self.assertIn('partial_availability', data['alternative_dates'])
        
        # Check if next available periods are suggested
        self.assertIn('next_available_periods', data['alternative_dates'])
        print("✓ Unavailable dates test with alternatives passed")
    
    def test_create_booking_api(self):
        """Test creating bookings through the API"""
        client = Client()
        today = date.today()
        two_weeks = today + timedelta(days=14)
        
        # Case 1: Create a valid booking
        booking_data = {
            'checkInDate': two_weeks.isoformat(),
            'checkOutDate': (two_weeks + timedelta(days=5)).isoformat(),
            'paymentType': "Credit Card",
            'paymentAmount': 4000,
            'guestName': "API Test Guest",
            'guestEmail': "apitest@example.com",
            'guestPhone': "5551234567",
            'guestAddress': "API Test Address",
            'totalGuestsAdults': 2,
            'totalGuestsChildren': 1,
            'IDtype': "Passport",
            'IDnumber': "API789",
            'purposeOfStay': "API Testing"
        }
        
        response = client.post(
            '/api/bookings/',
            data=json.dumps(booking_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)
        self.assertEqual(data['paymentStatus'], 0)  # Should be created as pending
        created_booking_id = data['bookingId']
        print(f"✓ Successfully created booking with ID {created_booking_id}")
        
        # Case 2: Try creating a booking with conflict
        conflict_data = {
            'checkInDate': self.next_week.isoformat(),  # Conflicts with existing confirmed booking
            'checkOutDate': (self.next_week + timedelta(days=5)).isoformat(),
            'paymentType': "Cash",
            'paymentAmount': 3000,
            'guestName': "Conflict Guest",
            'guestEmail': "conflict@example.com",
            'guestPhone': "5559876543",
            'guestAddress': "Conflict Address",
            'totalGuestsAdults': 1,
            'totalGuestsChildren': 0,
            'IDtype': "Driver License",
            'IDnumber': "CONFLICT123",
            'purposeOfStay': "Conflict Test"
        }
        
        response = client.post(
            '/api/bookings/',
            data=json.dumps(conflict_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'unavailable')
        self.assertIn('alternative_dates', data)
        print("✓ Conflict detection working correctly")
    
    def test_update_booking_status(self):
        """Test updating booking status with various scenarios"""
        client = Client()
        
        # Case 1: Update pending booking to approved
        response = client.post(
            f'/api/update-booking-status/{self.pending_booking.bookingId}/',
            data=json.dumps({'payment_status': 1}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_booking = Bookings.objects.get(bookingId=self.pending_booking.bookingId)
        self.assertEqual(updated_booking.paymentStatus, 1)
        print("✓ Successfully updated booking status")
        
        # Case 2: Create a conflicting pending booking
        today = date.today()
        dummy_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x12IDATx\x9cc```bPPP\x00\x02\xac\xea\x05\xc1\x1e\x1d\x00\x00\x00\x00IEND\xaeB`\x82'
        
        conflict_booking = Bookings.objects.create(
            bookingDate=today,
            checkInDate=self.next_week + timedelta(days=1),  # Conflicts with confirmed_booking
            checkOutDate=self.next_week + timedelta(days=4),
            paymentStatus=0,  # Pending
            paymentType="Cash",
            paymentAmount=1500,
            guestName="Conflict Test",
            guestEmail="conflict.test@example.com",
            guestPhone="1112223333",
            guestAddress="Conflict Test Address",
            totalGuestsAdults=1,
            totalGuestsChildren=0,
            IDtype="National ID",
            IDnumber="CONFTEST789",
            IDimage=dummy_image_data,
            purposeOfStay="Conflict Status Test"
        )
        
        # Try to approve the conflicting booking - should fail
        response = client.post(
            f'/api/update-booking-status/{conflict_booking.bookingId}/',
            data=json.dumps({'payment_status': 2}),  # Approved but unpaid
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        still_pending = Bookings.objects.get(bookingId=conflict_booking.bookingId)
        self.assertEqual(still_pending.paymentStatus, 0)  # Should still be pending
        print("✓ Prevented approval of conflicting booking")
    
    def test_partial_availability_suggestions(self):
        """Test partial availability suggestions when requested duration is partially available"""
        today = date.today()
        client = Client()
        
        # Create 3 separate bookings with gaps between them
        start_date = today + timedelta(days=30)
        dummy_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x12IDATx\x9cc```bPPP\x00\x02\xac\xea\x05\xc1\x1e\x1d\x00\x00\x00\x00IEND\xaeB`\x82'
        
        # First booking: Days 30-32
        booking1 = Bookings.objects.create(
            bookingDate=today,
            checkInDate=start_date,
            checkOutDate=start_date + timedelta(days=2),
            paymentStatus=1,
            paymentType="Credit Card",
            paymentAmount=2000,
            guestName="Gap Test 1",
            guestEmail="gap1@example.com",
            guestPhone="1111111111",
            guestAddress="Gap Address 1",
            totalGuestsAdults=2,
            totalGuestsChildren=0,
            IDtype="Passport",
            IDnumber="GAP111",
            IDimage=dummy_image_data,
            purposeOfStay="Gap Testing"
        )
        
        # Second booking: Days 35-37
        booking2 = Bookings.objects.create(
            bookingDate=today,
            checkInDate=start_date + timedelta(days=5),
            checkOutDate=start_date + timedelta(days=7),
            paymentStatus=1,
            paymentType="Credit Card",
            paymentAmount=2000,
            guestName="Gap Test 2",
            guestEmail="gap2@example.com",
            guestPhone="2222222222",
            guestAddress="Gap Address 2",
            totalGuestsAdults=2,
            totalGuestsChildren=0,
            IDtype="Passport",
            IDnumber="GAP222",
            IDimage=dummy_image_data,
            purposeOfStay="Gap Testing"
        )
        
        # Third booking: Days 40-42
        booking3 = Bookings.objects.create(
            bookingDate=today,
            checkInDate=start_date + timedelta(days=10),
            checkOutDate=start_date + timedelta(days=12),
            paymentStatus=1,
            paymentType="Credit Card",
            paymentAmount=2000,
            guestName="Gap Test 3",
            guestEmail="gap3@example.com",
            guestPhone="3333333333",
            guestAddress="Gap Address 3",
            totalGuestsAdults=2,
            totalGuestsChildren=0,
            IDtype="Passport",
            IDnumber="GAP333",
            IDimage=dummy_image_data,
            purposeOfStay="Gap Testing"
        )
        
        # Request a 10-day period that spans all three bookings
        request_start = start_date - timedelta(days=1)
        request_end = start_date + timedelta(days=13)
        
        response = client.get(
            f'/api/check-availability/?check_in_date={request_start.isoformat()}&check_out_date={request_end.isoformat()}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertFalse(data['available'])
        
        # Verify partial availability suggestions
        self.assertIn('partial_availability', data['alternative_dates'])
        partial_options = data['alternative_dates']['partial_availability']
        
        # Should have at least 3 periods of partial availability
        self.assertGreaterEqual(len(partial_options), 3)
        
        # Check that alternatives include some expected gaps
        found_ranges = 0
        for option in partial_options:
            if option['days'] >= 1:  # Any valid period
                found_ranges += 1
        
        self.assertGreaterEqual(found_ranges, 2)  # Should find at least 2 valid periods
        print(f"✓ Found {found_ranges} partial availability periods as expected")
        
        # Verify that days counts are correct
        for option in partial_options:
            start_date_parsed = date.fromisoformat(option['start_date'])
            end_date_parsed = date.fromisoformat(option['end_date'])
            expected_days = (end_date_parsed - start_date_parsed).days + 1
            self.assertEqual(option['days'], expected_days)
        
        print("✓ Day counts in alternative suggestions are correct")

    def test_direct_availability_functions(self):
        """Test the internal availability checking functions directly"""
        viewset = BookingViewSet()
        today = date.today()
        next_week = today + timedelta(days=7)
        
        # Test get_available_date_ranges
        available_ranges = viewset.get_available_date_ranges(today, today + timedelta(days=30))
        self.assertTrue(len(available_ranges) > 0)
        
        # Test check_availability_with_alternatives
        available, alternatives = viewset.check_availability_with_alternatives(
            next_week, next_week + timedelta(days=5), 5)
        
        # Should be unavailable due to confirmed_booking
        self.assertFalse(available)
        self.assertIsNotNone(alternatives)
        
        # Test for a period that should be available
        available, alternatives = viewset.check_availability_with_alternatives(
            today, today + timedelta(days=3), 3)
        self.assertTrue(available)
        self.assertIsNone(alternatives)
        
        print("✓ Internal availability functions working correctly")


def run_booking_tests():
    """Run all booking system tests"""
    print("\nRUNNING BOOKING SYSTEM TESTS")
    print("============================")
    
    tests = [
        'test_availability_check_api',
        'test_create_booking_api',
        'test_update_booking_status',
        'test_partial_availability_suggestions',
        'test_direct_availability_functions',
    ]
    
    failures = []
    for test_name in tests:
        print(f"\nRunning {test_name}...")
        try:
            # Create test instance
            test_instance = BookingSystemTests()
            test_instance._pre_setup()
            
            # Set up test data
            test_instance.setUpTestData()
            
            # Run the test
            getattr(test_instance, test_name)()
            
            # Clean up
            test_instance._post_teardown()
            
            print(f"✓ {test_name} PASSED")
        except Exception as e:
            print(f"✗ {test_name} FAILED: {e}")
            failures.append((test_name, str(e)))
    
    # Print summary
    print("\nTEST SUMMARY")
    print("============")
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {len(tests) - len(failures)}")
    print(f"Failed: {len(failures)}")
    
    if failures:
        print("\nFAILURES:")
        for name, error in failures:
            print(f"- {name}: {error}")
    else:
        print("\n✓ ALL TESTS PASSED - Booking system is working correctly!")
    
    return len(failures) == 0


if __name__ == "__main__":
    # This allows you to run this test file directly instead of through Django's test runner
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FarmHouse_Website_Backend.settings')
    django.setup()
    
    # Run the tests
    success = run_booking_tests()
    
    # Exit with appropriate code
    import sys
    sys.exit(0 if success else 1)

# Test file mein bakchodi zara ignore kar chatgpt ki hai
