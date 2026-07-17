from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from supermarket.models import Category, Supplier, Product, Sale, Receipt, ReceiptItem, MpesaTransaction


class Command(BaseCommand):
    help = 'Seed the database with sample categories, suppliers, products, sales and mpesa transactions.'

    def handle(self, *args, **options):
        categories = [
            {'name': 'Beverages', 'description': 'Soft drinks, water, juice and refreshments.'},
            {'name': 'Household', 'description': 'Cleaning supplies and household essentials.'},
            {'name': 'Snacks', 'description': 'Chips, sweets, biscuits and quick bites.'},
            {'name': 'Personal Care', 'description': 'Toiletries, hygiene and personal care products.'},
            {'name': 'Bakery', 'description': 'Bread, pastries, cakes and baked snacks.'},
            {'name': 'Dairy', 'description': 'Milk, cheese, yoghurt and dairy essentials.'},
        ]
        suppliers = [
            {'name': 'East Africa Drinks', 'contact_person': 'Anna Mwangi', 'phone': '0712345678', 'email': 'anna@eadrinks.co.ke', 'address': 'Nairobi Industrial Area'},
            {'name': 'Fresh Mart Supplies', 'contact_person': 'Peter Otieno', 'phone': '0722345678', 'email': 'peter@freshmart.co.ke', 'address': 'Nairobi CBD'},
            {'name': 'Sparkle Clean', 'contact_person': 'Grace Kimani', 'phone': '0733345678', 'email': 'grace@sparkleclean.co.ke', 'address': 'Thika Road'},
            {'name': 'Daily Essentials Ltd', 'contact_person': 'James Njoroge', 'phone': '0744445678', 'email': 'james@dailyessentials.co.ke', 'address': 'Westlands, Nairobi'},
            {'name': 'Bakers Guild', 'contact_person': 'Samuel Mwenda', 'phone': '0755556789', 'email': 'samuel@bakersguild.co.ke', 'address': 'Kilimani'},
            {'name': 'Pure Dairy Co', 'contact_person': 'Alice Wambui', 'phone': '0766667890', 'email': 'alice@puredairy.co.ke', 'address': 'Ruiru'},
        ]

        created_categories = {}
        for category_data in categories:
            category, created = Category.objects.get_or_create(
                name=category_data['name'],
                defaults={
                    'description': category_data['description'],
                    'is_active': True,
                }
            )
            created_categories[category.name] = category
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))

        created_suppliers = {}
        for supplier_data in suppliers:
            supplier, created = Supplier.objects.get_or_create(
                name=supplier_data['name'],
                defaults={
                    'contact_person': supplier_data['contact_person'],
                    'phone': supplier_data['phone'],
                    'email': supplier_data['email'],
                    'address': supplier_data['address'],
                    'is_active': True,
                }
            )
            created_suppliers[supplier.name] = supplier
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created supplier: {supplier.name}'))

        products = [
            {
                'name': 'Everest Mineral Water 500ml',
                'sku': 'BEV-001',
                'barcode_number': '1234567890123',
                'category': created_categories['Beverages'],
                'supplier': created_suppliers['East Africa Drinks'],
                'price': '55.00',
                'cost_price': '30.00',
                'stock_quantity': 120,
                'reorder_level': 20,
                'description': 'Refreshing bottled water for everyday customers.',
            },
            {
                'name': 'Spark Cola 330ml',
                'sku': 'BEV-002',
                'barcode_number': '1234567890456',
                'category': created_categories['Beverages'],
                'supplier': created_suppliers['East Africa Drinks'],
                'price': '90.00',
                'cost_price': '50.00',
                'stock_quantity': 80,
                'reorder_level': 15,
                'description': 'Classic soda drink for the whole family.',
            },
            {
                'name': 'Ultra Rice 5kg',
                'sku': 'HHD-001',
                'barcode_number': '1234567890789',
                'category': created_categories['Household'],
                'supplier': created_suppliers['Fresh Mart Supplies'],
                'price': '820.00',
                'cost_price': '600.00',
                'stock_quantity': 35,
                'reorder_level': 10,
                'description': 'High-quality white rice for home cooking.',
            },
            {
                'name': 'Sparkle Laundry Soap',
                'sku': 'HHD-002',
                'barcode_number': '1234567890111',
                'category': created_categories['Household'],
                'supplier': created_suppliers['Sparkle Clean'],
                'price': '250.00',
                'cost_price': '140.00',
                'stock_quantity': 60,
                'reorder_level': 12,
                'description': 'Powerful soap for fresh and clean laundry.',
            },
            {
                'name': 'Fresh Mint Toothpaste 100ml',
                'sku': 'PC-001',
                'barcode_number': '1234567890333',
                'category': created_categories['Personal Care'],
                'supplier': created_suppliers['Daily Essentials Ltd'],
                'price': '180.00',
                'cost_price': '95.00',
                'stock_quantity': 45,
                'reorder_level': 10,
                'description': 'Minty toothpaste for daily oral care.',
            },
            {
                'name': 'Chips Crave 70g',
                'sku': 'SNK-001',
                'barcode_number': '1234567890555',
                'category': created_categories['Snacks'],
                'supplier': created_suppliers['Daily Essentials Ltd'],
                'price': '65.00',
                'cost_price': '35.00',
                'stock_quantity': 100,
                'reorder_level': 25,
                'description': 'Crispy potato chips for a quick snack.',
            },
            {
                'name': 'Classic White Bread',
                'sku': 'BKR-001',
                'barcode_number': '1234567890666',
                'category': created_categories['Bakery'],
                'supplier': created_suppliers['Bakers Guild'],
                'price': '120.00',
                'cost_price': '70.00',
                'stock_quantity': 60,
                'reorder_level': 15,
                'description': 'Soft daily white bread loaf.',
            },
            {
                'name': 'Cheddar Cheese 250g',
                'sku': 'DRY-001',
                'barcode_number': '1234567890777',
                'category': created_categories['Dairy'],
                'supplier': created_suppliers['Pure Dairy Co'],
                'price': '320.00',
                'cost_price': '210.00',
                'stock_quantity': 30,
                'reorder_level': 8,
                'description': 'Rich and creamy cheddar cheese.',
            },
        ]

        created_products = {}
        for product_data in products:
            product, created = Product.objects.get_or_create(
                sku=product_data['sku'],
                defaults={
                    'name': product_data['name'],
                    'barcode_number': product_data['barcode_number'],
                    'category': product_data['category'],
                    'supplier': product_data['supplier'],
                    'price': product_data['price'],
                    'cost_price': product_data['cost_price'],
                    'stock_quantity': product_data['stock_quantity'],
                    'reorder_level': product_data['reorder_level'],
                    'description': product_data['description'],
                    'is_active': True,
                }
            )
            created_products[product.sku] = product
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created product: {product.name}'))

        if not Sale.objects.exists():
            sample_sales = [
                {'product': created_products['BEV-001'], 'quantity': 8, 'cashier': 'Mary'},
                {'product': created_products['BEV-002'], 'quantity': 5, 'cashier': 'Peter'},
                {'product': created_products['HHD-001'], 'quantity': 3, 'cashier': 'Alice'},
                {'product': created_products['PC-001'], 'quantity': 4, 'cashier': 'John'},
            ]
            for sale_data in sample_sales:
                sale = Sale.objects.create(
                    product=sale_data['product'],
                    quantity_sold=sale_data['quantity'],
                    unit_price=Decimal(str(sale_data['product'].price)),
                    cashier=sale_data['cashier'],
                )
                self.stdout.write(self.style.SUCCESS(f'Created sale: {sale}'))

        if not Receipt.objects.exists():
            receipt_samples = [
                {
                    'receipt_number': 'RCP-20260714-1001',
                    'cashier': 'Mary',
                    'items': [
                        {'sku': 'BEV-001', 'quantity': 2},
                        {'sku': 'SNK-001', 'quantity': 1},
                    ],
                    'amount_paid': '260.00',
                },
                {
                    'receipt_number': 'RCP-20260714-1002',
                    'cashier': 'Peter',
                    'items': [
                        {'sku': 'HHD-001', 'quantity': 1},
                        {'sku': 'PC-001', 'quantity': 2},
                    ],
                    'amount_paid': '560.00',
                },
            ]
            for receipt_data in receipt_samples:
                subtotal = Decimal('0.00')
                for item in receipt_data['items']:
                    product = created_products[item['sku']]
                    subtotal += product.price * item['quantity']
                tax_rate = Decimal('0.00')
                tax_amount = Decimal('0.00')
                grand_total = subtotal + tax_amount
                amount_paid = Decimal(receipt_data['amount_paid'])
                change_given = max(Decimal('0.00'), amount_paid - grand_total)

                receipt = Receipt.objects.create(
                    receipt_number=receipt_data['receipt_number'],
                    cashier=receipt_data['cashier'],
                    total_amount=subtotal,
                    tax_rate=tax_rate,
                    tax_amount=tax_amount,
                    grand_total=grand_total,
                    amount_paid=amount_paid,
                    change_given=change_given,
                )
                for item in receipt_data['items']:
                    product = created_products[item['sku']]
                    ReceiptItem.objects.create(
                        receipt=receipt,
                        product=product,
                        product_name=product.name,
                        quantity=item['quantity'],
                        unit_price=product.price,
                        subtotal=product.price * item['quantity'],
                    )
                self.stdout.write(self.style.SUCCESS(f'Created receipt: {receipt.receipt_number}'))

        if not MpesaTransaction.objects.exists():
            mpesa_samples = [
                {'phone_number': '254712345678', 'amount': '450.00', 'mpesa_code': 'ABC123XYZ', 'checkout_request_id': 'CRP001', 'is_successful': True},
                {'phone_number': '254733456789', 'amount': '980.00', 'mpesa_code': 'DEF456UVW', 'checkout_request_id': 'CRP002', 'is_successful': True},
                {'phone_number': '254722567890', 'amount': '520.00', 'mpesa_code': 'GHI789RST', 'checkout_request_id': 'CRP003', 'is_successful': True},
            ]
            for txn in mpesa_samples:
                transaction = MpesaTransaction.objects.create(
                    phone_number=txn['phone_number'],
                    amount=txn['amount'],
                    mpesa_code=txn['mpesa_code'],
                    checkout_request_id=txn['checkout_request_id'],
                    is_successful=txn['is_successful'],
                )
                self.stdout.write(self.style.SUCCESS(f'Created MpesaTransaction: {transaction}'))

        self.stdout.write(self.style.SUCCESS('Sample data seeded successfully.'))
