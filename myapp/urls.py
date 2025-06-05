from django.urls import path
from . import views

urlpatterns = [
    path('upload-excel/', views.upload_excel_view, name='upload_excel'),
]
