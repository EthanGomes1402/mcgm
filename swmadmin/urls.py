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

from swmadmin import views
from accounts import views as accounts_view
from django.contrib.auth import views as auth_views

urlpatterns = [
#   autocomplete
#   path('vehicle_autocomplete/',views.VehicleAutoCompleteView.as_view(),name='vehicle_autocomplete'),
#   path('user_autocomplete/',views.UserAutoCompleteView.as_view(),name='user_autocomplete'),

#   all ajax urls for bin route relations
    path('ajax/get_unallocated_bins_from_ward/',views.get_unallocated_bins_from_ward,name='get_unallocated_bins_from_ward'),
    path('ajax/allocate_bins_to_route/',views.allocate_bins_to_route,name='allocate_bins_to_route'),
    path('ajax/deallocate_bin_from_route/',views.deallocate_bin_from_route,name='deallocate_bin_from_route'),
    path('ajax/reorder_bins/',views.reorder_bins,name='reorder_bins'),
    path('ajax/get_bin_location_from_route/',views.get_bin_location_from_route,name='get_bin_location_from_route'),
    path('ajax/get_bins_from_route/',views.get_bins_from_route,name='get_bins_from_route'),


    #all edit urls
    path('bin/edit/<int:pk>/',views.BinUpdateView.as_view(),name='edit_bin'),
    path('contractor/edit/<int:pk>/',views.ContractorUpdateView.as_view(),name='edit_contractor'),
    path('route/edit/<int:pk>/',views.RouteUpdateView.as_view(),name='edit_route'),
    path('route_schedule/edit/<int:pk>/',views.RouteScheduleUpdateView.as_view(),name='edit_route_schedule'),
    path('stop_station/edit/<int:pk>/',views.StopStationUpdateView.as_view(),name='edit_stop_station'),
    path('vehicle/edit/<int:pk>/',views.VehicleUpdateView.as_view(),name='edit_vehicle'),
    path('wcm/edit/<int:pk>/',views.WCMUpdateView.as_view(),name='edit_wcm'),
    path('vgm/edit/<int:pk>/',views.VGMUpdateView.as_view(),name='edit_vgm'),
    path('installation/edit/<int:pk>/',views.InstallationUpdateView.as_view(),name='edit_installation'),
    #path('vcm/edit/',views.CreateVCMView.as_view(),name='add_vcm'),

    #all file upload and populate data urls
    path('upload_vehicle_data/',views.upload_vehicle_data,name='upload_vehicle_data'),
    path('upload_stop_station_data/',views.upload_stop_station_data,name='upload_stop_station_data'),
    path('upload_routes_and_bin_data/',views.upload_routes_and_bin_data,name='upload_routes_and_bin_data'),
    path('upload_bin_data/',views.upload_bin_data,name='upload_bin_data'),
    path('upload_wcm_data/',views.upload_ward_contractor_mapping,name='upload_ward_contractor_mapping'),
    path('upload_installation_data/',views.upload_installation_data,name='upload_installation_data'),
    path('upload_route_schedule_data/',views.upload_route_schedule_data,name='upload_route_schedule_data'),

#    #all add urls    
    path('bin/add/',views.BinCreateView.as_view(),name='add_bin'),
    path('contractor/add/',views.ContractorCreateView.as_view(),name='add_contractor'),
    path('route/add/',views.RouteCreateView.as_view(),name='add_route'),
    path('route_schedule/add/',views.RouteScheduleCreateView.as_view(),name='add_route_schedule'),
    path('stop_station/add/',views.StopStationCreateView.as_view(),name='add_stop_station'),
    path('vehicle/add/',views.VehicleCreateView.as_view(),name='add_vehicle'),
    path('wcm/add/',views.WCMCreateView.as_view(),name='add_wcm'),
    path('vgm/add/',views.VGMCreateView.as_view(),name='add_vgm'),
    path('installation/add/',views.InstallationCreateView.as_view(),name='add_installation'),
#   path('vcm/add/',views.CreateVCMView.as_view(),name='add_vcm'),

#   all list urls
    path('bins/',views.BinListView.as_view(),name='bins'),
    path('contractors/',views.ContractorListView.as_view(),name='contractors'),
    path('routes/',views.RouteListView.as_view(),name='routes'),
    path('route_schedules/',views.RouteScheduleListView.as_view(),name='route_schedules'),
    path('stop_stations/',views.StopStationListView.as_view(),name='stop_stations'),
    path('vehicles/',views.VehicleListView.as_view(),name='vehicles'),
    path('wcms/',views.WCMListView.as_view(),name='wcms'),
    path('vgms/',views.VGMListView.as_view(),name='vgms'),
    path('installations/',views.InstallationListView.as_view(),name='installations'),
#   path('vcms/',views.VCMListView.as_view(),name='vcms'),

#   all delete urls for common app
    path('ajax/delete_vehicle/',views.delete_vehicle,name='delete_vehicle'),
    path('ajax/delete_route/',views.delete_route,name='delete_route'),
    path('ajax/delete_bin/',views.delete_bin,name='delete_bin'),
    path('ajax/delete_stop_station/',views.delete_stop_station,name='delete_stop_station'),
    path('ajax/delete_route_schedule/',views.delete_route_schedule,name='delete_route_schedule'),
    path('ajax/delete_contractor/',views.delete_contractor,name='delete_contractor'),
    path('ajax/delete_wcm/',views.delete_wcm,name='delete_wcm'),
    path('ajax/delete_vgm/',views.delete_vgm,name='delete_vgm'),
    path('ajax/delete_installation/',views.delete_installation,name='delete_installation'),

#    path('ajax/get_route_fence/',views.get_route_fence,name='get_route_fence'),
    path('ajax/get_bin_spot/',views.get_bin_spot,name='get_bin_spot'),
    path('ajax/get_all_bin_spot/',views.get_all_bin_spot,name='get_all_bin_spot'),
    path('ajax/get_all_bin_spot_from_ward/',views.get_all_bin_spot_from_ward,name='get_all_bin_spot_from_ward'),
    path('ajax/get_all_mlc_spot/',views.get_all_mlc_spot,name='get_all_mlc_spot'),
    path('ajax/get_all_tnsstn_spot/',views.get_all_tnsstn_spot,name='get_all_tnsstn_spot'),
    path('ajax/get_all_dmpgnd_spot/',views.get_all_dmpgnd_spot,name='get_all_dmpgnd_spot'),
    path('ajax/get_all_garage_spot/',views.get_all_garage_spot,name='get_all_garage_spot'),
    path('ajax/get_stop_station_area/',views.get_stop_station_area,name='get_stop_station_area'),
]
