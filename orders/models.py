from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from django.contrib.auth import get_user_model
from plants_mall_shops.models import Shop
from products.models import Product,Cotton
 
User=get_user_model()

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Pickup'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
    ]
    
    
    order_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    order_number = models.CharField(max_length=20, unique=True, blank=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='shop_orders')
    order_taker=models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    dispatcher=models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,related_name="dispatcher")
    delivery_rider=models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,related_name="delivery_rider")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    latitude = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    accuracy = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    order_pdf = models.FileField(upload_to="order_pdfs/", blank=True, null=True)
    is_voice_order=models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def save(self, *args, **kwargs):
    
        if not self.order_number:
            from django.utils import timezone
            date_str = timezone.now().strftime('%Y%m%d')
            last_order = Order.objects.filter(order_number__startswith=f'ORD-{date_str}').order_by('order_number').last()
            new_num = int(last_order.order_number.split('-')[-1]) + 1 if last_order else 1
            self.order_number = f'ORD-{date_str}-{new_num:03d}'
        
        super().save(*args, **kwargs)
        self.calculate_totals()
        super().save(update_fields=['subtotal', 'total_amount'])

    def calculate_totals(self):
        """Calculate subtotal and total amount from items"""
        subtotal = sum(item.get_total_price() for item in self.items.all())
        self.subtotal = subtotal
        self.total_amount = subtotal  

    def __str__(self):
        return f"Order {self.order_number} - {self.shop.shop_name}"

class OrderVoiceNote(models.Model):
    order = models.ForeignKey(
        "Order",
        on_delete=models.CASCADE,
        related_name="voice_notes"
    )
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='orders')
    voice_file = models.FileField(upload_to="order_voice_notes/")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True, help_text="Optional description of the voice note")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Voice note for {self.order.order_number}"

    class Meta:
        ordering = ['created_at']
        verbose_name = "Order Voice Note"
        verbose_name_plural = "Order Voice Notes"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='shops_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) 
    cotton = models.ForeignKey(Cotton, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.unit_price:
            self.unit_price = self.product.price
        super().save(*args, **kwargs)
        self.order.calculate_totals()
        self.order.save(update_fields=['subtotal', 'total_amount'])

    def get_total_price(self):
        """Return total for this item considering discount as an amount off"""
        discount = self.discount_price or 0
        unit_price = self.unit_price or 0
        final_price = Decimal(unit_price) - Decimal(discount)
        if final_price < 0:
            final_price = 0
        return final_price * (self.quantity or 0)


    def __str__(self):
        return f"{self.quantity}x {self.product.name} - Rs {self.get_total_price()}"