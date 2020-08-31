"""myproject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,re_path

from healthadmin import views
from accounts import views as accounts_view
from django.contrib.auth import views as auth_views

urlpatterns = [

    #all file upload and populate data urls
    path('upload_vehicle_data/',views.upload_vehicle_data2,name='upload_health_vehicle_data'),
    path('vehicles/',views.VehicleListView.as_view(),name='health_vehicles'),
    path('vehicle/edit/<int:pk>/',views.VehicleUpdateView.as_view(),name='edit_health_vehicle'),
    path('ajax/delete_vehicle/',views.delete_vehicle,name='delete_health_vehicle'),
    path('vehicle/add/',views.VehicleCreateView.as_view(),name='add_health_vehicle'),
]
