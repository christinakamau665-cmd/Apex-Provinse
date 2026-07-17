from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import models
from django.db.models import Sum, Count, Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_not_required

import json
import random
import base64

from .models import Product, Category, Supplier, Sale, Receipt, ReceiptItem, MpesaTransaction, CustomerChat
from .forms import ProductForm, CategoryForm, SupplierForm, SaleForm, CustomerChatForm
from .utils import generate_promptpay_qr, send_whatsapp_via_twilio
from django_daraja.mpesa.core import MpesaClient


# ─────────────────────────────────────────
# AUTHENTICATION — single-admin login portal
# ─────────────────────────────────────────
class BrandedLoginView(LoginView):
    """
    Apex Provisions' branded sign-in screen. Reuses Django's battle-tested
    auth handling; only the template + "remember me" session behaviour are
    customised. There is no signup/registration view anywhere in this
    project by design — accounts are provisioned manually via
    `python manage.py createsuperuser`, keeping this a single-admin tool.
    """
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        if not self.request.POST.get('remember_me'):
            # Session cookie dies when the browser closes instead of
            # persisting for SESSION_COOKIE_AGE.
            self.request.session.set_expiry(0)
        return response


# ─────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────
def dashboard(request):
    total_sales_value = Sale.objects.aggregate(total=Sum('total_amount'))['total'] or 0

    total_mpesa = MpesaTransaction.objects.filter(
        is_successful=True
    ).aggregate(total=Sum('amount'))['total'] or 0

    total_mpesa_transactions = MpesaTransaction.objects.filter(is_successful=True).count()

    recent_mpesa = MpesaTransaction.objects.filter(
        is_successful=True
    ).order_by('-transaction_date')[:5]

    active_products = Product.objects.filter(is_active=True)
    total_products = active_products.count()
    inventory_value = active_products.aggregate(
        total=Sum(models.F('price') * models.F('stock_quantity'))
    )['total'] or 0
    low_stock = active_products.filter(stock_quantity__lte=models.F('reorder_level')).count()

    recent_sales = Sale.objects.select_related('product').order_by('-sale_date')[:6]

    context = {
        'total_sales_value': total_sales_value,
        'total_mpesa': total_mpesa,
        'total_mpesa_transactions': total_mpesa_transactions,
        'recent_mpesa': recent_mpesa,
        'total_products': total_products,
        'inventory_value': inventory_value,
        'low_stock': low_stock,
        'recent_sales': recent_sales,
    }
    return render(request, 'supermarket/dashboard.html', context)


# ─────────────────────────────────────────
# BARCODE LOOKUP
# ─────────────────────────────────────────
@require_GET
def barcode_lookup(request):
    code = request.GET.get('code', request.GET.get('sku', '')).strip()
    if not code:
        return JsonResponse({'found': False, 'error': 'No barcode provided'})

    product = Product.objects.filter(
        Q(barcode_number=code) | Q(sku=code) | Q(name__icontains=code),
        is_active=True
    ).first()
    if product:
        return JsonResponse({
            'found': True,
            'id': product.pk,
            'name': product.name,
            'sku': product.sku,
            'price': str(product.price),
            'stock': product.stock_quantity,
            'category': product.category.name if product.category else ''
        })

    return JsonResponse({'found': False, 'error': f'No product found for: {code}'})


