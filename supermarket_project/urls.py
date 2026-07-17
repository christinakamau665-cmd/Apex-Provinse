from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView

from supermarket.views import BrandedLoginView

# ─────────────────────────────────────────
# REBRANDING THE DJANGO ADMIN PANEL
# ─────────────────────────────────────────
admin.site.site_header = "Apex Provisions Administration"
admin.site.site_title = "Apex Provisions Portal"
admin.site.index_title = "Welcome to the Apex Provisions Management Console"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', BrandedLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('', include('supermarket.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)