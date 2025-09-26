from django.db import models
from django.contrib.auth import get_user_model
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import uuid
from django.core.files import File
User=get_user_model()
class Product(models.Model):
    user=models.ForeignKey(User,related_name="products",on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2,default=0) 
    discount_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, help_text="Optional discounted price"
    )
    tax_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.0, help_text="Tax percentage applied to this product"
    )
    stock = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=100, unique=True,blank=True, null=True)
    is_active = models.BooleanField(default=True)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=3, blank=True, null=True, help_text="Weight in kilograms")
    image = models.ImageField(upload_to="products/images/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def save(self, *args, **kwargs):
        if not self.sku:
            random_part = uuid.uuid4().hex[:4].upper()
            self.sku = f"PLM-{random_part}"

        super().save(*args, **kwargs)  
    @property
    def get_variants(self):
        """
        Return all variants of this product in a clean dictionary list
        """
        return [
            {
                "id": variant.id,
                "packing_unit": variant.packing_unit,
                "price": float(variant.price),
                "stock": variant.stock,
                "sku": variant.sku,
            }
            for variant in self.variants.all()
        ]
     

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self):
        return f"{self.name}"

    @property
    def allow_discounted_price(self):
        """Return discounted price if exists, else regular price"""
        return self.discount_price if self.discount_price else self.price
class ProductVariant(models.Model):
    SIZE_CHOICES = (
        ("g", "g"),
        ("kg", "kg"),
        ("ml", "ml"),
        ("ltr","ltr")
    )
    product = models.ForeignKey(Product, related_name="variants", on_delete=models.CASCADE)
    size = models.CharField(max_length=100, help_text="e.g. 250g, 500g, 1kg")
    weight_unit = models.CharField(choices=SIZE_CHOICES,default="g" , max_length=100,help_text="e.g. g, g, kg")
    
    
    

    def __str__(self):
        return f"{self.product.name} - {self.size}"
class Cotton(models.Model):
    product = models.ForeignKey(
        Product, related_name="cottons", on_delete=models.CASCADE
    )
    variant = models.ForeignKey(ProductVariant, related_name="cartons", on_delete=models.CASCADE,blank=True, null=True)  
    
    packing_unit = models.CharField(max_length=50, help_text="E.g., 2kg, 500gm")
    price = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True)
    stock = models.PositiveIntegerField(default=0) 
    sold_quantity = models.PositiveIntegerField(default=0)
    discount_value=models.PositiveIntegerField(default=0) 
    barcode_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    barcode_image = models.ImageField(
        upload_to="products/barcodes/", blank=True, null=True
    )
    pieces_per_carton=models.PositiveIntegerField(default=0) 
    no_of_cartons_history=models.PositiveIntegerField(default=0) 
    in_stock=models.BooleanField(default=True)

    def save(self, *args, **kwargs):
      
        if not self.sku:
            random_part = uuid.uuid4().hex[:4].upper()
            self.sku = f"COT-{self.product.id}-{random_part}"

       
        if not self.barcode_number:
            self.barcode_number = uuid.uuid4().hex[:12]

        super().save(*args, **kwargs)

       
        if not self.barcode_image:
            ean = barcode.get("code128", self.barcode_number, writer=ImageWriter())
            buffer = BytesIO()
            ean.write(buffer)
            file_name = f"barcode_{self.pk}.png"
            self.barcode_image.save(file_name, File(buffer), save=False)
            super().save(update_fields=["barcode_image"])

    def __str__(self):
        return f"{self.product.name} - {self.packing_unit} - {self.sku}"

class Loose(models.Model):
    variant = models.OneToOneField(ProductVariant, related_name="loose", on_delete=models.CASCADE,blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    in_stock=models.BooleanField(default=True)

    def __str__(self):
        return f"Loose - {self.variant.product.name}-{self.variant.size}-{self.variant.weight_unit}"