from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import *

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")  
    search_fields = ("name",)              
    prepopulated_fields = {"slug": ("name",)}  


class ShopImageInline(admin.TabularInline):
    model = ShopImage
    extra = 1   

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = (
        "shop_name", "category", "size", "owner_name"
        , "created_at", "registered_by_username"
    )
    list_filter = ("size", "category")
    search_fields = ("shop_name", "owner_name", "owner_phone")
    inlines = [ShopImageInline]  

    def registered_by_username(self, obj):
        return obj.registered_by.username
    registered_by_username.short_description = "Registered By"

@admin.register(ShopImage)
class ShopImageAdmin(admin.ModelAdmin):
    list_display = ("id", "shop", "image", "uploaded_at")
    
admin.site.register(ShopVoiceNotes)
admin.site.register(ShopSettings)
admin.site.register(StaffLocations)
admin.site.register(CompetitorImage)
    
 