from django.urls import path
from . import views
from django.contrib.auth import views as auth_views # Import Django's built-in auth views for consistency

urlpatterns = [
    path('upload-excel/', views.upload_excel_view, name='upload_excel'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'), # Using a custom login view
    path('logout/', views.logout_view, name='logout'), # Using a custom logout view
]
