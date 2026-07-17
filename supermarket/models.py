from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from io import BytesIO
import barcode
from barcode.writer import ImageWriter


# ─────────────────────────────────────────
# CATEGORY
# ─────────────────────────────────────────
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


# ─────────────────────────────────────────
# SUPPLIER
# ─────────────────────────────────────────
class Supplier(models.Model):
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ─────────────────────────────────────────
# PRODUCT
# ─────────────────────────────────────────
class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True)
    barcode_number = models.CharField(max_length=100, blank=True, null=True)
    barcode_image = models.ImageField(upload_to='barcodes/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock_quantity = models.IntegerField(default=0)
    reorder_level = models.IntegerField(default=10)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.reorder_level

    def _generate_barcode_image(self, barcode_value):
        sanitized = slugify(f"product-{self.pk}-{barcode_value}") or str(self.pk)
        file_name = f"{sanitized}.png"

        barcode_class = barcode.get_barcode_class('code128')
        writer = ImageWriter()
        barcode_obj = barcode_class(barcode_value, writer=writer)

        buffer = BytesIO()
        barcode_obj.write(
            buffer,
            {
                'module_width': 0.4,
                'module_height': 15.0,
                'font_size': 12,
                'text_distance': 1.0,
                'quiet_zone': 2.0,
            }
        )
        buffer.seek(0)

        self.barcode_image.save(file_name, ContentFile(buffer.read()), save=False)
        buffer.close()

    def save(self, *args, **kwargs):
        barcode_value = self.barcode_number or self.sku
        if barcode_value and not self.barcode_number:
            self.barcode_number = barcode_value

        should_generate_image = bool(barcode_value)

        if not self.pk:
            super().save(*args, **kwargs)

        if should_generate_image:
            expected_file_name = f"product-{self.pk}-{slugify(barcode_value)}.png"
            has_changed_image = not self.barcode_image or self.barcode_image.name != f"barcodes/{expected_file_name}"
            if has_changed_image:
                self._generate_barcode_image(barcode_value)
                super().save(update_fields=['barcode_image'])
            else:
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)


# ─────────────────────────────────────────
# SALE
# ─────────────────────────────────────────
class Sale(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sales')
    quantity_sold = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    cashier = models.CharField(max_length=100, blank=True, null=True)
    sale_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        self.total_amount = self.unit_price * self.quantity_sold
        if not self.pk:
            self.product.stock_quantity -= self.quantity_sold
            self.product.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x{self.quantity_sold} on {self.sale_date.strftime('%Y-%m-%d')}"


# ─────────────────────────────────────────
# RECEIPT
# ─────────────────────────────────────────
class Receipt(models.Model):
    receipt_number = models.CharField(max_length=50, unique=True)
    cashier = models.CharField(max_length=100, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    change_given = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.receipt_number


# ─────────────────────────────────────────
# RECEIPT ITEM
# ─────────────────────────────────────────
class ReceiptItem(models.Model):
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"


# ─────────────────────────────────────────
# CUSTOMER CHAT
# ─────────────────────────────────────────
class CustomerChat(models.Model):
    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_RESPONDED = 'responded'
    STATUS_CHOICES = [
        (STATUS_NEW, 'New'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_RESPONDED, 'Responded'),
    ]

    customer_name = models.CharField(max_length=120)
    customer_email = models.EmailField(blank=True, null=True)
    customer_phone = models.CharField(max_length=30, blank=True, null=True)
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='customer_chats')
    subject = models.CharField(max_length=200, blank=True, null=True)
    message = models.TextField()
    manager_response = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Chat from {self.customer_name} - {self.subject or 'Order request'}"


# ─────────────────────────────────────────
# MPESA TRANSACTION
# ─────────────────────────────────────────
class MpesaTransaction(models.Model):
    phone_number = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    mpesa_code = models.CharField(max_length=50)
    checkout_request_id = models.CharField(max_length=100, blank=True, null=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    is_successful = models.BooleanField(default=False)
    is_failed = models.BooleanField(default=False)  # Added to prevent errors in views.py check

    def __str__(self):
        return f"{self.mpesa_code} - KES {self.amount}"


# ─────────────────────────────────────────
# MPESA PAYMENT (linking to receipt)
# ─────────────────────────────────────────
class MpesaPayment(models.Model):
    receipt = models.ForeignKey(Receipt, on_delete=models.SET_NULL, null=True, blank=True)
    transaction = models.ForeignKey(MpesaTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"MpesaPayment #{self.pk}"