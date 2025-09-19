from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem, OrderVoiceNote


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("product", "quantity", "unit_price", "get_total_price")
    readonly_fields = ("get_total_price",)

    def get_total_price(self, obj):
        return obj.get_total_price()
    get_total_price.short_description = "Total Price"


class OrderVoiceNoteInline(admin.TabularInline):
    model = OrderVoiceNote
    extra = 0
    fields = ("voice_file", "uploaded_by", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "shop",
        "order_taker",
        "colored_status",
        "payment_status",
        "subtotal",
        "total_amount",
        "created_at",
    )
    list_filter = ("status", "payment_status", "shop", "created_at")
    search_fields = ("order_number", "shop__shop_name", "order_taker__username")
    readonly_fields = ("order_id", "order_number", "subtotal", "total_amount", "created_at", "updated_at")
    inlines = [OrderItemInline, OrderVoiceNoteInline]

    def colored_status(self, obj):
        colors = {
            "pending": "orange",
            "confirmed": "blue",
            "preparing": "purple",
            "ready": "teal",
            "delivered": "green",
            "cancelled": "red",
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, "black"),
            obj.status.capitalize()
        )
    colored_status.short_description = "Status"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity", "unit_price", "get_total_price", "created_at")
    list_filter = ("shop", "created_at")
    search_fields = ("product__name", "order__order_number")

    def get_total_price(self, obj):
        return obj.get_total_price()
    get_total_price.short_description = "Total Price"


@admin.register(OrderVoiceNote)
class OrderVoiceNoteAdmin(admin.ModelAdmin):
    list_display = ("order", "shop", "voice_file", "uploaded_by", "created_at")
    list_filter = ("shop", "created_at")
    search_fields = ("order__order_number", "uploaded_by__username")