@require_POST
def quick_sale(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
        product_id = payload.get('product_id')
        quantity = int(payload.get('quantity', 1))
        cashier = payload.get('cashier', '').strip()

        if not product_id or quantity < 1:
            return JsonResponse({'success': False, 'error': 'Invalid sale data'})

        product = Product.objects.get(pk=product_id, is_active=True)
        if quantity > product.stock_quantity:
            return JsonResponse({'success': False, 'error': 'Insufficient stock available'})

        sale = Sale.objects.create(
            product=product,
            quantity_sold=quantity,
            unit_price=product.price,
            cashier=cashier,
        )

        return JsonResponse({
            'success': True,
            'product': product.name,
            'total': str(sale.total_amount),
            'remaining_stock': product.stock_quantity,
        })
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Product not found'})
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid sale payload'})
    except Exception as exc:
        return JsonResponse({'success': False, 'error': str(exc)})


def barcode_scanner(request):
    return render(request, 'supermarket/barcode_scanner.html')


# ─────────────────────────────────────────
# POS SALE
# ─────────────────────────────────────────
def pos_sale(request):
    if request.method == 'POST':
        try:
            cart = json.loads(request.POST.get('cart_data', '[]'))
            cashier = request.POST.get('cashier', '')
            amount_paid = float(request.POST.get('amount_paid', 0) or 0)
            tax_rate = float(request.POST.get('tax_rate', 0) or 0)

            if not cart:
                messages.error(request, 'Cart is empty.')
                return redirect('pos_sale')

            errors = []
            for item in cart:
                product = Product.objects.get(pk=item['product_id'])
                if int(item['quantity']) > product.stock_quantity:
                    errors.append(f"Not enough stock for {product.name} (only {product.stock_quantity} left).")
            if errors:
                for e in errors:
                    messages.error(request, e)
                return redirect('pos_sale')

            subtotal = sum(float(i['price']) * int(i['quantity']) for i in cart)
            tax_amount = round(subtotal * (tax_rate / 100), 2)
            grand_total = round(subtotal + tax_amount, 2)
            change = round(amount_paid - grand_total, 2) if amount_paid >= grand_total else 0
            now = timezone.now()

            receipt = Receipt.objects.create(
                receipt_number=f"RCP-{now.strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
                cashier=cashier, total_amount=subtotal, tax_rate=tax_rate,
                tax_amount=tax_amount, grand_total=grand_total,
                amount_paid=amount_paid, change_given=change,
            )

            for item in cart:
                product = Product.objects.get(pk=item['product_id'])
                qty = int(item['quantity'])
                price = float(item['price'])
                ReceiptItem.objects.create(
                    receipt=receipt, product=product, product_name=product.name,
                    quantity=qty, unit_price=price, subtotal=round(qty * price, 2),
                )
                Sale.objects.create(product=product, quantity_sold=qty, unit_price=price, cashier=cashier)

            return redirect(f'/receipts/{receipt.pk}/?print=thermal')

        except Exception as e:
            messages.error(request, f'Error: {e}')
            return redirect('pos_sale')

    return render(request, 'supermarket/pos_sale.html')


# ─────────────────────────────────────────
# RECEIPT
# ─────────────────────────────────────────
def receipt_detail(request, pk):
    receipt = get_object_or_404(Receipt, pk=pk)
    qr_buffer = generate_promptpay_qr(receipt.amount_paid)
    qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode()

    template_name = (
        'supermarket/receipt_thermal.html'
        if request.GET.get('print') == 'thermal'
        else 'supermarket/receipt.html'
    )

    return render(request, template_name, {
        'receipt': receipt,
        'promptpay_qr': qr_base64,
    })


def receipt_list(request):
    receipts = Receipt.objects.all().order_by('-created_at')
    total = receipts.aggregate(total=Sum('grand_total'))['total'] or 0
    return render(request, 'supermarket/receipt_list.html', {'receipts': receipts, 'total': total})


# ─────────────────────────────────────────
# CUSTOMER CHAT
# ─────────────────────────────────────────
def customer_chat(request):
    """
    Form view where customers submit inquiries.
    Populates dynamic products for selection.
    """
    initial = {}
    if request.GET.get('product'):
        try:
            initial['product'] = Product.objects.get(pk=int(request.GET.get('product')))
        except (Product.DoesNotExist, ValueError):
            pass

    if request.method == 'POST':
        customer_name = request.POST.get('customer_name')
        customer_phone = request.POST.get('customer_phone', '').strip()
        customer_email = request.POST.get('customer_email', '').strip()
        product_id = request.POST.get('product')
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message')

        product = None
        if product_id:
            try:
                product = Product.objects.get(id=product_id)
            except (Product.DoesNotExist, ValueError):
                pass

        # Save new chat
        chat = CustomerChat.objects.create(
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            product=product,
            subject=subject or "Order Inquiry",
            message=message,
            status='new'
        )
        
        # Send optional WhatsApp notifications
        if getattr(settings, 'WHATSAPP_NOTIFICATIONS_ENABLED', False):
            mgr_number = getattr(settings, 'MANAGER_WHATSAPP_NUMBER', '')
            try:
                if mgr_number:
                    mgr_msg = (f"New customer message from {chat.customer_name} "
                               f"about {chat.product.name if chat.product else 'a product'}: {chat.message}\n"
                               f"Contact: {chat.customer_phone or chat.customer_email}")
                    send_whatsapp_via_twilio(mgr_number, mgr_msg)
                    
                if getattr(settings, 'NOTIFY_CUSTOMER_ON_SUBMIT', False) and chat.customer_phone:
                    cust_msg = (f"Hi {chat.customer_name}, we've received your message about "
                                f"{chat.product.name if chat.product else 'your request'}. We'll contact you shortly.")
                    send_whatsapp_via_twilio(chat.customer_phone, cust_msg)
            except Exception:
                pass

        # SUCCESS BLOCK: Executed regardless of whether WhatsApp is enabled
        messages.success(request, 'Your message has been sent. Our manager will contact you soon.')
        return redirect('customer_chat')

    # Fetch active products so they populate the select options dropdown
    products = Product.objects.filter(is_active=True).order_by('name')

    context = {
        'products': products,
        'initial': initial
    }
    return render(request, 'supermarket/customer_chat.html', context)


def customer_chat_list(request):
    """
    Manager Inbox list view.
    """
    chats = CustomerChat.objects.all().order_by('-created_at')
    return render(request, 'supermarket/customer_chat_list.html', {'chats': chats})


def customer_chat_detail(request, pk):
    """
    Response details view with dynamic status updates.
    """
    chat = get_object_or_404(CustomerChat, pk=pk)
    
    if request.method == 'POST':
        response_text = request.POST.get('manager_response', '').strip()
        status_update = request.POST.get('status', 'responded').strip()
        
        if response_text:
            chat.manager_response = response_text
            chat.status = status_update
            chat.responded_at = timezone.now()
            chat.save()
            messages.success(request, 'Inquiry response and status updated successfully.')
            return redirect('customer_chat_list')
            
    return render(request, 'supermarket/customer_chat_detail.html', {'chat': chat})


# ─────────────────────────────────────────
# PRODUCT VIEWS
# ─────────────────────────────────────────
def product_list(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    products = Product.objects.select_related('category', 'supplier').filter(is_active=True)
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(sku__icontains=query) | Q(barcode_number__icontains=query)
        )
    if category_id:
        products = products.filter(category_id=category_id)
    categories = Category.objects.all()
    return render(request, 'supermarket/product_list.html', {
        'products': products, 'categories': categories,
        'query': query, 'selected_category': category_id
    })


def product_add(request):
    form = ProductForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Product added successfully!')
        return redirect('product_list')
    return render(request, 'supermarket/product_form.html', {
        'form': form, 'title': 'Add Product', 'show_scanner': True
    })


def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)
    if form.is_valid():
        form.save()
        messages.success(request, 'Product updated successfully!')
        return redirect('product_list')
    return render(request, 'supermarket/product_form.html', {
        'form': form, 'title': 'Edit Product', 'product': product, 'show_scanner': True
    })


