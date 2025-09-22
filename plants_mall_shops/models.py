 
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
import random
from django.utils.text import slugify

User=get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=160, unique=True, blank=True)

    def save(self, *args, **kwargs):
     
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Shop(models.Model):
    SIZE_CHOICES = (
        ("small", "Small"),
        ("medium", "Medium"),
        ("large", "Large"),
    )
    SHOP_STATUS = (
        ("open", "Open"),
        ("close", "Close"),
    )
    registered_by=models.ForeignKey(User,related_name="sales_man_shops",on_delete=models.CASCADE, null=True, blank=True)
    shop_name = models.CharField(max_length=200)
    shop_address=models.CharField(max_length=300,blank=True,null=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
     
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="shops",blank=True, null=True)
    
    size = models.CharField(max_length=20, choices=SIZE_CHOICES,default="medium")
    
    owner_name = models.CharField(max_length=150,blank=True, null=True)
    
    owner_phone = models.CharField(max_length=20)
    is_whatsapp=models.BooleanField(default=True)
    
    shop_image = models.ImageField(upload_to="media/shop",null=True, blank=True)
    status=models.CharField(choices=SHOP_STATUS,default="open",max_length=100)
    latitude = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    accuracy = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)

     
     

    created_at = models.DateTimeField(auto_now_add=True)
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.shop_name)
            slug = base_slug
            counter = 1
            while Shop.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.shop_name}"

 
class ShopVoiceNotes(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="voice_notes")
    voice_note = models.FileField(upload_to="media/shops_register_voice_note")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.shop.shop_name}"
class ShopImage(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="media/shops_images")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.shop.shop_name}"

class ShopSettings(models.Model):
    radius_meters = models.FloatField(default=5000.0, help_text="Radius in meters to show nearby shops")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Shop Settings (Radius: {self.radius_meters} m)"

class StaffLocations(models.Model):
    staff = models.ForeignKey(User, on_delete=models.CASCADE, related_name="location_tracker",null=True, blank=True)
    identifier = models.CharField(max_length=200, unique=True)
    current_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    address = models.CharField(max_length=500, null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.identifier}"