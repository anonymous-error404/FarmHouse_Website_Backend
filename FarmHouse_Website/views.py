from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class Home(APIView):
    def get(self,request):
        return Response({'key':'value'}, content_type="application/json")


