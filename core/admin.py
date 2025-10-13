from django.contrib import admin
from .models import Product, Order, License, CHAUFFEcoinTransaction, UserProfile


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'chauffecoins_included', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('-created_at',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'quantity', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'user__email', 'product__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ('license_number', 'user', 'controller_name', 'status', 'issued_at')
    list_filter = ('status', 'issued_at')
    search_fields = ('license_number', 'user__username', 'controller_name', 'first_name', 'last_name')
    readonly_fields = ('id', 'license_number', 'issued_at')
    ordering = ('-issued_at',)


@admin.register(CHAUFFEcoinTransaction)
class CHAUFFEcoinTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'amount', 'description', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('user__username', 'description')
    readonly_fields = ('id', 'created_at')
    ordering = ('-created_at',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'chauffecoins_balance', 'total_licenses_purchased', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
