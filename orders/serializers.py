from rest_framework import serializers
from .models import Order, OrderItem, OrderVoiceNote
from products.models import Product, Cotton
from rest_framework.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal
from django.db import transaction
from rest_framework.exceptions import ValidationError
from decimal import Decimal
from django.db.models import Q
from django.utils.timezone import now
from .whatsapp import send_order
import random
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth import get_user_model
 
 
User=get_user_model()
from django.template.loader import render_to_string
class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    cotton_packing_unit = serializers.CharField(source="cotton.packing_unit", read_only=True)
    cotton_price = serializers.DecimalField(source="cotton.price", max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "cotton", "cotton_packing_unit", "cotton_price", "quantity", "unit_price","discount_price"]


class OrderVoiceNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderVoiceNote
        fields = ["id", "voice_file", "created_at"]




class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    voice_notes = OrderVoiceNoteSerializer(many=True, read_only=True)

    items_data = serializers.JSONField(write_only=True, required=True)
    voice_notes_data = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )
    shop_name=serializers.CharField(source="shop.shop_name",read_only=True)
    order_taker_name=serializers.CharField(source="order_taker.name",read_only=True)
    dispatcher_name=serializers.CharField(source="dispatcher.name",read_only=True)
    delivery_rider_name=serializers.CharField(source="delivery_rider.name",read_only=True)
    

    class Meta:
        model = Order
        fields = [
            "id", "order_id", "order_number", "shop","shop_name", "order_taker","order_taker_name",
            "status", "payment_status", "subtotal", "total_amount","dispatcher","delivery_rider","delivery_rider_name","dispatcher_name",
            "items", "voice_notes","latitude", "longitude", "accuracy",
            "items_data", "voice_notes_data",
            "created_at", "updated_at"
        ]
        read_only_fields = ("order_id", "order_number", "subtotal", "total_amount","order_taker")

    def create(self, validated_data):
        items_data = validated_data.pop("items_data", [])
        voice_files = validated_data.pop("voice_notes_data", [])
        is_voice_order = validated_data.pop("is_voice_order", False)
        request = self.context.get("request")   
        user = request.user  

        if not items_data:
            raise ValidationError({"items_data": "At least one item is required to create an order."})

        with transaction.atomic():
            order = Order.objects.create(**validated_data, order_taker=request.user)

            for item in items_data:
                
                product = None
                if is_voice_order or isinstance(item.get("product"), str):
                    product_name = item.get("product")
                    if not product_name:
                        raise ValidationError({"product": "Product name is required for voice orders."})
                    product = Product.objects.filter(name__iexact=product_name).first()
                    if not product:
                        raise ValidationError({"product": f"No product found matching '{product_name}'"})
                else:
                    try:
                        product = Product.objects.get(id=item["product"])
                    except Product.DoesNotExist:
                        raise ValidationError({"product": f"Invalid product id {item['product']}"})

               
                packing_unit = item.get("cotton_packing_unit")
                cotton_qs = product.cottons.filter(packing_unit=packing_unit, stock__gt=0).order_by("id")
                if not cotton_qs.exists():
                    raise ValidationError({
                        "cotton_packing_unit": (
                            f"No Cotton variant found for product '{product.name}' "
                            f"with packing unit '{packing_unit}'"
                        )
                    })

            
                remaining_qty = int(item["quantity"])
                requested_discount_price = item.get("discount_price")
                for cotton in cotton_qs:
                    if remaining_qty <= 0:
                        break

                    deduct = min(cotton.stock, remaining_qty)
                    cotton.stock -= deduct
                    cotton.sold_quantity += deduct
                    cotton.save(update_fields=["stock", "sold_quantity"])

                    
                    discount_price = None
                    if requested_discount_price:
                        requested_discount_price = Decimal(str(requested_discount_price))
                        if requested_discount_price <= cotton.price:
                            discount_price = requested_discount_price
                        else:
                            raise ValidationError({
                                "discount_price": f"Discount {requested_discount_price} > base {cotton.price}"
                            })

                  
                    OrderItem.objects.create(
                        order=order,
                        shop=order.shop,
                        product=product,
                        cotton=cotton,
                        quantity=deduct,
                        unit_price=cotton.price,
                        discount_price=discount_price,
                    )

                    remaining_qty -= deduct

                if remaining_qty > 0:
                    raise ValidationError({
                        "stock": f"Not enough stock for {product.name} ({packing_unit}). "
                                f"Requested {item['quantity']}, could only fulfill {item['quantity'] - remaining_qty}"
                    })

           
            for file in voice_files:
                OrderVoiceNote.objects.create(order=order, shop=order.shop, voice_file=file)

            admin_phone=User.objects.get(role="admin")
            
            order.calculate_totals()
            context = {
                    "order": {
                        "order_number": order.order_number,
                        "shop_name": order.shop.shop_name,
                        "owner_phone_number":order.shop.owner_phone,
                        "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        "order_taker": user.name,
                        "payment_status": order.payment_status,
                        "total_amount": order.total_amount,
                        "subtotal": order.subtotal,
                        "items": [
                    {
                        "product_name": item.product.name,
                        "cotton_packing_unit": item.cotton.packing_unit if item.cotton else None,
                        "quantity": item.quantity,
                        "unit_price": item.unit_price,
                        "discount_price": item.discount_price,
                    }
                    for item in order.items.select_related("product", "cotton")
                ],
                                    }
                }
            print(list(order.items.values()))
            subject = "Order Confirmation Email"
            from_email = settings.EMAIL_HOST_USER
            to = ["xopal99657@kwifa.com"]
            html_content = render_to_string(
            "emails/order.html",context
    )

 
            msg = EmailMultiAlternatives(subject, "", from_email, to)
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            print("email send")
            if order.shop.is_whatsapp:
              send_order(order=context["order"],is_whatsapp=True,phone=admin_phone.phone)
            else:
                send_order(order=context["order"],is_whatsapp=False)
            print("order send")
            

            

            return order



    def update(self, instance, validated_data):
        request = self.context.get("request")
        user = request.user if request else None
        role = getattr(user, "role", None)

        items_data = validated_data.pop("items_data", None)
        voice_files = validated_data.pop("voice_notes_data", None)
        dispatcher = validated_data.pop("dispatcher", None)

        old_status = instance.status
        new_status = validated_data.get("status", old_status)
        new_payment_status = validated_data.get("payment_status", instance.payment_status)
                         

      
        if role == "admin":
            if dispatcher:
                instance.dispatcher = dispatcher
                instance.save(update_fields=["dispatcher"])
        elif role == "dispatcher":
            if new_status not in ["preparing", "ready"]:
                raise ValidationError(
                    {"status": "Dispatcher can only set status to 'preparing' or 'ready'."}
                )
        elif role == "delivery_rider":
            if new_status and new_status != "delivered":
                raise ValidationError(
                    {"status": "Delivery rider can only set status to 'delivered'."}
                )
            if not new_payment_status and "payment_status" in validated_data:
                raise ValidationError(
                    {"payment_status": "Delivery rider can only update payment_status."}
                )
        else:
            raise ValidationError({"role": "You are not allowed to update this order."})

  
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

    
        if new_status == "confirmed" and dispatcher:
            instance.dispatcher = dispatcher
            instance.save(update_fields=["dispatcher"])
 
        if items_data is not None:
            instance.items.all().delete()
            for item in items_data:
                product = Product.objects.get(id=item["product"])
                packing_unit = item["cotton_packing_unit"]

                cotton_qs = product.cottons.filter(
                    packing_unit=packing_unit, stock__gt=0
                ).order_by("id")

                if not cotton_qs.exists():
                    raise ValidationError({
                        "cotton_packing_unit": (
                            f"No Cotton variant found for product '{product.name}' "
                            f"with packing unit '{packing_unit}'"
                        )
                    })

                remaining_qty = int(item["quantity"])

                for cotton in cotton_qs:
                    if remaining_qty <= 0:
                        break

                    deduct = min(cotton.stock, remaining_qty)
                    cotton.stock -= deduct
                    cotton.sold_quantity += deduct
                    cotton.save(update_fields=["stock", "sold_quantity"])

                    OrderItem.objects.create(
                        order=instance,
                        shop=instance.shop,
                        product=product,
                        cotton=cotton,
                        quantity=deduct,
                        unit_price=cotton.price,
                    )
                    remaining_qty -= deduct

                if remaining_qty > 0:
                    raise ValidationError({
                        "stock": f"Not enough stock for {product.name} ({packing_unit}). "
                                f"Requested {item['quantity']}, could only fulfill {int(item['quantity']) - remaining_qty}"
                    })

    
        if voice_files is not None:
            for file in voice_files:
                OrderVoiceNote.objects.create(
                    order=instance,
                    shop=instance.shop,
                    voice_file=file
                )

        # ✅ Recalculate totals
        instance.calculate_totals()
        instance.save(update_fields=["subtotal", "total_amount"])
        return instance
