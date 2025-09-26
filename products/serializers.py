
import json
from rest_framework import serializers
from .models import Product, ProductVariant, Loose, Cotton


class LooseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loose
        fields = ["price", "discount_value", "stock","in_stock"]


class CottonSerializer(serializers.ModelSerializer):
    pieces_per_carton = serializers.IntegerField(default=0)
    no_of_cartons_history = serializers.IntegerField(default=0)
    price_per_unit = serializers.DecimalField(max_digits=8, decimal_places=2)

    

    class Meta:
        model = Cotton
        fields = ["id", "packing_unit", "price", "discount_value", "stock", "pieces_per_carton", "no_of_cartons_history","price_per_unit","in_stock"]


class ProductVariantNestedSerializer(serializers.ModelSerializer):
    loose = LooseSerializer(required=False)
    cartons = CottonSerializer(many=True, required=False)

    class Meta:
        model = ProductVariant
        fields = ["id", "size", "weight_unit", "loose", "cartons"]  
class ProductSerializer(serializers.ModelSerializer):
    allow_discounted_price = serializers.ReadOnlyField()
     
    variants = serializers.JSONField(write_only=True, required=False)  
   
    variants_data = ProductVariantNestedSerializer(source="variants", many=True, read_only=True)
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "discount_price",
            "is_active",
            "weight_kg",
            "image",
            "allow_discounted_price",
            "variants",      
            "variants_data",   
            "created_at",
            "updated_at",
            "sku"
        ]
        


class ProductSerializerForVoiceOrder(serializers.ModelSerializer):
    variants = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "variants"
        ]

    def get_variants(self, obj):
        return [
            {
                "id": v.id,
                "size": v.size,
                "weight_unit": v.weight_unit,
                "loose": {
                    "id": v.loose.id if hasattr(v, "loose") else None,
                    "price": v.loose.price if hasattr(v, "loose") else 0,
                    "discount_value": v.loose.discount_value if hasattr(v, "loose") else 0,
                    "stock": v.loose.stock if hasattr(v, "loose") else 0,
                } if hasattr(v, "loose") else None,
                "cartons": [
                    {
                        "id": c.id,
                        "packing_unit": c.packing_unit,
                        "price": c.price if c.price else 0,
                        "discount_value": c.discount_value if c.discount_value else 0,
                        "stock": c.stock,
                        "pieces_per_carton": c.pieces_per_carton,
                        # "no_of_cartons": c.no_of_cartons,
                    }
                    for c in v.cartons.all()
                ]
            }
            for v in obj.variants.all()
        ]
        
class ProductVariantSerializerCreation(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ["id", "product", "size", "weight_unit"]

    