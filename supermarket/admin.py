from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Product, 
    Category, 
    Supplier, 
    Sale, 
    Receipt, 
    ReceiptItem, 
    CustomerChat, 
    MpesaTransaction, 
    MpesaPayment
)

# ─────────────────────────────────────────
# REBRANDING THE DJANGO ADMIN HEADER
# ─────────────────────────────────────────
admin.site.site_header = "Apex Provisions Administration"
admin.site.site_title = "Apex Provisions Portal"
admin.site.index_title = "Welcome to the Apex Provisions Management Console"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'phone', 'email', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'contact_person']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'barcode_number', 'barcode_preview', 'category', 'price', 'stock_quantity', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'sku', 'barcode_number']
    readonly_fields = ['barcode_preview']

    def barcode_preview(self, obj):
        if obj.barcode_image:
            return format_html('<img src="{}" style="height:40px;width:auto;" />', obj.barcode_image.url)
        return '-'
    barcode_preview.short_description = 'Barcode'


@admin.register(CustomerChat)
class CustomerChatAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'customer_phone', 'customer_email', 'product', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['customer_name', 'customer_phone', 'customer_email', 'subject', 'message']
    readonly_fields = ['created_at', 'responded_at']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity_sold', 'unit_price', 'total_amount', 'sale_date', 'cashier']
    list_filter = ['sale_date']
    search_fields = ['product__name', 'cashier']


# ─────────────────────────────────────────
# INLINES AND TRANSACTION MODELS
# ─────────────────────────────────────────

class ReceiptItemInline(admin.TabularInline):
    model = ReceiptItem
    extra = 0
    readonly_fields = ['product', 'product_name', 'quantity', 'unit_price', 'subtotal']
    can_delete = False


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'cashier', 'total_amount', 'grand_total', 'amount_paid', 'change_given', 'created_at']
    list_filter = ['created_at', 'cashier']
    search_fields = ['receipt_number', 'cashier']
    inlines = [ReceiptItemInline]


@admin.register(MpesaTransaction)
class MpesaTransactionAdmin(admin.ModelAdmin):
    list_display = ['mpesa_code', 'phone_number', 'amount', 'is_successful', 'is_failed', 'transaction_date', 'checkout_request_id']
    list_filter = ['is_successful', 'is_failed', 'transaction_date']
    search_fields = ['mpesa_code', 'phone_number', 'checkout_request_id']
    readonly_fields = ['transaction_date']


@admin.register(MpesaPayment)
class MpesaPaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'receipt', 'transaction', 'created_at']
    list_filter = ['created_at']
    readonly_fields = ['created_at']