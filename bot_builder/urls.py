from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from api import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('social_django.urls', namespace='social')),
    path('api/', include('api.urls')),
    path('', views.home, name='home'),  # ← корневой URL
    path('logout/',
         auth_views.LogoutView.as_view(next_page='/'),
         name='logout'
         ),
]
