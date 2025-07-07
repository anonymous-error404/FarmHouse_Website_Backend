from django.db import models

class Bookings(models.Model):
    bookingId = models.AutoField(primary_key=True)
    bookingDate = models.DateField()
    checkInDate = models.DateField()
    checkOutDate = models.DateField()
    paymentStatus = models.CharField(default="", max_length=10)
    paymentType = models.CharField(max_length=100)
    paymentAmount = models.IntegerField(default=0)
    guestName = models.TextField()
    guestEmail = models.CharField(max_length=50)
    guestPhone = models.CharField(max_length=15)
    guestAddress = models.TextField()
    totalGuestsAdults = models.IntegerField(default=0)
    totalGuestsChildren = models.IntegerField(default=0)
    purposeOfStay = models.CharField(max_length=50)

class Reviews(models.Model):
    reviewId = models.AutoField(primary_key=True)
    bookingId = models.IntegerField()
    reviewTitle = models.CharField(max_length=50, default="")
    reviewDate = models.DateField()
    rating = models.IntegerField()
    reviewContent = models.TextField(default="")

class ReviewsMedia(models.Model):
    mediaId = models.AutoField(primary_key=True)
    reviewId = models.ForeignKey(Reviews, on_delete=models.CASCADE)
    mediaName = models.CharField(max_length=50, default="")
    mediaType = models.CharField(max_length=20)
    media = models.BinaryField()

class Menu(models.Model):
    dishId = models.AutoField(primary_key=True)
    dishName = models.CharField(max_length=50)
    dishDescription = models.TextField()
    dishPrice = models.IntegerField()
    dishImage = models.BinaryField()
    dishCategory = models.CharField(max_length=30, default="")
    dishSource = models.CharField(max_length=30, default="")


