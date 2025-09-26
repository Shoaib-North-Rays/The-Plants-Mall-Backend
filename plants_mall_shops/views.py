
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import status

from django.contrib.auth import get_user_model
from Authentication.models import *
from .models import *
from .serializers import *
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Shop, ShopImage
from .serializers import ShopSerializer, ShopImageSerializer
from .permissions import IsSalesManOrAdmin
from rest_framework.pagination import PageNumberPagination
from geopy.distance import geodesic
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from google import genai
import os
import tempfile
import json
import time
from plants_mall_shops.models import Shop
from orders.models import Order
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .shops_filters import ShopFilter

User = get_user_model()


class ShopPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
class CategoryListCreateAPIView(APIView):
     
    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

 
    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


 
class ShopCreateAPIView(generics.CreateAPIView):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [IsSalesManOrAdmin]
    parser_classes = [MultiPartParser, FormParser]   


class ShopListAPIView(generics.ListAPIView):
    serializer_class = ShopSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ShopPagination  
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ShopFilter
    search_fields = ["shop_name", "owner_name", "owner_phone"]
    ordering_fields = ["created_at", "shop_name"]

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser or user.is_staff:
            return (
                Shop.objects.all()
                .select_related("category")
                .prefetch_related("images", "voice_notes")
            )

        return (
            Shop.objects.filter(registered_by=user)
            .select_related("category")
            .prefetch_related("images", "voice_notes")
        )
class ShopUpdateAPIView(generics.RetrieveUpdateAPIView):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [permissions.IsAuthenticated, IsSalesManOrAdmin]
    lookup_field = "id"
class NearbyShopsAPIView(generics.ListAPIView):
    serializer_class = ShopNearBySerializer
    permission_classes = [permissions.IsAuthenticated, IsSalesManOrAdmin]
    pagination_class = ShopPagination 

    def get_queryset(self):
        user = self.request.user
        user_lat = self.request.query_params.get("lat")
        user_lng = self.request.query_params.get("lng")
        
        
        if user.is_staff: 
            shops = Shop.objects.all().select_related("category").prefetch_related("images", "voice_notes")
        else:  
            shops = Shop.objects.filter(registered_by=user).select_related("category").prefetch_related("images", "voice_notes")
             

        if not user_lat or not user_lng:
            return Shop.objects.none()

        try:
            user_location = (float(user_lat), float(user_lng))
        except ValueError:
            return Shop.objects.none()

 
        radius_setting = ShopSettings.objects.last() 
        radius_km = (radius_setting.radius_meters / 1000.0) if radius_setting else 5.0

        shops_with_distance = []
        for shop in shops:
            if shop.latitude and shop.longitude:
                shop_location = (float(shop.latitude), float(shop.longitude))
                distance = geodesic(user_location, shop_location).km
                if distance <= radius_km:
                    shop.distance = round(distance, 2)
                    shops_with_distance.append(shop)
                     

        return sorted(shops_with_distance, key=lambda s: s.distance)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
class SpeechToTextShopRegistrationAPIView(APIView):
    permission_classes=[permissions.IsAuthenticated,IsSalesManOrAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            client = genai.Client(api_key="AIzaSyApkNNlUSkMxgbf_3cR3Pn-6LcGApe66pE")
            start_time = time.time()

           
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_obj.name)[-1]) as temp_file:
                for chunk in file_obj.chunks():
                    temp_file.write(chunk)
                temp_path = temp_file.name

            
            myfile = client.files.upload(file=temp_path)

            response = client.models.generate_content(
                 model="gemini-2.0-flash", contents=["""Translate this audio into English efficiently and provide details only about the shop name, owner name and owner phone number.
                                            You need to follow this structure:
                                            {
                                                "shop_name":"Shop Name",
                                                "owner_name":"Owner Name",
                                                "owner_phone":"Owner Phone Number"
                                            }
                                            If the audio file doesn't contain value for any field, just keep the value for that field as "".
                                            """, myfile]
    )

            end_time = time.time()

        
            output_text = response.text.replace("```json", "").replace("```", "").strip()

             
            try:
                results = json.loads(output_text)
            except json.JSONDecodeError:
                results = output_text   

       
            os.remove(temp_path)

            return Response({
                "time_taken_sec": round(end_time - start_time, 2),
                "results": results
            })

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 

class UpdateLocationAPIView(APIView):
    """
    POST {
      "identifier": "device-123",
      "lat": 24.8607,
      "lng": 67.0011,
      "address": "Barkat Market, Lahore"
    }
    """

    def post(self, request, *args, **kwargs):
        identifier = request.data.get("identifier")
        lat = request.data.get("lat")
        lng = request.data.get("lng")
        address = request.data.get("address", "")

        if not identifier or not lat or not lng:
            return Response({"error": "Missing fields"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(pk=int(identifier))  
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

     
        obj, _ = StaffLocations.objects.update_or_create(
            staff=user,
            defaults={
                "current_lat": lat,
                "current_lng": lng,
                "address": address,
                "last_seen": timezone.now()
            }
        )

        return Response({"status": "ok", "user": user.username})


class SalesmenLocationsAPIView(APIView):
    def get(self, request, *args, **kwargs):
        qs = StaffLocations.objects.all()
        serializer = SalesmanSerializer(qs, many=True,context={'request': request})
        return Response(serializer.data)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def shop_stats(request):
    user = request.user

    total_shops_by_user = Shop.objects.filter(registered_by=user).count()

    total_orders = Order.objects.filter(order_taker=user).count()

    today = now().date()
    today_orders = Order.objects.filter(order_taker=user, created_at__date=today).count()

    return Response({
        "total_shops_by_user": total_shops_by_user,
        "total_orders": total_orders,
        "today_orders": today_orders,
    })