def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.is_active = False
        product.save()
        messages.success(request, 'Product removed!')
        return redirect('product_list')
    return render(request, 'supermarket/confirm_delete.html', {'object': product, 'type': 'Product'})


def product_barcode(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'supermarket/product_barcode.html', {'product': product})


# ─────────────────────────────────────────
# CATEGORY VIEWS
# ─────────────────────────────────────────
def category_list(request):
    categories = Category.objects.annotate(product_count=Count('products'))
    return render(request, 'supermarket/category_list.html', {'categories': categories})


def category_add(request):
    form = CategoryForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Category added!')
        return redirect('category_list')
    return render(request, 'supermarket/product_form.html', {'form': form, 'title': 'Add Category'})


def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, instance=category)
    if form.is_valid():
        form.save()
        messages.success(request, 'Category updated!')
        return redirect('category_list')
    return render(request, 'supermarket/product_form.html', {'form': form, 'title': 'Edit Category'})


def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted!')
        return redirect('category_list')
    return render(request, 'supermarket/confirm_delete.html', {'object': category, 'type': 'Category'})


# ─────────────────────────────────────────
# SUPPLIER VIEWS
# ─────────────────────────────────────────
def supplier_list(request):
    suppliers = Supplier.objects.annotate(product_count=Count('products'))
    return render(request, 'supermarket/supplier_list.html', {'suppliers': suppliers})


