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
from products.models import ProductVariant
 
User=get_user_model()
from django.template.loader import render_to_string
class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    cotton_packing_unit = serializers.CharField(source="cotton.packing_unit", read_only=True)
    cotton_price = serializers.DecimalField(source="cotton.price", max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "cotton", "cotton_packing_unit", "cotton_price", "quantity", "unit_price","discount_price","loose","variant"]


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
    shop_name = serializers.CharField(source="shop.shop_name", read_only=True)
    order_taker_name = serializers.CharField(source="order_taker.name", read_only=True)
    dispatcher_name = serializers.CharField(source="dispatcher.name", read_only=True)
    delivery_rider_name = serializers.CharField(source="delivery_rider.name", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "order_id", "order_number", "shop", "shop_name",
            "order_taker", "order_taker_name",
            "status", "payment_status", "subtotal", "total_amount",
            "dispatcher", "delivery_rider", "delivery_rider_name", "dispatcher_name",
            "items", "voice_notes",
            "latitude", "longitude", "accuracy",
            "items_data", "voice_notes_data",
            "created_at", "updated_at"
        ]
        read_only_fields = ("order_id", "order_number", "subtotal", "total_amount", "order_taker")
    def create(self, validated_data):
        items_data = validated_data.pop("items_data", [])
        voice_files = validated_data.pop("voice_notes_data", [])
        is_voice_order = validated_data.pop("is_voice_order", False)
        request = self.context.get("request")
        user = request.user

        if not items_data:
            raise ValidationError({"items_data": "At least one item is required to create an order."})

        with transaction.atomic():
            order = Order.objects.create(**validated_data, order_taker=user)

            for item in items_data:
                # --- Find product ---
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

                # --- Find variant ---
                variant_id = item.get("variant")
                try:
                    variant = ProductVariant.objects.get(id=variant_id, product=product)
                except ProductVariant.DoesNotExist:
                    raise ValidationError({"variant": f"Invalid variant id {variant_id} for {product.name}"})

                # --- Loose or carton? ---
                is_carton = item.get("is_carton", False)
                stock_obj = None
                stock_type = None

                if is_carton:
                    # Deduct from a carton (cotton) inside this variant
                    cotton_id = item.get("carton_id")
                    if cotton_id:
                        try:
                            stock_obj = variant.cartons.get(id=cotton_id, stock__gt=0)
                        except Cotton.DoesNotExist:
                            raise ValidationError({
                                "cotton": f"No carton found for variant {variant.size} with id={cotton_id}"
                            })
                    else:
                        raise ValidationError({"cotton": "Carton id is required when is_carton=True"})
                    stock_type = "carton"
                else:
                    # Deduct from loose stock inside this variant
                    if not hasattr(variant, "loose"):
                        raise ValidationError({
                            "loose": f"No loose stock found for variant {variant.size}"
                        })
                    stock_obj = variant.loose
                    stock_type = "loose"

                # --- Deduct stock ---
                quantity = int(item["quantity"])
                if stock_obj.stock < quantity:
                    raise ValidationError({
                        "stock": f"Not enough stock for {product.name} ({variant.size}). "
                                f"Available {stock_obj.stock}, requested {quantity}"
                    })

                stock_obj.stock -= quantity
                stock_obj.save(update_fields=["stock"])

                # --- Discount check ---
                # discount_price = None
                # requested_discount_price = item.get("discount_price")
                # if requested_discount_price:
                #     requested_discount_price = Decimal(str(requested_discount_price))
                #     if requested_discount_price <= stock_obj.price:
                #         discount_price = requested_discount_price
                #     else:
                #         raise ValidationError({
                #             "discount_price": f"Discount {requested_discount_price} > base {stock_obj.price}"
                #         })

                # --- Create OrderItem ---
                OrderItem.objects.create(
                    order=order,
                    shop=order.shop,
                    product=product,
                    variant=variant,
                    loose=stock_obj if stock_type == "loose" else None,
                    cotton=stock_obj if stock_type == "carton" else None,
                    quantity=quantity,
                    unit_price=stock_obj.price,
                    # discount_price=discount_price,
                )

            # --- Voice notes ---
            for file in voice_files:
                OrderVoiceNote.objects.create(order=order, shop=order.shop, voice_file=file)

            # Totals
            order.calculate_totals()
            order.save(update_fields=["subtotal", "total_amount"])
            admin_phone = User.objects.get(role="admin")

            order.calculate_totals()
            context = {
    "order": {
        "order_number": order.order_number,
        "shop_name": order.shop.shop_name,
        "owner_phone_number": order.shop.owner_phone,
        "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "order_taker": user.name,
        "payment_status": order.payment_status,
        "total_amount": order.total_amount,
        "subtotal": order.subtotal,
        "items": [
            {
                "product_name": (
                    item["product"]
                    if isinstance(item["product"], str)
                    else Product.objects.get(id=item["product"]).name
                ),
                "packing_unit": item.get("_resolved", {}).get("packing_unit"),
                "quantity": item.get("quantity"),
                "unit_price": item.get("_resolved", {}).get("unit_price"),
                "discount_price": item.get("_resolved", {}).get("discount_price"),
                "stock_type": item.get("_resolved", {}).get("stock_type"),
            }
            for item in items_data
        ],
    }
}


            # send email
            subject = "Order Confirmation Email"
            from_email = settings.EMAIL_HOST_USER
            to = ["xopal99657@kwifa.com"]   
            html_content = render_to_string("emails/order.html", context)
            msg = EmailMultiAlternatives(subject, "", from_email, to)
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            # send whatsapp
            if order.shop.is_whatsapp:
                send_order(order=context["order"], is_whatsapp=True, phone=admin_phone.phone,
                           contact_name=str(order.shop.owner_name) + " " + str(order.shop.shop_name))
            else:
                send_order(order=context["order"], is_whatsapp=False, contact_name="You")


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
                raise ValidationError({"status": "Dispatcher can only set status to 'preparing' or 'ready'."})
        elif role == "delivery_rider":
            if new_status and new_status != "delivered":
                raise ValidationError({"status": "Delivery rider can only set status to 'delivered'."})
            if not new_payment_status and "payment_status" in validated_data:
                raise ValidationError({"payment_status": "Delivery rider can only update payment_status."})
        else:
            raise ValidationError({"role": "You are not allowed to update this order."})

      
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        def order_detals(order, user):
            context = {
                "order": {
                    "order_number": order.order_number,
                    "shop_name": order.shop.shop_name,
                    "owner_phone_number": order.shop.owner_phone,
                    "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "order_taker": user.name if user else "",
                    "payment_status": order.payment_status,
                    "total_amount": order.total_amount,
                    "subtotal": order.subtotal,
                    
                   
                    "items": [
                        {
                            "product_name": item.product.name,
                            "quantity": item.quantity,
                            "unit_price": item.unit_price,
                            "discount_price": item.discount_price,
                            "packing_unit": item.cotton.packing_unit if item.cotton else None,
                            "cotton": {
                                "id": item.cotton.id if item.cotton else None,
                                "sku": item.cotton.sku if item.cotton else None,
                                "packing_unit": item.cotton.packing_unit if item.cotton else None,
                                "price": item.cotton.price if item.cotton else None,
                                "stock": item.cotton.stock if item.cotton else None,
                                "sold_quantity": item.cotton.sold_quantity if item.cotton else None,
                            } if item.cotton else None,
                        }
                        for item in order.items.select_related("product", "cotton")
                    ],
                }
            }
            return context

             
     
        
 
        def send_order_email(subject, to_email, template, order, user):
            context = {
                "order": {
                    "order_number": order.order_number,
                    "shop_name": order.shop.shop_name,
                    "owner_phone_number": order.shop.owner_phone,
                    "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "order_taker": user.name if user else "",
                    "payment_status": order.payment_status,
                    "total_amount": order.total_amount,
                    "subtotal": order.subtotal,
                    
                   
                    "items": [
                        {
                            "product_name": item.product.name,
                            "quantity": item.quantity,
                            "unit_price": item.unit_price,
                            "discount_price": item.discount_price,
                            "packing_unit": item.cotton.packing_unit if item.cotton else None,
                            "cotton": {
                                "id": item.cotton.id if item.cotton else None,
                                "sku": item.cotton.sku if item.cotton else None,
                                "packing_unit": item.cotton.packing_unit if item.cotton else None,
                                "price": item.cotton.price if item.cotton else None,
                                "stock": item.cotton.stock if item.cotton else None,
                                "sold_quantity": item.cotton.sold_quantity if item.cotton else None,
                            } if item.cotton else None,
                        }
                        for item in order.items.select_related("product", "cotton")
                    ],
                }
            }

            html_content = render_to_string(template, context)
            msg = EmailMultiAlternatives(subject, "", settings.EMAIL_HOST_USER, [to_email])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
     
     
     
        if new_status == "confirmed" and dispatcher:
            send_order_email(
                subject="New Order Assigned",
                to_email=dispatcher.email,
                template="emails/dispatcher_notification.html",
                order=instance,
                user=user,
            )
        # send_order(order=order_detals(order=instance,user=user),is_whatsapp=False,contact_name=dispatcher.name,phone=dispatcher.phone,dispatcher_or_admin=True)

  
        if old_status != "ready" and new_status == "ready" and instance.delivery_rider:
            send_order_email(
                subject="Order Ready for Delivery",
                to_email=instance.delivery_rider.email,
                template="emails/delivery_rider_notification.html",
                order=instance,
                user=user,
            )
        # send_order(order=order_detals(order=instance,user=user),is_whatsapp=False,contact_name=instance.delivery_rider.phone,phone=instance.delivery_rider.phone,dispatcher_or_admin=False)
 
        if old_status != "delivered" and new_status == "delivered":
            send_order_email(
                subject="Order Delivered",
                to_email=settings.ADMIN_EMAIL, 
                template="emails/order_delivered.html",
                order=instance,
                user=user,
            )
        # send_order(order=order_detals(order=instance,user=user),is_whatsapp=False,contact_name="You",phone=dispatcher.phone,dispatcher_or_admin=True)
           
            

   
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

     
        instance.calculate_totals()
        instance.save(update_fields=["subtotal", "total_amount"])

        return instance
