from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import *
from .serializers import *
from plants_mall_shops.permissions import IsSalesManOrAdmin
 
from rest_framework.pagination import PageNumberPagination
from rest_framework import viewsets, permissions, status
from django.shortcuts import get_object_or_404
import json
from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

from .models import Product, ProductVariant, Loose, Cotton
from .serializers import ProductSerializer
class ProductPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

from django.db import transaction
class ProductListCreateAPIView(generics.ListCreateAPIView):
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated,IsSalesManOrAdmin]   
    pagination_class = ProductPagination

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                "message": "Products retrieved successfully",
                "results": serializer.data
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "message": "Products retrieved successfully",
            "results": serializer.data
        }, status=status.HTTP_200_OK)

 
class ProductRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"
    pagination_class=True

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "message": "Product updated successfully",
            "product": serializer.data
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            "message": "Product deleted successfully"
        }, status=status.HTTP_200_OK)
class ProductListForAi(generics.ListAPIView):
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProductSerializerForVoiceOrder
    permission_classes = [permissions.AllowAny]   
    pagination_class = None 
 




def parse_variants(data):
    variants = data.pop("variants", [])

 
    if isinstance(variants, str):
        try:
            variants = json.loads(variants)
        except json.JSONDecodeError:
            return []

   
    if isinstance(variants, list) and len(variants) == 1 and isinstance(variants[0], str):
        try:
            variants = json.loads(variants[0])
        except json.JSONDecodeError:
            return []
 
    if isinstance(variants, dict):
        variants = [variants]

    if not isinstance(variants, list):
        return []

    return variants




from django.db import transaction

@api_view(["POST"])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def create_product(request):
    data = request.data
    variants_data = parse_variants(data)

    if not variants_data:
        return Response(
            {"variants": "At least one variant is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    product_serializer = ProductSerializer(data=data, context={"request": request})

    if not product_serializer.is_valid():
        return Response(product_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
          
            product = product_serializer.save()

            for v in variants_data:
                if isinstance(v, str):
                    try:
                        v = json.loads(v)
                    except json.JSONDecodeError:
                        raise serializers.ValidationError({"variants": "Invalid variant format."})

                if not isinstance(v, dict):
                    raise serializers.ValidationError({"variants": "Invalid variant format."})

                loose_data = v.pop("loose", None)
                cartons_data = v.pop("cartons", [])

               
                variant = ProductVariant.objects.create(product=product, **v)

                
                if loose_data:
                    if isinstance(loose_data, str):
                        try:
                            loose_data = json.loads(loose_data)
                        except json.JSONDecodeError:
                            loose_data = None
                    if isinstance(loose_data, dict):
                        Loose.objects.create(variant=variant, **loose_data)

               
                if isinstance(cartons_data, str):
                    try:
                        cartons_data = json.loads(cartons_data)
                    except json.JSONDecodeError:
                        cartons_data = []

                if isinstance(cartons_data, dict):
                    cartons_data = [cartons_data]

                if isinstance(cartons_data, list):
                    for c in cartons_data:
                        if isinstance(c, str):
                            try:
                                c = json.loads(c)
                            except json.JSONDecodeError:
                                continue
                        if not isinstance(c, dict):
                            continue
                        Cotton.objects.create(product=product, variant=variant, **c)

    except Exception as e:
        return Response(
            {"error": f"Product creation failed: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        ProductSerializer(product, context={"request": request}).data,
        status=status.HTTP_201_CREATED,
    )

@api_view(["PUT", "PATCH"])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def update_product(request, pk):
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

    data = request.data.copy()
    variants_data = parse_variants(data)

    if not variants_data:
        return Response({"variants": "At least one variant is required."}, status=status.HTTP_400_BAD_REQUEST)

    product_serializer = ProductSerializer(product, data=data, partial=True)
    if product_serializer.is_valid():
        product_serializer.save()
        new_variant_ids = []

        for v in variants_data:
           
            if isinstance(v, str):
                try:
                    v = json.loads(v)
                except json.JSONDecodeError:
                    return Response({"variants": "Invalid variant format."}, status=status.HTTP_400_BAD_REQUEST)

            if isinstance(v, list) and len(v) > 0:
                v = v[0]

            if not isinstance(v, dict):
                return Response({"variants": "Invalid variant format."}, status=status.HTTP_400_BAD_REQUEST)

            
            variant_id = v.get("id")
            loose_data = v.pop("loose", None)
            cartons_data = v.pop("cartons", [])
            delete_flag = v.pop("delete", False)   

            if isinstance(loose_data, str):
                loose_data = json.loads(loose_data)
            if isinstance(cartons_data, str):
                cartons_data = json.loads(cartons_data)

         
            if variant_id:
                try:
                    variant = ProductVariant.objects.get(id=variant_id, product=product)
                except ProductVariant.DoesNotExist:
                    return Response({"variant": f"Invalid variant id {variant_id}"}, status=status.HTTP_400_BAD_REQUEST)

                if delete_flag:  
                    variant.delete()
                    continue  

                for attr, value in v.items():
                    setattr(variant, attr, value)
                variant.save()
            else:
                variant = ProductVariant.objects.create(product=product, **v)

            new_variant_ids.append(variant.id)

    
            if loose_data:
                if hasattr(variant, "loose"):
                    loose = variant.loose
                    for attr, value in loose_data.items():
                        setattr(loose, attr, value)
                    loose.save()
                else:
                    Loose.objects.create(variant=variant, **loose_data)

   
            existing_cottons = {c.id: c for c in variant.cartons.all()}
            new_cotton_ids = []

            for c in cartons_data:
                if isinstance(c, str):
                    c = json.loads(c)

                if not isinstance(c, dict):
                    continue

                cotton_id = c.get("id")
                if cotton_id and cotton_id in existing_cottons:
                    cotton = existing_cottons[cotton_id]
                    for attr, value in c.items():
                        if attr != "id":
                            setattr(cotton, attr, value)
                    cotton.save()
                else:
                    cotton = Cotton.objects.create(product=product, variant=variant, **c)

                new_cotton_ids.append(cotton.id)

         
            variant.cartons.exclude(id__in=new_cotton_ids).delete()
 

        return Response(ProductSerializer(product).data, status=status.HTTP_200_OK)

    return Response(product_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
@api_view(["GET"])
def list_products(request):
  
    products = Product.objects.filter(is_active=True).order_by("-created_at")

    paginator = ProductPagination()
    paginated_products = paginator.paginate_queryset(products, request)

    serializer = ProductSerializer(
        paginated_products, many=True, context={'request': request}
    )
    return paginator.get_paginated_response(serializer.data)

@api_view(["GET"])
def retrieve_product(request, pk):
    """Get product by ID"""
    try:
        product = Product.objects.get(pk=pk)
        
    except Product.DoesNotExist:
        return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = ProductSerializer(product, context={"request": request})
    return Response(serializer.data, status=status.HTTP_200_OK)