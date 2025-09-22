from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from rest_framework.exceptions import AuthenticationFailed
from Authentication.models import  *
import random
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from .models import *
from django.utils.timezone import now
from .whatsapp_notification import send_shop_whatsapp_message


User = get_user_model()
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name","des"]
 
class ShopImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopImage
        fields = ["id", "image", "uploaded_at"]
class ShopVoiceNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopVoiceNotes    
        fields = ["id", "voice_note", "uploaded_at"]



class ShopSerializer(serializers.ModelSerializer):
    images = ShopImageSerializer(many=True, read_only=True)
    voice_notes = ShopVoiceNoteSerializer(many=True, read_only=True)

   

    class Meta:
        model = Shop
        fields = [
            "id", "shop_name", "shop_address", "slug",
            "owner_name", "owner_phone","is_whatsapp",
            "shop_image", "status",
            "latitude", "longitude", "accuracy",
            "voice_notes", "images", "created_at",
            
        ]
        

    def create(self, validated_data):
            request = self.context.get("request")
 
            latitude = validated_data.get("latitude")
            longitude = validated_data.get("longitude")
            accuracy = validated_data.get("accuracy")
            owner_phone = validated_data.get("owner_phone")
            shop_image = validated_data.get("shop_image")
            images = request.FILES.getlist("images")

  
            if not shop_image:
                raise serializers.ValidationError({"error": "Shop image is required."})
            if not images:
                raise serializers.ValidationError({"error": "Shop inside image is required."})
            if Shop.objects.filter(latitude=latitude).exists():
                raise serializers.ValidationError({"error": "A shop with this latitude already exists."})
            if Shop.objects.filter(longitude=longitude).exists():
                raise serializers.ValidationError({"error": "A shop with this longitude already exists."})
            if Shop.objects.filter(accuracy=accuracy).exists():
                raise serializers.ValidationError({"error": "A shop with this accuracy already exists."})
            if Shop.objects.filter(owner_phone=owner_phone).exists():
                raise serializers.ValidationError({"error": "A shop with this owner phone already exists."})
            

            
            shop = Shop.objects.create(registered_by=request.user, **validated_data)

          
            images = request.FILES.getlist("images")
            for img in images:
                ShopImage.objects.create(shop=shop, image=img)
            voice_notes = request.FILES.getlist("voice_notes")
            for voice in voice_notes:
                ShopVoiceNotes.objects.create(shop=shop, voice_note=voice)
            whats_app=validated_data.get("is_whatsapp")
            if whats_app:
              send_shop_whatsapp_message(shop= validated_data.get("shop_name"),address= validated_data.get("shop_address"),owner_name=validated_data.get("owner_name"),phone= validated_data.get("phone"),shop_id=shop.pk)
            

            return shop

       
    def update(self, instance, validated_data):
        import ast
        request = self.context.get("request")

      
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
 
        delete_images = request.data.get("delete_images", [])
        delete_voice_notes = request.data.get("delete_voice_notes", [])

      
        if isinstance(delete_images, str):
            try:
                delete_images = ast.literal_eval(delete_images)   
            except:
                delete_images = []
        if isinstance(delete_voice_notes, str):
            try:
                delete_voice_notes = ast.literal_eval(delete_voice_notes)
            except:
                delete_voice_notes = []

    
        if delete_images:
            instance.images.filter(id__in=delete_images).delete()
        if delete_voice_notes:
            instance.voice_notes.filter(id__in=delete_voice_notes).delete()
      
        images = request.FILES.getlist("images")
        if images:
            for img in images:   
                ShopImage.objects.create(shop=instance, image=img)

 
           

        voice_notes = request.FILES.getlist("voice_notes")
        for voice in voice_notes:
            ShopVoiceNotes.objects.create(shop=instance, voice_note=voice)

        return instance



class ShopNearBySerializer(serializers.ModelSerializer):
    images = ShopImageSerializer(many=True, required=True)
    voice_notes = ShopVoiceNoteSerializer(many=True, read_only=True)
    total_shops_by_user = serializers.SerializerMethodField()
    total_orders = serializers.SerializerMethodField()
    today_orders = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()  

    class Meta:
        model = Shop
        fields = [
            "id", "shop_name", "shop_address", "slug",
            "owner_name", "owner_phone", "shop_image", "status","is_whatsapp",
            "latitude", "longitude", "accuracy",
            "voice_notes", "images", "created_at",
            "distance",  "total_shops_by_user", "total_orders", "today_orders"
        ]
    def get_total_shops_by_user(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Shop.objects.filter(registered_by=request.user).count()
        return 0

    def get_total_orders(self, obj):
        return obj.shop_orders.count()

    def get_today_orders(self, obj):
        today = now().date()
        return obj.shop_orders.filter(created_at__date=today).count()

    def get_distance(self, obj):
        return getattr(obj, "distance", None)  # return distance if set
 

class SalesmanSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='staff.username')
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = StaffLocations
        fields = ['id', 'name', 'identifier', 'current_lat', 'current_lng', 'address', 'last_seen', 'image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if request and obj.staff.profile_pic:
            # This produces: http://127.0.0.1:8000/media/profiles/image_2.png
            return request.build_absolute_uri(obj.staff.profile_pic.url)
        return None
