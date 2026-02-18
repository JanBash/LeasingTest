from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.views.defaults import page_not_found
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('app.urls')),
    path('auth/', include('user.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += [
        path('test-404/', page_not_found, {'exception': Exception("Test 404")}),
    ]