def supplier_add(request):
    form = SupplierForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Supplier added!')
        return redirect('supplier_list')
    return render(request, 'supermarket/product_form.html', {'form': form, 'title': 'Add Supplier'})


def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    form = SupplierForm(request.POST or None, instance=supplier)
    if form.is_valid():
        form.save()
        messages.success(request, 'Supplier updated!')
        return redirect('supplier_list')
    return render(request, 'supermarket/product_form.html', {'form': form, 'title': 'Edit Supplier'})


def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.delete()
        messages.success(request, 'Supplier deleted!')
        return redirect('supplier_list')
    return render(request, 'supermarket/confirm_delete.html', {'object': supplier, 'type': 'Supplier'})


# ─────────────────────────────────────────
# SALE VIEWS
# ─────────────────────────────────────────
def sale_list(request):
    sales = Sale.objects.select_related('product').order_by('-sale_date')
    total = sales.aggregate(total=Sum('total_amount'))['total'] or 0

    # ── Real chart data, built from the actual Sale rows in the DB ──
    from django.db.models.functions import TruncDate

    daily = (
        Sale.objects.annotate(day=TruncDate('sale_date'))
        .values('day')
        .annotate(revenue=Sum('total_amount'))
        .order_by('day')
    )
    chart_labels = [row['day'].strftime('%b %d') for row in daily if row['day']]
    chart_values = [float(row['revenue'] or 0) for row in daily if row['day']]

    top_products = (
        Sale.objects.values('product__name')
        .annotate(qty=Sum('quantity_sold'))
        .order_by('-qty')[:6]
    )
    product_labels = [row['product__name'] for row in top_products]
    product_values = [row['qty'] for row in top_products]

    context = {
        'sales': sales,
        'total': total,
        'chart_labels_json': json.dumps(chart_labels),
        'chart_values_json': json.dumps(chart_values),
        'product_labels_json': json.dumps(product_labels),
        'product_values_json': json.dumps(product_values),
        'chart_days_count': len(chart_labels),
    }
    return render(request, 'supermarket/sale_list.html', context)


def sale_add(request):
    form = SaleForm(request.POST or None)
    if form.is_valid():
        sale = form.save(commit=False)
        if sale.quantity_sold > sale.product.stock_quantity:
            messages.error(request, f'Not enough stock! Only {sale.product.stock_quantity} available.')
        else:
            sale.save()
            messages.success(request, 'Sale recorded!')
            return redirect('sale_list')
    return render(request, 'supermarket/product_form.html', {'form': form, 'title': 'Record Sale'})


