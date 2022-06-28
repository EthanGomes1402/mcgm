from django.contrib import admin
from django.urls import path,re_path

from reports import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('reports/alert_geofence',views.alert_geofence,name='alert_geofence'),
    path('reports/alert_power_disconnect',views.alert_power_disconnect,name='alert_power_disconnect'),
    path('reports/alert_route_deviation',views.alert_route_deviation,name='alert_route_deviation'),
    path('reports/alert_speed',views.alert_speed,name='alert_speed'),

    path('reports/bin_collection_status',views.bin_collection_status,name='bin_collection_status'),
    path('reports/bin_rfid_tag_status',views.bin_rfid_tag_status,name='bin_rfid_tag_status'),

    path('reports/garage_traction',views.garage_traction,name='garage_traction'),

    path('reports/land_fill_site_usage_current',views.land_fill_site_usage_current,name='land_fill_site_usage_current'),
    path('reports/land_fill_site_usage_dumping_groundwise',views.land_fill_site_usage_dumping_groundwise,name='land_fill_site_usage_dumping_groundwise'),
    path('reports/land_fill_site_usage_weightwise',views.land_fill_site_usage_weightwise,name='land_fill_site_usage_weightwise'),

    path('reports/location_check_post',views.location_check_post,name='location_check_post'),
    path('reports/location_dumping_ground',views.location_dumping_ground,name='location_dumping_ground'),
    path('reports/location_garage',views.location_garage,name='location_garage'),
    path('reports/location_mlc',views.location_mlc,name='location_mlc'),
    path('reports/location_transfer_station',views.location_transfer_station,name='location_transfer_station'),

    path('reports/poi_departmental_offices',views.poi_departmental_offices,name='poi_departmental_offices'),
    path('reports/poi_departmental_workshops',views.poi_departmental_workshops,name='poi_departmental_workshops'),
    path('reports/poi_dmpgnd',views.poi_dmpgnd,name='poi_dmpgnd'),
    path('reports/poi_garbage_collection_points',views.poi_garbage_collection_points,name='poi_garbage_collection_points'),
    path('reports/poi_mlcs',views.poi_mlcs,name='poi_mlcs'),
    path('reports/poi_other_points',views.poi_other_points,name='poi_other_points'),
    path('reports/poi_station_locations',views.poi_station_locations,name='poi_station_locations'),
    path('reports/poi_swm_garages',views.poi_swm_garages,name='poi_swm_garages'),
    path('reports/poi_swm_offices',views.poi_swm_offices,name='poi_swm_offices'),
    path('reports/poi_transfer_stations',views.poi_transfer_stations,name='poi_transfer_stations'),
    path('reports/poi_ward_offices',views.poi_ward_offices,name='poi_ward_offices'),
    path('reports/poi_work_sites',views.poi_work_sites,name='poi_work_sites'),

    path('reports/register_transfer_station_vehiclewise',views.register_transfer_station_vehiclewise,name='register_transfer_station_vehiclewise'),
    path('reports/register_vehicle',views.register_vehicle,name='register_vehicle'),

    path('reports/stoppage',views.stoppage,name='stoppage'),

    path('reports/vehicle_route_history',views.vehicle_route_history,name='vehicle_route_history'),
    path('reports/vehicle_summery',views.vehicle_summery,name='vehicle_summery'),
    path('reports/vehicle_route_report',views.vehicle_route_report,name='vehicle_route_report'),
    #path('reports/generatePdfForVehicleRouteReport', views.generatePdfForVehicleRouteReport, name = 'generatePdfForVehicleRouteReport'),
    path('reports/generatePdfForVehicleRouteReport', views.generateps2pdf, name = 'generatePdfForVehicleRouteReport'),

    path('reports/vehicle_status_bin_rfid_tag',views.vehicle_status_bin_rfid_tag,name='vehicle_status_bin_rfid_tag'),
    path('reports/vehicle_status_bin_rfid_tag_status',views.vehicle_status_bin_rfid_tag_status,name='vehicle_status_bin_rfid_tag_status'),
    path('reports/vehicle_status_bin_rfid_tag_unregistered',views.vehicle_status_bin_rfid_tag_unregistered,name='vehicle_status_bin_rfid_tag_unregistered'),
    path('reports/vehicle_wind_schield_tag',views.vehicle_wind_schield_tag,name='vehicle_wind_schield_tag'),
    path('reports/vehicle_trace',views.vehicle_trace,name='vehicle_trace'),
    path('reports/vehicle_tracking',views.vehicle_tracking,name='vehicle_tracking'),

    path('reports/weight_locationwise',views.weight_locationwise,name='weight_locationwise'),
    path('reports/weight_wardwise',views.weight_wardwise,name='weight_wardwise'),
    path('reports/weight_zonewise',views.weight_zonewise,name='weight_zonewise'),
    path('reports/weight_history',views.weight_history,name='weight_history'),
    path('reports/get_vehicle_travel_history',views.get_vehicle_travel_history,name='get_vehicle_travel_history'),
    
