import os
from django.urls import path
from django.http import FileResponse, Http404
from django.conf import settings
from django.contrib.auth.decorators import login_not_required
from . import views

@login_not_required
def serve_sw(request):
    """
    Serves the service worker file for PWA capabilities.
    Django's FileResponse automatically manages closing this file stream.
    """
    sw_path = os.path.join(settings.BASE_DIR, 'supermarket', 'static', 'sw.js')
    if os.path.exists(sw_path):
        return FileResponse(open(sw_path, 'rb'), content_type='application/javascript')
    raise Http404("Service Worker file not found")

urlpatterns = [
    # Main Dashboard / Landing Page
    path('', views.dashboard, name='dashboard'),

    # POS & Barcode Scanner
    path('pos/', views.pos_sale, name='pos_sale'),
    path('scan/', views.barcode_scanner, name='barcode_scanner'),
    path('barcode/lookup/', views.barcode_lookup, name='barcode_lookup'),
    path('api/quick-sale/', views.quick_sale, name='api_quick_sale'),
    path('products/<int:pk>/barcode/', views.product_barcode, name='product_barcode'),

    # Customer Chat System
    path('chat/', views.customer_chat, name='customer_chat'),
    path('customer-chats/', views.customer_chat_list, name='customer_chat_list'),
    path('customer-chats/<int:pk>/', views.customer_chat_detail, name='customer_chat_detail'),

    # Receipts & Service Worker
    path('receipts/', views.receipt_list, name='receipt_list'),
    path('receipts/<int:pk>/', views.receipt_detail, name='receipt_detail'),
    path('sw.js', serve_sw, name='sw'),
    
    # Products Management (CRUD)
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_add, name='product_add'),
    path('products/edit/<int:pk>/', views.product_edit, name='product_edit'),
    path('products/delete/<int:pk>/', views.product_delete, name='product_delete'),

    # Categories Management (CRUD)
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_add, name='category_add'),
    path('categories/edit/<int:pk>/', views.category_edit, name='category_edit'),
    path('categories/delete/<int:pk>/', views.category_delete, name='category_delete'),

    # Suppliers Management (CRUD)
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.supplier_add, name='supplier_add'),
    path('suppliers/edit/<int:pk>/', views.supplier_edit, name='supplier_edit'),
    path('suppliers/delete/<int:pk>/', views.supplier_delete, name='supplier_delete'),

    # Sales & M-Pesa Payments integration
    path('sales/', views.sale_list, name='sale_list'),
    path('sales/add/', views.sale_add, name='sale_add'),
    path('mpesa/pay/', views.send_stk_push, name='stk_push'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('mpesa/status/', views.mpesa_payment_status, name='mpesa_status'),
]