from django.test import TestCase

from .forms import CategoryForm, ProductForm, SupplierForm


class ManagementFormTests(TestCase):
    def test_category_form_includes_active_status(self):
        form = CategoryForm()
        self.assertIn('is_active', form.fields)

    def test_supplier_form_includes_active_status(self):
        form = SupplierForm()
        self.assertIn('is_active', form.fields)

    def test_product_form_includes_status_and_description(self):
        form = ProductForm()
        self.assertIn('description', form.fields)
        self.assertIn('is_active', form.fields)
