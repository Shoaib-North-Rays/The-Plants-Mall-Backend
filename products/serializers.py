
from .models import *
from rest_framework import serializers
from .models import Product,Cotton
from rest_framework import serializers
from .models import Product, Cotton
import json
from rest_framework import serializers
from .models import Product, Cotton


class CottonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cotton
        fields = ["id", "packing_unit", "price", "stock"]

class ProductSerializer(serializers.ModelSerializer):
    allow_discounted_price = serializers.ReadOnlyField()
    cottons = CottonSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "description", "price", "discount_price",
            "tax_percentage", "stock", "sku", "is_active",
            "weight_kg", "image", "allow_discounted_price",
            "created_at", "updated_at", "cottons"
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        cottons_data = request.data.get("cottons")  # comes as text in form-data

        product = Product.objects.create(**validated_data)

        if cottons_data:
            try:
                cottons = json.loads(cottons_data)  
                for c in cottons:
                    Cotton.objects.create(
                        product=product,
                        packing_unit=c.get("packing_unit"),
                        price=c.get("price"),
                        stock=c.get("stock")
                    )
            except json.JSONDecodeError:
                raise serializers.ValidationError({"cottons": "Invalid JSON format"})

        return product

    def update(self, instance, validated_data):
        request = self.context.get("request")
        cottons_data = request.data.get("cottons")

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if cottons_data:
            try:
                cottons = json.loads(cottons_data)
                instance.cottons.all().delete()
                for c in cottons:
                    Cotton.objects.create(
                        product=instance,
                        packing_unit=c.get("packing_unit"),
                        price=c.get("price"),
                        stock=c.get("stock")
                    )
            except json.JSONDecodeError:
                raise serializers.ValidationError({"cottons": "Invalid JSON format"})

        return instance



class ProductSerializerForVoiceOrder(serializers.ModelSerializer):
    cottons = serializers.SerializerMethodField(read_only=True) 
    
    class Meta:
        model = Product
        fields = [
            "id", "name","cottons"
        ]
    def get_cottons(self, obj):
            return [
                {
                    
                    "packing_unit": c.packing_unit,
                    "price":c.price if c.price else 0,
                }
                for c in obj.cottons.all()
            ]