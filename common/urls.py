from django.conf.urls import url
from django.contrib import admin
from django.urls import path,include
from common import views as common_views

urlpatterns = [
    #all add urls for common app     
    path('upload_wards_kml/',common_views.upload_wards,name='upload_wards'),
    path('ward/add/',common_views.WardCreateView.as_view(),name='add_ward'),
    path('zone/add/',common_views.ZoneCreateView.as_view(),name='add_zone' ),
    path('div/add/',common_views.DivCreateView.as_view(),name='add_div' ),

    #all edit urls for common app
    path('ward/edit/<int:pk>/',common_views.WardUpdateView.as_view(),name='edit_ward'),
    path('zone/edit/<int:pk>/',common_views.ZoneUpdateView.as_view(),name='edit_zone'),
    path('div/edit/<int:pk>',common_views.DivUpdateView.as_view(),name='edit_div' ),

    #all list urls for common app  
    path('wards/',common_views.WardListView.as_view(),name='wards'),
    path('zones/',common_views.ZoneListView.as_view(),name='zones'),
    path('divs/',common_views.DivListView.as_view(),name='divs'),

    #all delete urls for common app
    path('ajax/delete_ward/',common_views.delete_ward,name='delete_ward'),
    path('ajax/delete_zone/',common_views.delete_zone,name='delete_zone'),
    path('ajax/delete_div/',common_views.delete_div,name='delete_div'),

    #get fences of areas
    path('ajax/get_ward_area/',common_views.get_ward_area,name='get_ward_area'),
    path('ajax/get_zone_area/',common_views.get_zone_area,name='get_zone_area'),
    path('ajax/get_div_area/',common_views.get_div_area,name='get_div_area'),
]