#
#    #all ajax urls
#    path('ajax/get_unallocated_bins_from_ward/',views.get_unallocated_bins_from_ward,name='get_unallocated_bins_from_ward'),
#    path('ajax/allocate_bins_to_route/',views.allocate_bins_to_route,name='allocate_bins_to_route'),
#    path('ajax/deallocate_bin_from_route/',views.deallocate_bin_from_route,name='deallocate_bin_from_route'),
#    path('ajax/reorder_bins/',views.reorder_bins,name='reorder_bins'),
##   path('ajax/delete_topic/',views.delete_topic,name='delete_topic'),
#
#    #all edit urls
#    path('bin/edit/<int:pk>/',views.BinUpdateView.as_view(),name='edit_bin'),
#    path('contractor/edit/<int:pk>/',views.ContractorUpdateView.as_view(),name='edit_contractor'),
#    path('route/edit/<int:pk>/',views.RouteUpdateView.as_view(),name='edit_route'),
#    path('route_schedule/edit/<int:pk>/',views.RouteScheduleUpdateView.as_view(),name='edit_route_schedule'),
#    path('stop_station/edit/<int:pk>/',views.StopStationUpdateView.as_view(),name='edit_stop_station'),
#    path('vehicle/edit/<int:pk>/',views.VehicleUpdateView.as_view(),name='edit_vehicle'),
#    #path('ward/edit/<int:pk>/',views.WardUpdateView.as_view(),name='edit_ward'),
#    #path('vcm/edit/',views.CreateVCMView.as_view(),name='add_vcm'),
#    #path('board/edit/<int:pk>/',views.BoardUpdateView.as_view(),name='edit_board'),
#    #path('topic/edit/<int:pk>/',views.TopicUpdateView.as_view(),name='edit_topic'),
#
##    #all test urls
##    path('see_me/',views.see_me,name='see_me'),
##    #path('see_me/',views.see_me,name='see_me'),
##    path('lets_see/',views.lets_see,name='lets_see'),
##    path('just_simple_view/',views.just_simple_view.as_view(),name='see'),
##    #path('about/',views.add_board_topic,name='about'),
##
#    #all file upload and populate data urls
##   path('upload_student_data/',views.upload_student_data,name='upload_student_data'),
#    path('upload_vehicle_data/',views.upload_vehicle_data,name='upload_vehicle_data'),
#    path('upload_routes_and_bin_data/',views.upload_routes_and_bin_data,name='upload_bin_data'),
##   path('upload_wards_kml/',views.upload_wards,name='upload_wards_data'),
##   path('upload_geos_kml/',views.upload_geos,name='upload_geos_data'),
##   path('upload_vcm_data/',views.upload_vehicle_contractor_mapping,name='upload_vehicle_contractor_mapping'),
#
##    #all add urls    
#    path('bin/add/',views.BinCreateView.as_view(),name='add_bin'),
#    path('contractor/add/',views.ContractorCreateView.as_view(),name='add_contractor'),
#    path('route/add/',views.RouteCreateView.as_view(),name='add_route'),
#    path('route_schedule/add/',views.RouteScheduleCreateView.as_view(),name='add_route_schedule'),
#    path('stop_station/add/',views.StopStationCreateView.as_view(),name='add_stop_station'),
#    path('vehicle/add/',views.VehicleCreateView.as_view(),name='add_vehicle'),
#   #path('ward/add/',views.WardCreateView.as_view(),name='add_ward'),
#   #path('vcm/add/',views.CreateVCMView.as_view(),name='add_vcm'),
#   #path('ward/add/',views.add_ward,name='add_ward'),
#   #path('board/add/',views.CreateBoardView.as_view(),name='add_board'),
#
#    path('bin/delete/',views.BinCreateView.as_view(),name='delete_bin'),
#    path('contractor/add/',views.ContractorCreateView.as_view(),name='add_contractor'),
#    path('route/add/',views.RouteCreateView.as_view(),name='add_route'),
#    path('route_schedule/add/',views.RouteScheduleCreateView.as_view(),name='add_route_schedule'),
#    path('stop_station/add/',views.StopStationCreateView.as_view(),name='add_stop_station'),
#    path('vehicle/add/',views.VehicleCreateView.as_view(),name='add_vehicle'),
#    #path('ward/add/',views.WardCreateView.as_view(),name='add_ward'),
##
#    #all list urls
#    path('bins/',views.BinListView.as_view(),name='bins'),
#    path('contractors/',views.ContractorListView.as_view(),name='contractors'),
#    path('routes/',views.RouteListView.as_view(),name='routes'),
#    path('route_schedules/',views.RouteScheduleListView.as_view(),name='route_schedules'),
#    path('stop_stations/',views.StopStationListView.as_view(),name='stop_stations'),
#    path('vehicles/',views.VehicleListView.as_view(),name='vehicles'),
##   path('vcms/',views.VCMListView.as_view(),name='vcms'),
##   path('wards/',views.WardListView.as_view(),name='wards'),
#
#    #path('route/add/',views.add_route_data,name='add_route'),
#    #path('route/add/',views.CreateRouteView.as_view(),name='add_route'),
##    re_path(r'^boards/(?P<id>\d+)/$', views.boards,name='boards'),
##    re_path(r'^boards/(?P<id>\d+)/new/$', views.new_topic,name='new_topic'),
##    re_path(r'^topics/$', views.TopicListView.as_view(),name='topics'),
##    re_path(r'^boards/(?P<id>\d+)/topics/(?P<topic_id>\d+)/$',views.posts,name='posts'),
##    re_path(r'^boards/(?P<id>\d+)/topics/(?P<topic_id>\d+)/reply/$',views.reply_topic,name='reply_topic'),
##    re_path(r'^boards/(?P<id>\d+)/topics/(?P<topic_id>\d+)/posts/(?P<post_id>\d+)/edit/$',views.PostUpdateView.as_view(),name='edit_post')
]
