from rest_framework import generics, permissions
from .models import Order
from .serializers import OrderSerializer
from rest_framework.pagination import PageNumberPagination
import time
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from google import genai
import os
import tempfile
import json
import requests
from .filters import OrderFilter 
from django_filters.rest_framework import DjangoFilterBackend
from plants_mall_shops.permissions import IsSalesManOrAdmin
from products.models import Product
from products.serializers import ProductSerializerForVoiceOrder
class OrderPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class OrderListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = OrderPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = OrderFilter
    def get_serializer_context(self):
         
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def get_queryset(self):
        qs = Order.objects.all().order_by("-created_at")
        user = self.request.user
        shop_id = self.request.query_params.get("shop_id")

        
        if user.role == "dispatcher":
            qs = qs.filter(dispatcher=user)
        elif user.role == "delivery_rider":
            qs = qs.filter(delivery_rider=user,status__in=["ready","delivered"])
        elif user.role == "sales_man":
            qs = qs.filter(order_taker=user)
        if shop_id:
            qs = qs.filter(shop_id=shop_id)

        return qs


class OrderRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'



class SpeechToTextAPIView(APIView):
    permission_classes=[permissions.IsAuthenticated,IsSalesManOrAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get("file")
        products = Product.objects.all()
        serializer = ProductSerializerForVoiceOrder(products, many=True)
        d = serializer.data   
        if not file_obj:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            client = genai.Client(api_key="AIzaSyDVAMbAK_CvTwjQM5CJP9sADPZYcjHLk9U")
            start_time = time.time()

           
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_obj.name)[-1]) as temp_file:
                for chunk in file_obj.chunks():
                    temp_file.write(chunk)
                temp_path = temp_file.name

            
            myfile = client.files.upload(file=temp_path)

            response = client.models.generate_content(
            model="gemini-2.0-flash", contents=[f"""If there are no product names mentioned in the audio:
                                                You need to follow this structure for the final response:
                                                    [
                                                    {{
                                                    "message":"The Audio has no information about the Products"
                                                    }}
                                                    ]
                                            If there are products mentioned in the audio:
                                                Listen carefully to the audio first and then translate this audio into English efficiently and provide details only about the product name, product quantity, weight and its discount price.                                            
                                                Product name should be extracted from the audio precisely and keep the first alphabet of product name capital.
                                                Product quantity should be extracted precisely from the audio.
                                                Product name should always be in English language.
                                                If the audio doesn't contain information about the number of kilos, only kilo/s is mentioned in the audio, consider it as 1 kg.
                                                If the audio contains information about the carton for the specific product, keep is_carton true and include another field as "carton_id" with respective carton ID for that specific product only. If the audio doesn't contain information about carton for the specfic product, keep is_carton false for that specific product only.
                                                If the weight is mentioned in the audio with respect to kilos, the unit of weight should be kg. If the weight is mentioned is grams, the unit of weight should be g.
                                                If the Product name is not available in this list of dictionaries containing product name, its id and packing unit: {d}, still follow the below-given structure. 
                                                You need to get id, quantity, price of the respective product and variant id, carton id, variant size, weight unit and discount_value of its variant from this list of dictionaries containing product name, its respective id and respective packing unit: {d}  
                                                
                                                    You need to follow this structure for all the products mentioned in the audio:
                                                        [{{
                                                            "product": Product ID (integer),
                                                            "price":Product Price (integer),
                                                            "product_name":Product Name,
                                                            "variant": Variant ID (integer),
                                                            "is_carton": true or false,
                                                            "carton_id": Carton ID (integer),
                                                            "quantity": Product quantity,
                                                            "discount_price": Discount Value (integer),
                                                            "variant_size":Variant Size + Variant Weight Unit
                                                        }}]
                                                        If the audio file doesn't contain value for any field, just keep the value for that field as "".
                                            
                                            
                                            """, myfile]
    )
            end_time = time.time()
            print(f"Time taken: {end_time - start_time:.2f} sec")
            print(response.text.replace("```json","").replace("```",""))
            req = response.text.replace("```json","").replace("```","").replace("\n","").strip()
            product_ids = [p.get('id') for p in d]
            req = json.loads(req)
            for product in req:
                if product.get('carton_id') == "":
                    product.pop('carton_id')
                if product.get('is_carton') == False:
                    product["is_carton"] = "false"
                if product.get('is_carton') == True:
                    product["is_carton"] = "true"
                if product.get('product') not in product_ids and product.get('message') == "The Audio has no information about the Products":
                    product['message'] = "The Audio has no information about the Products"
                elif product.get('product') not in product_ids:
                    product["message"] = "This Product is not available at The Plants Mall"
                    
                    end_time = time.time()
             
          

           
            os.remove(temp_path)
            print(req)
            return Response({
                "time_taken_sec": round(end_time - start_time, 2),
                "results": req
            })

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