# ─────────────────────────────────────────
# M-PESA STK PUSH
# ─────────────────────────────────────────
@csrf_exempt
def send_stk_push(request):
    if request.method == 'POST':
        try:
            phone_number = request.POST.get('phone_number', '').strip()
            amount_raw   = request.POST.get('amount', '').strip()

            if not phone_number:
                return JsonResponse({'success': False, 'error': 'Phone number is required.'}, status=400)

            if not amount_raw:
                return JsonResponse({'success': False, 'error': 'Amount is required.'}, status=400)

            try:
                amount = int(float(amount_raw))
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Amount must be a number (e.g. 500).'}, status=400)

            if amount < 1:
                return JsonResponse({'success': False, 'error': 'Amount must be at least KES 1.'}, status=400)

            # Normalise phone format
            phone_number = phone_number.replace(' ', '').replace('-', '')
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            elif phone_number.startswith('+'):
                phone_number = phone_number[1:]

            if not phone_number.startswith('254') or len(phone_number) != 12:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid phone number. Use format: 07XXXXXXXX or 2547XXXXXXXX'
                }, status=400)

            cl = MpesaClient()
            response = cl.stk_push(
                phone_number=phone_number,
                amount=amount,
                account_reference='ElshadaiSupermarket',
                transaction_desc='Payment for goods',
                callback_url='https://your-ngrok-url.ngrok-free.app/mpesa/callback/'
            )

            checkout_request_id = getattr(response, 'checkout_request_id', None) or str(response)

            MpesaTransaction.objects.create(
                phone_number=phone_number,
                amount=amount,
                mpesa_code=f"PENDING-{checkout_request_id[:20]}",
                is_successful=False,
                checkout_request_id=checkout_request_id,
            )

            return JsonResponse({
                'success': True,
                'message': f'M-Pesa prompt sent to {phone_number}. Ask customer to enter PIN.',
                'checkout_request_id': checkout_request_id,
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'POST method required.'}, status=405)


# ─────────────────────────────────────────
# M-PESA STATUS POLL
# ─────────────────────────────────────────
@require_GET
def mpesa_payment_status(request):
    checkout_request_id = request.GET.get('checkout_request_id', '').strip()

    if not checkout_request_id:
        return JsonResponse({'status': 'error', 'message': 'Missing checkout_request_id'}, status=400)

    try:
        txn = MpesaTransaction.objects.filter(
            checkout_request_id=checkout_request_id
        ).latest('transaction_date')

        if txn.is_successful:
            return JsonResponse({
                'status': 'success',
                'mpesa_code': txn.mpesa_code,
                'amount': str(txn.amount),
                'phone': txn.phone_number,
                'message': f'Payment of KES {txn.amount} confirmed! Code: {txn.mpesa_code}',
            })
        elif getattr(txn, 'is_failed', False):
            return JsonResponse({
                'status': 'failed',
                'message': 'Payment was cancelled or rejected by customer.',
            })
        else:
            return JsonResponse({'status': 'pending', 'message': 'Waiting for customer to enter PIN...'})

    except MpesaTransaction.DoesNotExist:
        return JsonResponse({'status': 'pending', 'message': 'Waiting for payment confirmation...'})


# ─────────────────────────────────────────
# M-PESA CALLBACK
# ─────────────────────────────────────────
@login_not_required
@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        try:
            data        = json.loads(request.body)
            result      = data['Body']['stkCallback']
            result_code = result['ResultCode']
            checkout_request_id = result.get('CheckoutRequestID', '')

            if result_code == 0:
                items      = result['CallbackMetadata']['Item']
                amount     = next(i['Value'] for i in items if i['Name'] == 'Amount')
                mpesa_code = next(i['Value'] for i in items if i['Name'] == 'MpesaReceiptNumber')
                phone      = next(i['Value'] for i in items if i['Name'] == 'PhoneNumber')

                txn = MpesaTransaction.objects.filter(
                    checkout_request_id=checkout_request_id
                ).first()

                if txn:
                    txn.mpesa_code    = mpesa_code
                    txn.amount        = amount
                    txn.phone_number  = str(phone)
                    txn.is_successful = True
                    txn.save()
                else:
                    MpesaTransaction.objects.create(
                        phone_number=str(phone),
                        amount=amount,
                        mpesa_code=mpesa_code,
                        checkout_request_id=checkout_request_id,
                        is_successful=True,
                    )
            else:
                MpesaTransaction.objects.filter(
                    checkout_request_id=checkout_request_id,
                    is_successful=False,
                ).update(
                    mpesa_code='FAILED',
                    is_failed=True,
                )

        except Exception as e:
            print(f"[M-Pesa Callback Error]: {e}")

        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})

    return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Invalid method'})