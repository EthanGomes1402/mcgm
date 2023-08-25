from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import User
from common.models import Ward,Zone,Div
from swmadmin.models import Vehicle,Contractor,Ward_Contractor_Mapping,Bin,Route,Stop_station,Vehicle_Garage_Mapping,Ewd
from reports.models import Alert,Tracklog_history
from django.http import HttpResponse,JsonResponse
from django.shortcuts import render,redirect,get_object_or_404
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import CreateView,UpdateView,ListView,View,DetailView,DeleteView
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import datetime
from openpyxl import load_workbook
import json,re,string,random,inspect
from fastkml import kml
from django.contrib.gis.gdal.datasource import DataSource
from django.contrib.gis.geos import GEOSGeometry,Point,LineString
from django.contrib.gis.gdal import SpatialReference, CoordTransform
from django.contrib import messages
from django.contrib.gis import geos
from django.http import QueryDict
from django.db.models import Sum,Count
import dateutil.parser
from geopy.geocoders import Nominatim
from datetime import date,timedelta
from itertools import chain
import codecs
import math
from datetime import datetime
import os
from rest_framework.decorators import api_view, renderer_classes      #***ETH
import logging
import psycopg2      #***ETH

gcoord = SpatialReference(3857)
mycoord = SpatialReference(4326)
trans = CoordTransform(gcoord, mycoord)
timestamp_from = datetime.now().date()

geofence_alert_subcategory = {
        '1' : 'central workshop',
        '2' : 'department offices',
        '3' : 'department workshop',
        '4' : 'dumping ground',
        '5' : 'garbage collection point',
        '6' : 'maintainance sites',
        '7' : 'motor loading chowkies',
        '8' : 'station location',
        '9' : 'swd workshops',
        '10' : 'swm garages',
        '11' : 'swm offices',
        '12' : 'transfer stations',
        '13' : 'ward offices',
        '14' : 'work site'
        }

def set_session_reporting_form_params(request):
    form_parameters = dict()
    geo_heirarchy = dict()
    area_without_geo_heirarchy = dict()
    area_without_geo_heirarchy['tnsstns'] = []
    area_without_geo_heirarchy['dmpgnds'] = []
    for each_ts in Stop_station.objects.filter(is_tnsstn=True):
        ts_info = dict()
        ts_info['id'] = each_ts.id
        ts_info['name'] = each_ts.name
        area_without_geo_heirarchy['tnsstns'].append(ts_info)

    for each_dmpgnd in Stop_station.objects.filter(is_dmpgnd=True):
        dmpgnd_info = dict()
        dmpgnd_info['id'] = each_dmpgnd.id
        dmpgnd_info['name'] = each_dmpgnd.name
        area_without_geo_heirarchy['dmpgnds'].append(dmpgnd_info)

    for each_div in Div.objects.all().order_by('short_name'):
        div_key = str(each_div.short_name)+ str('_') + str(each_div.id)
        geo_heirarchy[div_key] = {}
        for each_zone in each_div.zones.all().order_by('short_name'):
            zone_key = str(each_zone.short_name)+ str('_') + str(each_zone.id)
            geo_heirarchy[div_key][zone_key]={}
            for each_ward in each_zone.wards.all():
                ward_key = str(each_ward.name)+ str('_') + str(each_ward.id)
                geo_heirarchy[div_key][zone_key][ward_key]={}
                geo_heirarchy[div_key][zone_key][ward_key]['vehicles']=[]
                geo_heirarchy[div_key][zone_key][ward_key]['garages']=[]
                geo_heirarchy[div_key][zone_key][ward_key]['mlcs']=[]
                geo_heirarchy[div_key][zone_key][ward_key]['checkposts']=[]
                geo_heirarchy[div_key][zone_key][ward_key]['bins']=[]
                geo_heirarchy[div_key][zone_key][ward_key]['routes']=[]
#                if Ward_Contractor_Mapping.objects.filter(ward=each_ward):
#                    ward_contractor_map = Ward_Contractor_Mapping.objects.filter(ward=each_ward).get()
#                    for each_vehicle in Vehicle.objects.filter(contractor= ward_contractor_map.contractor):
#                        vehicle_info = dict()
#                        vehicle_info['id'] = each_vehicle.id
#                        vehicle_info['plate_number'] = each_vehicle.plate_number
#                        geo_heirarchy[div_key][zone_key][ward_key]['vehicles'].append(vehicle_info)

                for each_vehicle in each_ward.vehicles.all():
                        vehicle_info = dict()
                        vehicle_info['id'] = each_vehicle.id
                        vehicle_info['plate_number'] = each_vehicle.plate_number
                        geo_heirarchy[div_key][zone_key][ward_key]['vehicles'].append(vehicle_info)

                for each_stop_station in Stop_station.objects.filter(is_garage=True).filter(stop_station_fence__coveredby=each_ward.ward_fence):
                    garage_vehicle_maps = Vehicle_Garage_Mapping.objects.filter(garage=each_stop_station)
                    garage_info = dict()
                    garage_info['id'] = each_stop_station.id
                    garage_info['name'] = each_stop_station.name
                    garage_info['vehicles'] = []

                    for each_gvm in garage_vehicle_maps:
                        vehicle_info = dict()
                        vehicle_info['id'] = each_gvm.vehicle.id
                        vehicle_info['plate_number'] = each_gvm.vehicle.plate_number
                        garage_info['vehicles'].append(vehicle_info)

                    geo_heirarchy[div_key][zone_key][ward_key]['garages'].append(garage_info)

                for each_mlc in Stop_station.objects.filter(is_mlc=True).filter(stop_station_fence__coveredby=each_ward.ward_fence):
                    mlc_info = dict()
                    mlc_info['id'] = each_mlc.id
                    mlc_info['name'] = each_mlc.name
                    geo_heirarchy[div_key][zone_key][ward_key]['mlcs'].append(mlc_info)

                for each_cp in Stop_station.objects.filter(is_chkpst=True).filter(stop_station_fence__coveredby=each_ward.ward_fence):
                    cp_info = dict()
                    cp_info['id'] = each_cp.id
                    cp_info['name'] = each_cp.name
                    geo_heirarchy[div_key][zone_key][ward_key]['checkposts'].append(cp_info)

                for each_bin in each_ward.bins.all():
                    bin_info = dict()
                    bin_info['id'] = each_bin.id
                    bin_info['code'] = each_bin.code
                    geo_heirarchy[div_key][zone_key][ward_key]['bins'].append(bin_info)

                for each_route in each_ward.routes.all():
                    route_info = dict()
                    route_info['id'] = each_route.id
                    route_info['code'] = each_route.code
                    geo_heirarchy[div_key][zone_key][ward_key]['routes'].append(route_info)

    form_parameters['areal_hierarchy_params'] = geo_heirarchy
    form_parameters['areal_extra_params'] = area_without_geo_heirarchy
    request.session['reports_form_params']= json.dumps(form_parameters)
    return

##done
def alert_geofence(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
        from_time = dateutil.parser.parse(form_data['from_time'])
        to_time   = dateutil.parser.parse(form_data['to_time'])
        sub_cat   = form_data['selectCategory']
        vehicles  = list(map(lambda vehicle : Vehicle.objects.get(pk=vehicle) , form_data['selectVehicle'].split("_")))

        for each_vehicle in vehicles:
            for each_alert in each_vehicle.alerts.filter(created_at__range=(from_time,to_time)).filter(category='1').filter(sub_category=sub_cat):
                each_alert_data = dict()
                each_alert_data['sub_category'] = geofence_alert_subcategory[each_alert.sub_category]
                each_alert_data['message'] = each_alert.message
                if each_alert.location:
                    each_alert_data['lat'] = each_alert.location.coords[1]
                    each_alert_data['lon'] = each_alert.location.coords[0]
                else:
                    each_alert_data['lat'] = ''
                    each_alert_data['lon'] = ''

                each_alert_data['vehicle'] = each_vehicle.plate_number
                each_alert_data['alert'] = 'Geofence'
                each_alert_data['time'] = each_vehicle.created_at.strftime("%Y-%m-%d %H:%M:%S")
                response_data['data'].append(each_alert_data)

        return HttpResponse(json.dumps(response_data),content_type="application/json")

    #get alert of all vehcle selected or all for given category within date range
    #this alert table will be populated by cron running in bg
    #fields required div,zone,vehicle,geofence category,date range parameter
    sub_category = Alert.alert_sub_category_choices
    return render(request,'reports/alert_geofence.html',{ 'form_params' : form_params , 'sub_category' : sub_category})

##done
def alert_power_disconnect(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
        from_time = dateutil.parser.parse(form_data['from_time'])
        to_time = dateutil.parser.parse(form_data['to_time'])
        vehicles  = list(map(lambda vehicle : Vehicle.objects.get(pk=vehicle) , form_data['selectVehicle'].split("_")))

        vgm = 0
        for each_vehicle in vehicles:
            if Vehicle_Garage_Mapping.objects.filter(vehicle=each_vehicle).exists():
                vgm = Vehicle_Garage_Mapping.objects.get(vehicle_id=each_vehicle.id)

            for each_alert in each_vehicle.alerts.filter(created_at__range=(from_time,to_time)).filter(category='2'):
                each_alert_data = dict()
                each_alert_data['message'] = each_alert.message
                if each_alert.location:
                    each_alert_data['lat'] = each_alert.location.coords[1]
                    each_alert_data['lon'] = each_alert.location.coords[0]
                else:
                    each_alert_data['lat'] = ''
                    each_alert_data['lon'] = ''

                each_alert_data['vehicle'] = each_vehicle.plate_number

                if vgm:
                    each_alert_data['garage'] = vgm.garage
                else:
                    each_alert_data['garage'] = ''

                each_alert_data['alert'] = 'Power Disconnections'
                each_alert_data['time'] = each_vehicle.created_at.strftime("%Y-%m-%d %H:%M:%S")
                response_data['data'].append(each_alert_data)

        return HttpResponse(json.dumps(response_data),content_type="application/json")

    #get alert of all vehicle selected or all for given category within date range
    #this alert table will be populated by cron running in bg
    #fields required div,zone,vehicle,geofence category,date range parameter

    #fields required div,zone,vehicle,date range parameter
    #return HttpResponse("<h1> report "+ str(inspect.stack()[0][3]) +"</h1>")
    return render(request,'reports/alert_power_disconnect.html',{ 'form_params' : form_params })

##done
def alert_route_deviation(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
        from_time = dateutil.parser.parse(form_data['from_time'])
        to_time = dateutil.parser.parse(form_data['to_time'])
        vehicles  = list(map(lambda vehicle : Vehicle.objects.get(pk=vehicle) , form_data['selectVehicle'].split("_")))

        vgm = 0
        for each_vehicle in vehicles:
            if Vehicle_Garage_Mapping.objects.filter(vehicle=each_vehicle).exists():
                vgm = Vehicle_Garage_Mapping.objects.get(vehicle_id=each_vehicle.id)

            for each_alert in each_vehicle.alerts.filter(created_at__range=(from_time,to_time)).filter(category='3'):
                each_alert_data = dict()
                each_alert_data['message'] = each_alert.message
                if each_alert.location:
                    each_alert_data['lat'] = each_alert.location.coords[1]
                    each_alert_data['lon'] = each_alert.location.coords[0]
                else:
                    each_alert_data['lat'] = ''
                    each_alert_data['lon'] = ''

                each_alert_data['vehicle'] = each_vehicle.plate_number

                if vgm:
                    each_alert_data['garage'] = vgm.garage
                else:
                    each_alert_data['garage'] = ''

                each_alert_data['alert'] = 'Route Deviation'
                each_alert_data['time'] = each_vehicle.created_at.strftime("%Y-%m-%d %H:%M:%S")
                response_data['data'].append(each_alert_data)

        return HttpResponse(json.dumps(response_data),content_type="application/json")

    #get alert of all vehicle selected or all for given category within date range
    #this alert table will be populated by cron running in bg
    #fields required div,zone,vehicle,geofence category,date range parameter

    #fields required div,zone,vehicle,date range parameter
    #return HttpResponse("<h1> report "+ str(inspect.stack()[0][3]) +"</h1>")
    return render(request,'reports/alert_route_deviation.html', { 'form_params' : form_params })

##done
def alert_speed(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
        from_time = dateutil.parser.parse(form_data['from_time'])
        to_time = dateutil.parser.parse(form_data['to_time'])
        vehicles  = list(map(lambda vehicle : Vehicle.objects.get(pk=vehicle) , form_data['selectVehicle'].split("_")))

        vgm = 0
        for each_vehicle in vehicles:
            if Vehicle_Garage_Mapping.objects.filter(vehicle=each_vehicle).exists():
                vgm = Vehicle_Garage_Mapping.objects.get(vehicle_id=each_vehicle.id)

            for each_alert in each_vehicle.alerts.filter(created_at__range=(from_time,to_time)).filter(category='4'):
                each_alert_data = dict()
                each_alert_data['message'] = each_alert.message
                if each_alert.location:
                    each_alert_data['lat'] = each_alert.location.coords[1]
                    each_alert_data['lon'] = each_alert.location.coords[0]
                else:
                    each_alert_data['lat'] = ''
                    each_alert_data['lon'] = ''

                each_alert_data['vehicle'] = each_vehicle.plate_number

                if vgm:
                    each_alert_data['garage'] = vgm.garage
                else:
                    each_alert_data['garage'] = ''

                each_alert_data['alert'] = 'Speed Exceed'
                each_alert_data['time'] = each_vehicle.created_at.strftime("%Y-%m-%d %H:%M:%S")
                response_data['data'].append(each_alert_data)

        return HttpResponse(json.dumps(response_data),content_type="application/json")

    #get alert of all vehicle selected or all for given category within date range
    #this alert table will be populated by cron running in bg
    #fields required div,zone,vehicle,geofence category,date range parameter

    #fields required div,zone,vehicle,date range parameter
    #return HttpResponse("<h1> report "+ str(inspect.stack()[0][3]) +"</h1>")
    return render(request,'reports/alert_speed.html',{ 'form_params' : form_params })

##done
def bin_collection_status(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
        from_date = dateutil.parser.parse(form_data['from_date'])
#        bin_status= form_data['selectStatus'] == 'active' and True or False
#        wards  = list(map(lambda ward : Ward.objects.get(pk=ward) , form_data['selectWard'].split("_")))
#
#        for each_ward in wards:
#            for each_bin in each_ward.bins.filter(is_active=bin_status):
#                each_bin_data = dict()
#                each_bin_data['name'] = each_bin.name
#                each_bin_data['id'] = each_bin.id
#                #each_bin_data['location'] = each_bin.bin_location
#                each_bin_data['rfid'] = each_bin.tag
#                each_bin_data['status'] = 'active'
#                response_data['data'].append(each_bin_data)
#
    #fields required div,zone,ward,mlcs,shift,date range parameter
    #op = mlc ,shift,vehicle,veh category,route,total bisn to be collecetd , total bins collected,bin_entry_time,bin_exits_time, bin status
    #return HttpResponse("<h1> report "+ str(inspect.stack()[0][3]) +"</h1>")
    return render(request,'reports/bin_collection_status.html',{ 'form_params' : form_params })

##done
def bin_rfid_tag_status(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
        bin_status= form_data['selectStatus'] == 'active' and True or False
        wards  = list(map(lambda ward : Ward.objects.get(pk=ward) , form_data['selectWard'].split("_")))

        for each_ward in wards:
            for each_bin in each_ward.bins.filter(is_active=bin_status):
                each_bin_data = dict()
                each_bin_data['name'] = each_bin.name
                each_bin_data['id'] = each_bin.id
                #each_bin_data['location'] = each_bin.bin_location
                each_bin_data['rfid'] = each_bin.tag
                each_bin_data['status'] = 'active'
                response_data['data'].append(each_bin_data)

        return HttpResponse(json.dumps(response_data),content_type="application/json")
    #op rfid tag number,bin location,bin name,status(active or inactive)
    #return HttpResponse("<h1> report "+ str(inspect.stack()[0][3]) +"</h1>")
    return render(request,'reports/bin_rfid_tag_status.html',{ 'form_params' : form_params })

##done
def garage_traction(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
#        bin_status= form_data['selectStatus'] == 'active' and True or False
#        wards  = list(map(lambda ward : Ward.objects.get(pk=ward) , form_data['selectWard'].split("_")))
#
#        for each_ward in wards:
#            for each_bin in each_ward.bins.filter(is_active=bin_status):
#                each_bin_data = dict()
#                each_bin_data['name'] = each_bin.name
#                each_bin_data['id'] = each_bin.id
#                #each_bin_data['location'] = each_bin.bin_location
#                each_bin_data['rfid'] = each_bin.tag
#                each_bin_data['status'] = 'active'
#                response_data['data'].append(each_bin_data)

        return HttpResponse(json.dumps(response_data),content_type="application/json")
    #fields required div,garage,vehicle,date range,shift
    #return HttpResponse("<h1> report "+ str(inspect.stack()[0][3]) +"</h1>")
    return render(request,'reports/garage_traction.html',{ 'form_params' : form_params })

##done
def land_fill_site_usage_current(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
        from_date = date.today() - timedelta(days = 10)
        dmpgnds  = list(map(lambda dmpgnd : Stop_station.objects.get(pk=dmpgnd) , form_data['selectDumpingGround'].split("_")))

        for each_dmpgnd in dmpgnds:
            for each_wt_entry in each_dmpgnd.weight_historys.filter(datetime__date=from_date):
                each_wt_record = dict()
                each_wt_record['dmpgnd'] = each_dmpgnd.name
                each_wt_record['vehicle'] = each_wt_entry.vehicle.plate_number
                each_wt_record['weight'] = each_wt_entry.weight
                each_wt_record['time'] = each_wt_entry.datetime.strftime("%Y-%m-%d %H:%M:%S")
                response_data['data'].append(each_wt_record)
        return HttpResponse(json.dumps(response_data),content_type="application/json")

    return render(request,'reports/land_fill_site_usage_current.html',{ 'form_params' : form_params })

##done
def land_fill_site_usage_dumping_groundwise(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
        from_date = dateutil.parser.parse(form_data['from_time']).date()
        to_date = dateutil.parser.parse(form_data['to_time']).date()
        shift = form_data['selectShift']
        dmpgnds  = list(map(lambda dmpgnd : Stop_station.objects.get(pk=dmpgnd) , form_data['selectDumpingGround'].split("_")))

        for each_dmpgnd in dmpgnds:
            if int(shift):
                whs= each_dmpgnd.weight_historys.filter(shift=shift).filter(datetime__date__range=(from_date,to_date)).values('stop_station').annotate(total_vehicle=Count('id')).annotate(total_weight=Sum('weight')).order_by()
            else:
                whs= each_dmpgnd.weight_historys.filter(datetime__date__range=(from_date,to_date)).values('stop_station').annotate(total_vehicle=Count('id')).annotate(total_weight=Sum('weight')).order_by()

            if not whs.count():
                continue

            for each_wh in whs:
                each_wt_record = dict()
                each_wt_record['dmpgnd'] = each_dmpgnd.name
                each_wt_record['in_vehicle'] = each_wh['total_vehicle']
                each_wt_record['out_vehicle'] = each_wh['total_vehicle']
                each_wt_record['net_weight'] = each_wh['total_weight']
                response_data['data'].append(each_wt_record)
        return HttpResponse(json.dumps(response_data),content_type="application/json")
    return render(request,'reports/land_fill_site_usage_dumping_groundwise.html',{ 'form_params' : form_params })

##done
def land_fill_site_usage_weightwise(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
        from_date = dateutil.parser.parse(form_data['from_time']).date()
        to_date = dateutil.parser.parse(form_data['to_time']).date()
        shift = form_data['selectShift']
        dmpgnds  = list(map(lambda dmpgnd : Stop_station.objects.get(pk=dmpgnd) , form_data['selectDumpingGround'].split("_")))

        for each_dmpgnd in dmpgnds:
            if int(shift):
                whs= each_dmpgnd.weight_historys.filter(shift=shift).filter(datetime__date__range=(from_date,to_date)).values('vehicle').annotate(total_weight=Sum('weight')).order_by()
            else:
                whs= each_dmpgnd.weight_historys.filter(datetime__date__range=(from_date,to_date)).values('vehicle','shift').annotate(total_weight=Sum('weight')).order_by()

            if not whs.count():
                continue

            for each_wh in whs:
                each_wt_record = dict()
                each_wt_record['dmpgnd'] = each_dmpgnd.name
                each_wt_record['vehicle'] = Vehicle.objects.get(id=each_wh['vehicle']).plate_number
                each_wt_record['shift'] = each_wh['shift']
                each_wt_record['weight'] = each_wh['total_weight']
                response_data['data'].append(each_wt_record)
        return HttpResponse(json.dumps(response_data),content_type="application/json")
    return render(request,'reports/land_fill_site_usage_weightwise.html',{ 'form_params' : form_params })

##done
def location_check_post(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
#        bin_status= form_data['selectStatus'] == 'active' and True or False
#        wards  = list(map(lambda ward : Ward.objects.get(pk=ward) , form_data['selectWard'].split("_")))
#
#        for each_ward in wards:
#            for each_bin in each_ward.bins.filter(is_active=bin_status):
#                each_bin_data = dict()
#                each_bin_data['name'] = each_bin.name
#                each_bin_data['id'] = each_bin.id
#                #each_bin_data['location'] = each_bin.bin_location
#                each_bin_data['rfid'] = each_bin.tag
#                each_bin_data['status'] = 'active'
#                response_data['data'].append(each_bin_data)
#
        return HttpResponse(json.dumps(response_data),content_type="application/json")

    return render(request,'reports/location_check_post.html',{ 'form_params' : form_params })

##done
def location_dumping_ground(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
#        bin_status= form_data['selectStatus'] == 'active' and True or False
#        wards  = list(map(lambda ward : Ward.objects.get(pk=ward) , form_data['selectWard'].split("_")))
#
#        for each_ward in wards:
#            for each_bin in each_ward.bins.filter(is_active=bin_status):
#                each_bin_data = dict()
#                each_bin_data['name'] = each_bin.name
#                each_bin_data['id'] = each_bin.id
#                #each_bin_data['location'] = each_bin.bin_location
#                each_bin_data['rfid'] = each_bin.tag
#                each_bin_data['status'] = 'active'
#                response_data['data'].append(each_bin_data)

        return HttpResponse(json.dumps(response_data),content_type="application/json")
    #fields required dmpgnd,vehicle,shift,date range parameter

    return render(request,'reports/location_dumping_ground.html',{ 'form_params' : form_params })

##done
def location_garage(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
#        bin_status= form_data['selectStatus'] == 'active' and True or False
#        wards  = list(map(lambda ward : Ward.objects.get(pk=ward) , form_data['selectWard'].split("_")))
#
#        for each_ward in wards:
#            for each_bin in each_ward.bins.filter(is_active=bin_status):
#                each_bin_data = dict()
#                each_bin_data['name'] = each_bin.name
#                each_bin_data['id'] = each_bin.id
#                #each_bin_data['location'] = each_bin.bin_location
#                each_bin_data['rfid'] = each_bin.tag
#                each_bin_data['status'] = 'active'
#                response_data['data'].append(each_bin_data)

        return HttpResponse(json.dumps(response_data),content_type="application/json")

    return render(request,'reports/location_garage.html',{ 'form_params' : form_params })

##done
def location_mlc(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
#        bin_status= form_data['selectStatus'] == 'active' and True or False
#        wards  = list(map(lambda ward : Ward.objects.get(pk=ward) , form_data['selectWard'].split("_")))
#
#        for each_ward in wards:
#            for each_bin in each_ward.bins.filter(is_active=bin_status):
#                each_bin_data = dict()
#                each_bin_data['name'] = each_bin.name
#                each_bin_data['id'] = each_bin.id
#                #each_bin_data['location'] = each_bin.bin_location
#                each_bin_data['rfid'] = each_bin.tag
#                each_bin_data['status'] = 'active'
#                response_data['data'].append(each_bin_data)

        return HttpResponse(json.dumps(response_data),content_type="application/json")

    return render(request,'reports/location_mlc.html',{ 'form_params' : form_params })

##done
def location_transfer_station(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
#        bin_status= form_data['selectStatus'] == 'active' and True or False
#        wards  = list(map(lambda ward : Ward.objects.get(pk=ward) , form_data['selectWard'].split("_")))
#
#        for each_ward in wards:
#            for each_bin in each_ward.bins.filter(is_active=bin_status):
#                each_bin_data = dict()
#                each_bin_data['name'] = each_bin.name
#                each_bin_data['id'] = each_bin.id
#                #each_bin_data['location'] = each_bin.bin_location
#                each_bin_data['rfid'] = each_bin.tag
#                each_bin_data['status'] = 'active'
#                response_data['data'].append(each_bin_data)

        return HttpResponse(json.dumps(response_data),content_type="application/json")
    #fields required transfer_station,vehicle,shift,date range parameter
    #return HttpResponse("<h1> report "+ str(inspect.stack()[0][3]) +"</h1>")
    return render(request,'reports/location_transfer_station.html',{ 'form_params' : form_params })

def poi_departmental_offices(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']
    #fields required div,zone,ward
    #return HttpResponse("<h1> report "+ str(inspect.stack()[0][3]) +"</h1>")
    return render(request,'reports/poi_departmental_offices.html',{ 'form_params' : form_params })

def poi_departmental_workshops(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']
    #fields required div,zone,ward
    #return HttpResponse("<h1> report "+ str(inspect.stack()[0][3]) +"</h1>")
    return render(request,'reports/poi_departmental_workshops.html',{ 'form_params' : form_params })

def poi_dmpgnd(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']
    #fields required div,zone,ward
    #return HttpResponse("<h1> report "+ str(inspect.stack()[0][3]) +"</h1>")
    return render(request,'reports/poi_dmpgnd.html',{ 'form_params' : form_params })

def poi_garbage_collection_points(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']
    #fields required div,zone,ward
    #return HttpResponse("<h1> report "+ str(inspect.stack()[0][3]) +"</h1>")
    return render(request,'reports/poi_garbage_collection_points.html',{ 'form_params' : form_params })

def poi_mlcs(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']
    #fields required div,zone,ward
    #return HttpResponse("<h1> report "+ str(inspect.stack()[0][3]) +"</h1>")
    return render(request,'reports/poi_mlcs.html',{ 'form_params' : form_params })

def poi_other_points(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']
    #fields required div,zone,ward
    #return HttpResponse("<h1> report "+ str(inspect.stack()[0][3]) +"</h1>")
    return render(request,'reports/poi_other_points.html',{ 'form_params' : form_params })

def poi_station_locations(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']
    #fields required div,zone,ward
    #return HttpResponse("<h1> report "+ str(inspect.stack()[0][3]) +"</h1>")
    return render(request,'reports/poi_station_locations.html',{ 'form_params' : form_params })

def poi_swm_garages(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']
    #fields required div,zone,ward
    #return HttpResponse("<h1> report "+ str(inspect.stack()[0][3]) +"</h1>")
    return render(request,'reports/poi_swm_garages.html',{ 'form_params' : form_params })

def poi_swm_offices(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']
    #fields required div,zone,ward
    #return HttpResponse("<h1> report "+ str(inspect.stack()[0][3]) +"</h1>")
    return render(request,'reports/poi_swm_offices.html',{ 'form_params' : form_params })

def poi_transfer_stations(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']
    #fields required div,zone,ward
    #return HttpResponse("<h1> report "+ str(inspect.stack()[0][3]) +"</h1>")
    return render(request,'reports/poi_transfer_stations.html',{ 'form_params' : form_params })

def poi_ward_offices(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']
    #fields required div,zone,ward
    #return HttpResponse("<h1> report "+ str(inspect.stack()[0][3]) +"</h1>")
    return render(request,'reports/poi_ward_offices.html',{ 'form_params' : form_params })

def poi_work_sites(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']
    #fields required div,zone,ward
    #return HttpResponse("<h1> report "+ str(inspect.stack()[0][3]) +"</h1>")
    return render(request,'reports/poi_work_sites.html',{ 'form_params' : form_params })

def register_transfer_station_vehiclewise(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']
    #fields required transfer_station,date_range,shift
    #return HttpResponse("<h1> report "+ str(inspect.stack()[0][3]) +"</h1>")
    return render(request,'reports/register_transfer_station_vehiclewise.html',{ 'form_params' : form_params })

def register_vehicle(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
        vehicles  = list(map(lambda vehicle : Vehicle.objects.get(pk=vehicle) , form_data['selectVehicle'].split("_")))

# table: table which record rfid tag read entries of unregistered
# desc : get list windschedil tag read entry for a selected vehicle
# op   : vehicle,RFID tag,location,datetime(at which tag read)
#
#        for each_vehicle in vehicles:
#            for each_alert in each_vehicle.alerts.filter(created_at__range=(from_time,to_time)):
#                each_alert_data = dict()
#                each_alert_data['location'] = each_alert.location
#                each_alert_data['vehicle'] = each_vehicle.plate_number
#                each_alert_data['tag'] = 'geofence'
#                each_alert_data['time'] = each_vehicle.created_at.strftime("%Y-%m-%d %H:%M:%S")
#                response_data['data'].append(each_alert_data)
#
        return HttpResponse(json.dumps(response_data),content_type="application/json")

    #return HttpResponse("<h1> report "+ str(inspect.stack()[0][3]) +"</h1>")
    return render(request,'reports/register_vehicle.html',{ 'form_params' : form_params })

def stoppage(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']
    #fields required div,zone,ward,vehicle,date range parameter,stopage_time greater than
    #return HttpResponse("<h1> report "+ str(inspect.stack()[0][3]) +"</h1>")
    return render(request,'reports/stoppage.html',{ 'form_params' : form_params })

#done
def get_ward_report(request):
    return render(request,'reports/ward_report.html')

def get_weight_report(request):
    return render(request,'reports/weight_report.html')

def get_vehicle_tracking_report(request):
    return render(request,'reports/vehicle_tracking_report.html')

def get_vehicle_trace_report(request):
    return render(request,'reports/vehicle_trace_report.html')

def get_vehicle_status_report(request):
    return render(request,'reports/vehicle_status_report.html')

def get_vehicle_history_report(request):
    return render(request,'reports/vehicle_history_report.html')

def get_tracking_status_report(request):
    return render(request,'reports/tracking_status_report.html')

def get_location_report(request):
    return render(request,'reports/location_report.html')

def get_landfill_site_usage_report(request):
    return render(request,'reports/landfill_site_usage_report.html')

def get_garage_traction_report(request):
    return render(request,'reports/garage_traction_report.html')

def get_garage_report(request):
    return render(request,'reports/garage_report.html')

def get_garage_logsheet_report(request):
    return render(request,'reports/garage_logsheet_report.html')

def get_fuel_status_report(request):
    return render(request,'reports/fuel_status_report.html')

def get_bin_status_report(request):
    return render(request,'reports/bin_status_report.html')

def get_alert_report(request):
    return render(request,'reports/alert_report.html')

def vehicle_route_history(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
        from_time = dateutil.parser.parse(form_data['from_time'])
        to_time = dateutil.parser.parse(form_data['to_time'])
        vehicles  = list(map(lambda vehicle : Vehicle.objects.get(pk=vehicle) , form_data['selectVehicle'].split("_")))

# table: table which record rfid tag read entries of unregistered
# desc : get list windschedil tag read entry for a selected vehicle
# op   : vehicle,RFID tag,location,datetime(at which tag read)
#
#        for each_vehicle in vehicles:
#            for each_alert in each_vehicle.alerts.filter(created_at__range=(from_time,to_time)):
#                each_alert_data = dict()
#                each_alert_data['location'] = each_alert.location
#                each_alert_data['vehicle'] = each_vehicle.plate_number
#                each_alert_data['tag'] = 'geofence'
#                each_alert_data['time'] = each_vehicle.created_at.strftime("%Y-%m-%d %H:%M:%S")
#                response_data['data'].append(each_alert_data)
#
        return HttpResponse(json.dumps(response_data),content_type="application/json")

    #fields required div,zone,ward,vehicle,date range parameter
    #return HttpResponse("<h1> report "+ str(inspect.stack()[0][3]) +"</h1>")
    return render(request,'reports/vehicle_route_history.html',{ 'form_params' : form_params })

#done
def vehicle_summery(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
        from_time = dateutil.parser.parse(form_data['from_time'])
        to_time = dateutil.parser.parse(form_data['to_time'])
        vehicles  = list(map(lambda vehicle : Vehicle.objects.get(pk=vehicle) , form_data['selectVehicle'].split("_")))
    return render(request,'reports/vehicle_summery.html',{ 'form_params' : form_params } )

def by_datetime(ele):
    return ele.datetime

##done
def vehicle_route_report(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
        from_time = dateutil.parser.parse(form_data['from_time'])
        response_data['fromtime'] = str(from_time)
        to_time   = dateutil.parser.parse(form_data['to_time'])
        response_data['totime'] = str(to_time)
        plate_no  = form_data['vehicle']
        vehicle   = Vehicle.objects.get(plate_number=plate_no)
        vc = chain(vehicle.vehicle_tracklog_historys.filter(datetime__range=(from_time,to_time)).order_by('datetime').distinct('datetime'), vehicle.current_tracklog_historys.filter(datetime__range=(from_time,to_time)).order_by('datetime').distinct('datetime'))
        sorted_vc = sorted(vc,key=by_datetime)

        seen        = dict()
        speed_zero  = dict()

        #ajit's code block 1 starts - initializing the dictionary from txt file.
        mydict = {}
        filename = "../../../../../tmp/fulldata.txt"
        a_file = codecs.open(filename, encoding="utf-8")
        for line in a_file:
            key, value = line.split(":::")
            mydict[key] = value
        #ajit code block 1 ends here

        for each_vehicle_record in sorted_vc:
            #logic to skip consecutive stationary entries 
            if each_vehicle_record.speed == 0.0:
                if each_vehicle_record.speed in speed_zero.keys():
                    continue
                else:
                    speed_zero[each_vehicle_record.speed]=1
            else:
                speed_zero = {}

            #logic to keep a entry for a minute  
            tm_upto_minute = each_vehicle_record.datetime.strftime("%d_%m_%Y_%H_%M")
            if tm_upto_minute in seen.keys():
                continue
            else:
                seen[tm_upto_minute]=1

#            location=Point(float(each_vehicle_record.longitude), float(each_vehicle_record.latitude))
#            area    = None
#
#            try:
#                pass
#                #area = Ewd.objects.filter(ewd_fence__contains=location).get()
#            except:
#                area = None
#
#            area = area.name if area else ''

            #from here: ajit's code block 2 starts - computing and saving the addresses in the response data dictionary
            inputlat = each_vehicle_record.latitude
            inputlong = each_vehicle_record.longitude
            inputlatlong = str(inputlat)+","+str(inputlong)
            #accept the input and turn it into the nearest value whose answer we have in our text file database
            newlat = format((round(inputlat,6)),'.6f')
            newlong = format((round(inputlong, 6)),'.6f')
            latfract = int(newlat[3:9])
            longfract = int(newlong[3:9])
            latadjustmentoffset = latfract%1000
            if(int(newlat[0:2]) == 18):
                finallatfract = latfract+(999-latadjustmentoffset)
            else:
                finallatfract = latfract+(223-latadjustmentoffset)
                finallatfract = str(finallatfract).zfill(6)
            longadjustmentoffset = longfract%1000
            finallongfract = longfract+(896-longadjustmentoffset)
            latmain = int(math.floor(float(newlat)))
            longmain = int(math.floor(float(newlong)))
            finallatlong = str(latmain)+"."+str(finallatfract)+","+str(longmain)+"."+str(finallongfract)
            try:
                resultaddress = mydict[finallatlong]
                resultaddress = (resultaddress.split(","))[:2]
            except:
                resultaddress = "Out of Mumbai."
            #ajit code block 2 ends here

            each_vehicle_record_data = dict()
            each_vehicle_record_data['vehicle']     = plate_no
            each_vehicle_record_data['date']        = str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))
            each_vehicle_record_data['time']        = str(each_vehicle_record.datetime.strftime("%H:%M:%S"))
            each_vehicle_record_data['area']        = resultaddress
            each_vehicle_record_data['speed']       = str(each_vehicle_record.speed)
            response_data['data'].append(each_vehicle_record_data)
        return HttpResponse(json.dumps(response_data),content_type="application/json")
    return render(request,'reports/vehicle_route_report.html',{ 'form_params' : form_params})

##done
def vehicle_route_report_v2(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
        from_time = dateutil.parser.parse(form_data['from_time'])
        to_time   = dateutil.parser.parse(form_data['to_time'])
        plate_no  = form_data['vehicle']
        vehicle   = Vehicle.objects.get(plate_number=plate_no)
        vc = chain(vehicle.vehicle_tracklog_historys.filter(datetime__range=(from_time,to_time)).order_by('datetime').distinct('datetime'), vehicle.current_tracklog_historys.filter(datetime__range=(from_time,to_time)).order_by('datetime').distinct('datetime'))
        sorted_vc = sorted(vc,key=by_datetime)

        for each_vehicle_record in sorted_vc:
            each_vehicle_record_data = dict()
            each_vehicle_record_data['vehicle']     = plate_no
            each_vehicle_record_data['date']        = str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))
            each_vehicle_record_data['time']        = str(each_vehicle_record.datetime.strftime("%H:%M:%S"))
            each_vehicle_record_data['location']    = ''
            each_vehicle_record_data['speed']       = str(each_vehicle_record.speed)
            response_data['data'].append(each_vehicle_record_data)
        paginatorr = Paginator(response_data['data'], 100)
        first_page = paginatorr.page(1).object_list
        page_range = paginatorr.page_range
        context = {
            'paginatorr':paginatorr,
            'first_page':first_page,
            'page_range':page_range
        }
        page_n = request.POST.get('page_n', None)
        results['list'] = list(paginatorr.page(page_n).object_list.values('id', 'datetime'))
        return JsonResponse({"results":results})
        #return HttpResponse(json.dumps(response_data),content_type="application/json")
    return render(request,'reports/vehicle_route_report_v2.html',{ 'form_params' : form_params})

##done
def vehicle_status_bin_rfid_tag(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
        from_date = dateutil.parser.parse(form_data['from_date'])
        vehicles  = list(map(lambda vehicle : Vehicle.objects.get(pk=vehicle) , form_data['selectVehicle'].split("_")))

        for each_vehicle in vehicles:
            for each_tag in each_vehicle.tag_read_historys.filter(read_at__date=from_date):
                location = Point(float(each_tag.longitude), float(each_tag.latitude))
                ward = ''
                try:
                    ward = Ward.objects.filter(is_active='t').filter(ward_fence__contains=location).get().name
                except Exception as e:
                    print (str(e))

                each_tag_data = dict()
                each_tag_data['lat'] = str(each_tag.latitude)
                each_tag_data['lon'] = str(each_tag.longitude)
                each_tag_data['ward'] = ward
                each_tag_data['vehicle'] = each_vehicle.plate_number
                each_tag_data['tag'] = each_tag.tag
                each_tag_data['time'] = each_tag.read_at.strftime("%Y-%m-%d %H:%M:%S")
                each_tag_data['desc'] = 'valid RFID/GPS'
                response_data['data'].append(each_tag_data)

        return HttpResponse(json.dumps(response_data),content_type="application/json")
    #fields required div,zone,ward,vehicle,date parameter
    #return HttpResponse("<h1> report "+ str(inspect.stack()[0][3]) +"</h1>")
    return render(request,'reports/vehicle_status_bin_rfid_tag.html',{ 'form_params' : form_params })

##done
def vehicle_status_bin_rfid_tag_status(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
        from_date = date.today()
        vehicles  = list(map(lambda vehicle : Vehicle.objects.get(pk=vehicle) , form_data['selectVehicle'].split("_")))

        for each_vehicle in vehicles:
            each_tag_data = dict()
            each_tag_data['vehicle'] = each_vehicle.plate_number
            each_tag_data['from_date'] = from_date.strftime('%Y-%m-%d')
            last_read_tag = each_vehicle.tag_read_historys.filter(read_at__date=from_date).order_by('-read_at').first()
            print(last_read_tag)
            if last_read_tag:
                each_tag_data['rfid_status'] = 'Yes'
            else:
                each_tag_data['rfid_status'] = 'No'

            response_data['data'].append(each_tag_data)
        return HttpResponse(json.dumps(response_data),content_type="application/json")

    #return HttpResponse("<h1> report "+ str(inspect.stack()[0][3]) +"</h1>")
    return render(request,'reports/vehicle_status_bin_rfid_tag_status.html',{ 'form_params' : form_params })

##done
def vehicle_status_bin_rfid_tag_unregistered(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
        from_date = dateutil.parser.parse(form_data['from_date'])
        vehicles  = list(map(lambda vehicle : Vehicle.objects.get(pk=vehicle) , form_data['selectVehicle'].split("_")))

        for each_vehicle in vehicles:
            for each_tag in each_vehicle.tag_read_historys.filter(is_registered=False).filter(read_at__date=from_date):
                location = Point(float(each_tag.longitude), float(each_tag.latitude))
                ward = ''
                try:
                    ward = Ward.objects.filter(is_active='t').filter(ward_fence__contains=location).get().name
                except Exception as e:
                    print (str(e))

                each_tag_data = dict()
                each_tag_data['lat'] = str(each_tag.latitude)
                each_tag_data['lon'] = str(each_tag.longitude)
                each_tag_data['ward'] = ward
                each_tag_data['vehicle'] = each_vehicle.plate_number
                each_tag_data['tag'] = each_tag.tag
                each_tag_data['time'] = each_tag.read_at.strftime("%Y-%m-%d %H:%M:%S")
                each_tag_data['desc'] = 'valid RFID/GPS'
                response_data['data'].append(each_tag_data)

        return HttpResponse(json.dumps(response_data),content_type="application/json")
    return render(request,'reports/vehicle_status_bin_rfid_tag_unregistered.html',{ 'form_params' : form_params })

##done
def vehicle_wind_schield_tag(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
        from_time = dateutil.parser.parse(form_data['from_time'])
        to_time = dateutil.parser.parse(form_data['to_time'])
        vehicles  = list(map(lambda vehicle : Vehicle.objects.get(pk=vehicle) , form_data['selectVehicle'].split("_")))

        for each_vehicle in vehicles:
            for each_tag in each_vehicle.tag_read_historys.filter(tag_type='W').filter(read_at__range=(from_time,to_time)):
                location = Point(float(each_tag.longitude), float(each_tag.latitude))
                ward = ''
                try:
                    ward = Ward.objects.filter(is_active='t').filter(ward_fence__contains=location).get().name
                except Exception as e:
                    print (str(e))

                each_tag_data = dict()
                each_tag_data['lat'] = str(each_tag.latitude)
                each_tag_data['lon'] = str(each_tag.longitude)
                each_tag_data['ward'] = ward
                each_tag_data['vehicle'] = each_vehicle.plate_number
                each_tag_data['tag'] = each_tag.tag
                each_tag_data['time'] = each_tag.read_at.strftime("%Y-%m-%d %H:%M:%S")
                response_data['data'].append(each_tag_data)

        return HttpResponse(json.dumps(response_data),content_type="application/json")
    return render(request,'reports/vehicle_wind_schield_tag.html',{ 'form_params' : form_params })

##done
def vehicle_trace(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
        from_date = dateutil.parser.parse(form_data['from_date'])
        vehicles  = list(map(lambda vehicle : Vehicle.objects.get(pk=vehicle) , form_data['selectVehicle'].split("_")))
# table: activity_log
# desc : last recorded entry for that vehicle for respective date
# op   : vehicle,RFID tag,location,datetime(at which tag read)
#
#        for each_vehicle in vehicles:
#            for each_alert in each_vehicle.alerts.filter(created_at__range=(from_time,to_time)):
#                each_alert_data = dict()
#                each_alert_data['location'] = each_alert.location
#                each_alert_data['vehicle'] = each_vehicle.plate_number
#                each_alert_data['tag'] = 'geofence'
#                each_alert_data['time'] = each_vehicle.created_at.strftime("%Y-%m-%d %H:%M:%S")
#                response_data['data'].append(each_alert_data)
#
        return HttpResponse(json.dumps(response_data),content_type="application/json")

    #return HttpResponse("<h1> report "+ str(inspect.stack()[0][3]) +"</h1>")
    return render(request,'reports/vehicle_trace.html',{ 'form_params' : form_params })

##done
def vehicle_tracking(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
        vehicles  = list(map(lambda vehicle : Vehicle.objects.get(pk=vehicle) , form_data['selectVehicle'].split("_")))
# table: activity log
# desc : get latest entry for a selected vehicle
# op   : Garage,vehicle,veh_type,veh category,location,last updated datetime(at which tag read)
#
#        for each_vehicle in vehicles:
#            for each_alert in each_vehicle.alerts.filter(created_at__range=(from_time,to_time)):
#                each_alert_data = dict()
#                each_alert_data['location'] = each_alert.location
#                each_alert_data['vehicle'] = each_vehicle.plate_number
#                each_alert_data['tag'] = 'geofence'
#                each_alert_data['time'] = each_vehicle.created_at.strftime("%Y-%m-%d %H:%M:%S")
#                response_data['data'].append(each_alert_data)
#
        return HttpResponse(json.dumps(response_data),content_type="application/json")

    #fields required garage,vehicle,veh_type,veh category,last_updated_time,location
    return render(request,'reports/vehicle_tracking.html',{ 'form_params' : form_params })

def weight_locationwise(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
#        from_time = dateutil.parser.parse(form_data['from_time'])
#        to_time = dateutil.parser.parse(form_data['to_time'])
#        vehicles  = list(map(lambda vehicle : Vehicle.objects.get(pk=vehicle) , form_data['selectVehicle'].split("_")))
#
#        for each_vehicle in vehicles:
#            for each_alert in each_vehicle.alerts.filter(created_at__range=(from_time,to_time)):
#                each_alert_data = dict()
#                each_alert_data['sub_category'] = each_alert.sub_category
#                each_alert_data['message'] = each_alert.message
#                each_alert_data['location'] = each_alert.location
#                each_alert_data['vehicle'] = each_vehicle.plate_number
#                each_alert_data['alert'] = 'geofence'
#                each_alert_data['time'] = each_vehicle.created_at.strftime("%Y-%m-%d %H:%M:%S")
#                response_data['data'].append(each_alert_data)
#
        return HttpResponse(json.dumps(response_data),content_type="application/json")

    #fields required ward,bin_location,date_range
    #return HttpResponse("<h1> report "+ str(inspect.stack()[0][3]) +"</h1>")
    return render(request,'reports/weight_locationwise.html',{ 'form_params' : form_params })

##done
def weight_wardwise(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
        from_time = dateutil.parser.parse(form_data['from_time'])
        to_time = dateutil.parser.parse(form_data['to_time'])
        shift = form_data['selectShift']
        wards  = list(map(lambda ward : Ward.objects.get(pk=ward) , form_data['selectWard'].split("_")))

        wardwise_weight_data = {}

        for each_ward in wards:
            if not Ward_Contractor_Mapping.objects.filter(ward=each_ward):
                continue
            #get contractor for ward
            #ward_contractor_map = Ward_Contractor_Mapping.objects.filter(ward=each_ward).get()

            if each_ward.name not in wardwise_weight_data:
                wardwise_weight_data[each_ward.name]=dict()

            for each_vehicle in Vehicle.objects.filter(ward = each_ward ):
                if each_vehicle.vehicle_type not in wardwise_weight_data[each_ward.name]:
                    wardwise_weight_data[each_ward.name][each_vehicle.vehicle_type] = dict()
                if int(shift):
                    whs=each_vehicle.weight_historys.filter(datetime__range=(from_time,to_time)).filter(shift=shift).values('shift').annotate(total_weight=Sum('weight')).annotate(total_count=Count('id')).order_by()
                    vehicle_route_schedules = each_vehicle.route_schedules.filter(is_active=True).filter(shift=shift)
                else:
                    whs=each_vehicle.weight_historys.filter(datetime__range=(from_time,to_time)).values('shift').annotate(total_weight=Sum('weight')).annotate(total_count=Count('id')).order_by()
                    vehicle_route_schedules = each_vehicle.route_schedules.filter(is_active=True)

                if not whs.count():
                    continue

                for each_wh in whs:
                    if each_wh['shift'] not in wardwise_weight_data[each_ward.name][each_vehicle.vehicle_type] :
                        wardwise_weight_data[each_ward.name][each_vehicle.vehicle_type][each_wh['shift']] = dict()
                        wardwise_weight_data[each_ward.name][each_vehicle.vehicle_type][each_wh['shift']]['total_weight']=each_wh['total_weight']
                        wardwise_weight_data[each_ward.name][each_vehicle.vehicle_type][each_wh['shift']]['indent']=each_wh['total_count']
                        wardwise_weight_data[each_ward.name][each_vehicle.vehicle_type][each_wh['shift']]['total_trip']=each_wh['total_count']
                        wardwise_weight_data[each_ward.name][each_vehicle.vehicle_type][each_wh['shift']]['recieved']=each_wh['total_count']
                        wardwise_weight_data[each_ward.name][each_vehicle.vehicle_type][each_wh['shift']]['total_bins']= 0
                        wardwise_weight_data[each_ward.name][each_vehicle.vehicle_type][each_wh['shift']]['collected_bins']=0
                    else:
                        wardwise_weight_data[each_ward.name][each_vehicle.vehicle_type][each_wh['shift']]['total_weight']+=each_wh['total_weight']

        response_data['data'] = wardwise_weight_data
        return HttpResponse(json.dumps(response_data),content_type="application/json")

    #wardwise aggragation of kilos of grabage within date range vehicle categoriwise
    return render(request,'reports/weight_wardwise.html',{ 'form_params' : form_params })

##done
def weight_zonewise(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
        from_time = dateutil.parser.parse(form_data['from_time'])
        to_time = dateutil.parser.parse(form_data['to_time'])
        shift = form_data['selectShift']
        zones  = list(map(lambda zone : Zone.objects.get(pk=zone) , form_data['selectZone'].split("_")))

        zonewise_weight_data = {}
        wardwise_weight_data = {}

        for each_zone in zones:
            zonewise_weight_data[each_zone.short_name] = {}
            for each_ward in each_zone.wards.all():
                if not Ward_Contractor_Mapping.objects.filter(ward=each_ward):
                    continue
                #get contractor for ward
                #ward_contractor_map = Ward_Contractor_Mapping.objects.filter(ward=each_ward).get()

                if each_ward.name not in wardwise_weight_data:
                    wardwise_weight_data[each_ward.name]=dict()

                for each_vehicle in Vehicle.objects.filter(ward=each_ward):
                    if each_vehicle.vehicle_type not in  zonewise_weight_data[each_zone.short_name]:
                        zonewise_weight_data[each_zone.short_name][each_vehicle.vehicle_type] = dict()
                    if int(shift):
                        whs=each_vehicle.weight_historys.filter(datetime__range=(from_time,to_time)).filter(shift=shift).values('shift').annotate(total_weight=Sum('weight')).annotate(total_count=Count('id')).order_by()
                        vehicle_route_schedules = each_vehicle.route_schedules.filter(is_active=True).filter(shift=shift)
                    else:
                        whs=each_vehicle.weight_historys.filter(datetime__range=(from_time,to_time)).values('shift').annotate(total_weight=Sum('weight')).annotate(total_count=Count('id')).order_by()
                        vehicle_route_schedules = each_vehicle.route_schedules.filter(is_active=True)

                    if not whs.count():
                        continue

                    for each_wh in whs:
                        if each_wh['shift'] not in zonewise_weight_data[each_zone.short_name][each_vehicle.vehicle_type] :
                            zonewise_weight_data[each_zone.short_name][each_vehicle.vehicle_type][each_wh['shift']] = dict()
                            zonewise_weight_data[each_zone.short_name][each_vehicle.vehicle_type][each_wh['shift']]['total_weight']=each_wh['total_weight']
                            zonewise_weight_data[each_zone.short_name][each_vehicle.vehicle_type][each_wh['shift']]['indent']=each_wh['total_count']
                            zonewise_weight_data[each_zone.short_name][each_vehicle.vehicle_type][each_wh['shift']]['total_trip']=each_wh['total_count']
                            zonewise_weight_data[each_zone.short_name][each_vehicle.vehicle_type][each_wh['shift']]['recieved']=each_wh['total_count']
                            zonewise_weight_data[each_zone.short_name][each_vehicle.vehicle_type][each_wh['shift']]['total_bins']= 0
                            zonewise_weight_data[each_zone.short_name][each_vehicle.vehicle_type][each_wh['shift']]['collected_bins']=0
                        else:
                            zonewise_weight_data[each_zone.short_name][each_vehicle.vehicle_type][each_wh['shift']]['total_weight']+=each_wh['total_weight']

        response_data['data'] = zonewise_weight_data
        print(response_data['data'])
        return HttpResponse(json.dumps(response_data),content_type="application/json")

# table: weight_log,activity_log
# desc : zonewise aggragation of kilos of grabage within date range vehicle categoriwise
# op   : zone,vehicle category,total bins to collect,total bins collected,total weight
#
#        for each_vehicle in vehicles:
#            for each_alert in each_vehicle.alerts.filter(created_at__range=(from_time,to_time)):
#                each_alert_data = dict()
#                each_alert_data['sub_category'] = each_alert.sub_category
#                each_alert_data['message'] = each_alert.message
#                each_alert_data['location'] = each_alert.location
#                each_alert_data['vehicle'] = each_vehicle.plate_number
#                each_alert_data['alert'] = 'geofence'
#                each_alert_data['time'] = each_vehicle.created_at.strftime("%Y-%m-%d %H:%M:%S")
#                response_data['data'].append(each_alert_data)
#
        return HttpResponse(json.dumps(response_data),content_type="application/json")

    #zonewise aggragation of kilos of grabage within date range vehicle categoriwise
    #columns zonename,vehicle category,trips,bin_collected,total bin weight
    return render(request,'reports/weight_zonewise.html',{ 'form_params' : form_params })

##done
def weight_history(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':
        response_data=dict()
        response_data['status'] = 'success'
        response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
        from_time = dateutil.parser.parse(form_data['from_time'])
        to_time = dateutil.parser.parse(form_data['to_time'])
        vehicles  = list(map(lambda vehicle : Vehicle.objects.get(pk=vehicle) , form_data['selectVehicle'].split("_")))

        for each_vehicle in vehicles:
            whs=each_vehicle.weight_historys.filter(datetime__range=(from_time,to_time)).values('stop_station','vehicle').annotate(total_weight=Sum('weight')).order_by('vehicle','stop_station')
            for each_wh in whs:
                each_wh_record = dict()
                each_wh_record['vehicle'] = Vehicle.objects.get(id=each_wh['vehicle']).plate_number
                each_wh_record['location'] = Stop_station.objects.get(id=each_wh['stop_station']).name
                each_wh_record['from_time'] = from_time.strftime("%Y-%m-%d %H:%M:%S")
                each_wh_record['to_time'] = to_time.strftime("%Y-%m-%d %H:%M:%S")
                each_wh_record['weight'] = each_wh['total_weight']
                response_data['data'].append(each_wh_record)

        return HttpResponse(json.dumps(response_data),content_type="application/json")
    #vehiclewise aggragation of kilos of garbage within date range vehicle categoriwise
    #return HttpResponse("<h1> report "+ str(inspect.stack()[0][3]) +"</h1>")
    return render(request,'reports/weight_history.html',{ 'form_params' : form_params })

##done
def get_vehicle_travel_history(request):
    response_data=dict()
    response_data['status'] = 'success'
    response_data['data'] = list()
    form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
    from_time = dateutil.parser.parse(form_data['from_time'])
    to_time = dateutil.parser.parse(form_data['to_time'])
    vehicle = Vehicle.objects.get(pk=form_data['selectVehicle'])
    vc = chain(vehicle.vehicle_tracklog_historys.filter(datetime__range=(from_time,to_time)).order_by('datetime') , vehicle.current_tracklog_historys.filter(datetime__range=(from_time,to_time)).order_by('datetime'))

    for each_vehicle_record in set(vc):
        each_vehicle_record_data = dict()
        each_vehicle_record_data['lat'] = str(each_vehicle_record.latitude)
        each_vehicle_record_data['lon'] = str(each_vehicle_record.longitude)
        each_vehicle_record_data['time'] = str(each_vehicle_record.datetime)
        each_vehicle_record_data['id'] = str(each_vehicle_record.id)
        each_vehicle_record_data['heading'] = str(each_vehicle_record.heading)   #Change made on 9th June
        each_vehicle_record_data['speed'] = str(each_vehicle_record.speed)
        each_vehicle_record_data['shift'] = str(each_vehicle_record.shift)
        each_vehicle_record_data['v_id'] = str(each_vehicle_record.vehicle_id)
        each_vehicle_record_data['plate_no'] = str(form_data['selectVehicle'])
        response_data['data'].append(each_vehicle_record_data)
    #vehicles  = list(map(lambda vehicle : Vehicle.objects.get(pk=vehicle) , form_data['selectVehicle'].split("_")))
    return HttpResponse(json.dumps(response_data),content_type="application/json")









#///////////////////////////////////////////////////////////////////////////////////




def generateps2pdf(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']

    if request.method == 'POST':

        #banned_vehicle_list = ["MH47Y5832","MH47Y5831","MH47Y5842","MH47Y5843","MH47Y6348","MH47Y6345","MH47Y6423","MH47Y6352","MH47Y6424","MH47Y6349","MH47Y6351","MH47Y6420","MH47Y6356","MH47Y6353","MH47Y6359","MH47Y6367","MH47Y6368","MH47Y6347","MH47Y6350","MH47Y6344","MH47Y6355","MH47Y6357","MH47Y6419","MH47Y6365","MH47Y6418","MH47Y6421","MH47Y6435","MH47Y6434","MH47Y6436","MH47Y6437","MH47Y6362","MH47Y6369","MH47Y6360","MH47Y6346","MH47Y6361","MH47Y6366","MH47Y5849","MH47Y6410","MH47Y6409","MH47Y6416","MH47Y6339","MH47Y6341","MH47Y6340","MH47Y6343","MH47Y6334","MH47Y6335","MH47Y6408","MH47Y6342","MH47Y6445","MH47Y6405","MH47Y6413","MH47Y6415","MH47Y6441","MH47Y6414","MH47Y6404","MH47Y6407","MH47Y6411","MH47Y6406","MH47Y6412","MH47Y6338","MH47Y6439","MH47Y6440","MH47Y6443","MH47Y6329","MH47Y6330","MH47Y6332","MH47Y6328","MH47Y6331","MH47Y6337","MH47Y6442","MH47Y6438","MH47Y6333","MH47Y5850","MH47Y6495","MH47Y6484","MH47Y6482","MH47Y6483","MH47Y6481","MH47Y6485","MH47AS1364","MH47AS1366","MH47AS1365","MH47Y7471","MH47Y7481","MH47Y7484","MH47Y7482","MH47Y7479","MH47Y7478","MH47Y7472","MH47Y7476","MH47Y7473","MH47Y7464","MH47Y7483","MH47Y7469","MH47Y7462","MH47Y7467","MH47Y7461","MH47Y7486","MH47Y7457","MH47Y7459","MH47Y7460","MH47Y7485","MH47Y7466","MH47Y7488","MH47Y7468","MH47Y7458","MH47Y7456","MH47Y7463","MH47Y7743","MH47Y7746","MH47Y7748","MH47Y8025","MH47Y8016","MH47Y7750","MH47Y7751","MH47Y7747","MH47Y8024","MH47Y8013","MH47Y8011","MH47Y8014","MH47Y8009","MH47Y8017","MH47Y8012","MH47Y8015","MH47Y7465","MH47Y8003","MH47Y7993","MH47Y7995","MH47Y7998","MH47Y7994","MH47Y7996","MH47Y8006","MH47Y8004","MH47Y8099","MH47Y8098","MH47Y8101","MH47Y8097","MH47Y8088","MH47Y8092","MH47Y8094","MH47Y8087","MH47Y8089","MH47Y8086","MH47Y8085","MH47Y8093","MH47Y8095","MH47Y8096","MH47Y8005","MH47Y8018","MH47Y7489","MH47Y7744","MH47Y7480","MH47Y8007","MH47Y8465","MH47Y8746","MH47Y8747"]
        banned_vehicle_list = []
        noPDF = "https://swm.vtms.cleanupmumbai.com/static/pdfreports/no_vehicle_route_report.pdf"
        #response_data=dict()
        #response_data['status'] = 'success'
        #response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
        from_time = dateutil.parser.parse(form_data['from_time'])
        #response_data['fromtime'] = str(from_time)
        to_time   = dateutil.parser.parse(form_data['to_time'])
        #response_data['totime'] = str(to_time)
        plate_no  = form_data['vehicle']
        if plate_no in banned_vehicle_list:
            return HttpResponse(noPDF)
        timedelay = form_data['timedelay']
        vehicle   = Vehicle.objects.get(plate_number=plate_no)
        vc = chain(vehicle.vehicle_tracklog_historys.filter(datetime__range=(from_time,to_time)).order_by('datetime').distinct('datetime'), vehicle.current_tracklog_historys.filter(datetime__range=(from_time,to_time)).order_by('datetime').distinct('datetime'))
        sorted_vc = sorted(vc,key=by_datetime)

        seen        = dict()
        speed_zero  = dict()

        #ajit's code block 1 starts - initializing the dictionary from txt file.
        mydict = {}
        filename = "../../../../../tmp/fulldata.txt"
        a_file = codecs.open(filename, encoding="utf-8")
        for line in a_file:
            key, value = line.split(":::")
            mydict[key] = value
        #ajit code block 1 ends here


        psfilename = "/home/mcgm/Development/mcgm/mcgm/static/pdfreports/"+str(plate_no)+"_"+str(from_time)+"_to_"+str(to_time)+".ps"
        pdffilename = "/home/mcgm/Development/mcgm/mcgm/static/pdfreports/"+str(plate_no)+"_"+str(from_time)+"_to_"+str(to_time)+".pdf"
        pdffilelink = "//swm.vtms.cleanupmumbai.com/static/pdfreports/"+str(plate_no)+"_"+str(from_time)+"_to_"+str(to_time)+".pdf"
        #replace all bad unix characters with underscores
        psfilename = psfilename.replace(" ", "_")
        psfilename = psfilename.replace(":", "_")
        pdffilename = pdffilename.replace(" ", "_")
        pdffilename = pdffilename.replace(":", "_")
        pdffilelink = pdffilelink.replace(" ", "_")
        pdffilelink= pdffilelink.replace(":", "_")
        pdffilelink = "http:"+pdffilelink




        now = datetime.now()
        # dd/mm/YY H:M:S
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")


        page1 = """%!PS-Adobe-2.0

%%FIRST_PAGE_START
%%IMAGE
/MCGM_LOGO
{
save
/showpage {} bind def
238 600 translate
0.5 0.5 scale
(/home/mcgm/Development/mcgm/mcgm/static/pdfreports/mcgmlogo.eps) run
restore
}def

%%PROCEDURE
/ReportNamefont
/Times findfont 20 scalefont def

/WORDS_FONT
/Helvetica-Bold findfont 12 scalefont def

/WORDS_DATA_FONT
/Helvetica findfont 12 scalefont def

/PrintReportName {
0 setgray 
216 550 moveto
ReportNamefont setfont
(Route Travel Report) show
}def

/FirstPageBorder
{
40 300 moveto
515 0 rlineto
0 230 rlineto
-515 0 rlineto
0 -400 rlineto 
closepath
%10 setlinewidth 
1 0.83 0.83 setrgbcolor fill
stroke
} def

/FirstPageFromBoxBorder
{
65 470 moveto
460 0 rlineto
0 20 rlineto
-460 0 rlineto
0 -20 rlineto 
closepath
%10 setlinewidth 
1 1 1 setrgbcolor fill
stroke
} def

/FirstPageTOBoxBorder
{
65 400 moveto
460 0 rlineto
0 20 rlineto
-460 0 rlineto
0 -20 rlineto 
closepath
%10 setlinewidth 
1 1 1 setrgbcolor fill
stroke
} def

/FirstPage3rdBoxBorder
{
65 330 moveto
460 0 rlineto
0 20 rlineto
-460 0 rlineto
0 -20 rlineto 
closepath
%10 setlinewidth 
1 1 1 setrgbcolor fill
stroke
} def
%%FIRST_PAGE_FINISH

%%SECOND_PAGE_START
%PROCEDURE
/HEADER_FONT
/Helvetica-Bold findfont 10 scalefont def

/DATA_FONT
/Helvetica findfont 9 scalefont def

%%%%%%%%%%%%PRINTING CODE %%MAIN CODE%%%%%%%%%%%%%%%%%%
%%%%%%%%%FIRSTPAGE 
1
{
FirstPageBorder
FirstPageFromBoxBorder
FirstPageTOBoxBorder
FirstPage3rdBoxBorder
PrintReportName
MCGM_LOGO

%FROM_WORD_1st_PAGE
0 setgray 65 500 moveto
WORDS_FONT setfont
(From:) show

%FROM_WORD_1st_PAGE
0 setgray 73 476 moveto
WORDS_DATA_FONT setfont
("""+str(from_time)+""") show

%TO_WORD_1st_PAGE
0 setgray 65 430 moveto
WORDS_FONT setfont
(To:) show

%FROM_WORD_1st_PAGE
0 setgray 73 406 moveto
WORDS_DATA_FONT setfont
("""+str(to_time)+""") show

%3rd_WORD_1st_PAGE
0 setgray 65 360 moveto
WORDS_FONT setfont
(Report Generated Date:) show

%FROM_WORD_1st_PAGE
0 setgray 73 336 moveto
WORDS_DATA_FONT setfont
("""+dt_string+""") show

showpage
} repeat"""


        # Append-adds at last
        #htmlfile = open(htmlfilename, "a")  # append mode
        psfile = open(psfilename, "a", encoding="utf-8")
        psfile.write(page1)




        loopcounter = 1
        pagerowcounter = 0
        for each_vehicle_record in sorted_vc:
            #logic to skip consecutive stationary entries 
            #if each_vehicle_record.speed == 0.0:
            #    if each_vehicle_record.speed in speed_zero.keys():
            #        continue
            #    else:
            #        speed_zero[each_vehicle_record.speed]=1
            #else:
            #    speed_zero = {}

            #logic to keep a entry for a minute  
            tm_upto_minute = each_vehicle_record.datetime.strftime("%d_%m_%Y_%H_%M")
            if tm_upto_minute in seen.keys():
                continue
            else:
                if(timedelay == "1"):
                    seen[tm_upto_minute]=1
                elif(timedelay == "2"):
                    seen[tm_upto_minute]=1

                    dt_obj = datetime.strptime(tm_upto_minute, "%d_%m_%Y_%H_%M")
                    final_time = dt_obj + timedelta(minutes=1)
                    final_time_str = final_time.strftime('%d_%m_%Y_%H_%M')
                    seen[final_time_str]=1

                elif(timedelay == "5"):
                    seen[tm_upto_minute]=1

                    dt_obj = datetime.strptime(tm_upto_minute, "%d_%m_%Y_%H_%M")
                    final_time = dt_obj + timedelta(minutes=1)
                    final_time_str = final_time.strftime('%d_%m_%Y_%H_%M')
                    seen[final_time_str]=1

                    dt_obj = datetime.strptime(tm_upto_minute, "%d_%m_%Y_%H_%M")
                    final_time = dt_obj + timedelta(minutes=2)
                    final_time_str = final_time.strftime('%d_%m_%Y_%H_%M')
                    seen[final_time_str]=1

                    dt_obj = datetime.strptime(tm_upto_minute, "%d_%m_%Y_%H_%M")
                    final_time = dt_obj + timedelta(minutes=3)
                    final_time_str = final_time.strftime('%d_%m_%Y_%H_%M')
                    seen[final_time_str]=1

                    dt_obj = datetime.strptime(tm_upto_minute, "%d_%m_%Y_%H_%M")
                    final_time = dt_obj + timedelta(minutes=4)
                    final_time_str = final_time.strftime('%d_%m_%Y_%H_%M')
                    seen[final_time_str]=1

                #10-min delay
                else:
                    seen[tm_upto_minute]=1

                    dt_obj = datetime.strptime(tm_upto_minute, "%d_%m_%Y_%H_%M")
                    final_time = dt_obj + timedelta(minutes=1)
                    final_time_str = final_time.strftime('%d_%m_%Y_%H_%M')
                    seen[final_time_str]=1

                    dt_obj = datetime.strptime(tm_upto_minute, "%d_%m_%Y_%H_%M")
                    final_time = dt_obj + timedelta(minutes=2)
                    final_time_str = final_time.strftime('%d_%m_%Y_%H_%M')
                    seen[final_time_str]=1

                    dt_obj = datetime.strptime(tm_upto_minute, "%d_%m_%Y_%H_%M")
                    final_time = dt_obj + timedelta(minutes=3)
                    final_time_str = final_time.strftime('%d_%m_%Y_%H_%M')
                    seen[final_time_str]=1

                    dt_obj = datetime.strptime(tm_upto_minute, "%d_%m_%Y_%H_%M")
                    final_time = dt_obj + timedelta(minutes=4)
                    final_time_str = final_time.strftime('%d_%m_%Y_%H_%M')
                    seen[final_time_str]=1

                    dt_obj = datetime.strptime(tm_upto_minute, "%d_%m_%Y_%H_%M")
                    final_time = dt_obj + timedelta(minutes=5)
                    final_time_str = final_time.strftime('%d_%m_%Y_%H_%M')
                    seen[final_time_str]=1
                
                    dt_obj = datetime.strptime(tm_upto_minute, "%d_%m_%Y_%H_%M")
                    final_time = dt_obj + timedelta(minutes=6)
                    final_time_str = final_time.strftime('%d_%m_%Y_%H_%M')
                    seen[final_time_str]=1

                    dt_obj = datetime.strptime(tm_upto_minute, "%d_%m_%Y_%H_%M")
                    final_time = dt_obj + timedelta(minutes=7)
                    final_time_str = final_time.strftime('%d_%m_%Y_%H_%M')
                    seen[final_time_str]=1

                    dt_obj = datetime.strptime(tm_upto_minute, "%d_%m_%Y_%H_%M")
                    final_time = dt_obj + timedelta(minutes=8)
                    final_time_str = final_time.strftime('%d_%m_%Y_%H_%M')
                    seen[final_time_str]=1

                    dt_obj = datetime.strptime(tm_upto_minute, "%d_%m_%Y_%H_%M")
                    final_time = dt_obj + timedelta(minutes=9)
                    final_time_str = final_time.strftime('%d_%m_%Y_%H_%M')
                    seen[final_time_str]=1

                
                

#            location=Point(float(each_vehicle_record.longitude), float(each_vehicle_record.latitude))
#            area    = None
#
#            try:
#                pass
#                #area = Ewd.objects.filter(ewd_fence__contains=location).get()
#            except:
#                area = None
#
#            area = area.name if area else ''

            #from here: ajit's code block 2 starts - computing and saving the addresses in the response data dictionary
            inputlat = each_vehicle_record.latitude
            inputlong = each_vehicle_record.longitude
            inputlatlong = str(inputlat)+","+str(inputlong)
            #accept the input and turn it into the nearest value whose answer we have in our text file database
            newlat = format((round(inputlat,6)),'.6f')
            newlong = format((round(inputlong, 6)),'.6f')
            latfract = int(newlat[3:9])
            longfract = int(newlong[3:9])
            latadjustmentoffset = latfract%1000
            if(int(newlat[0:2]) == 18):
                finallatfract = latfract+(999-latadjustmentoffset)
            else:
                finallatfract = latfract+(223-latadjustmentoffset)
                finallatfract = str(finallatfract).zfill(6)
            longadjustmentoffset = longfract%1000
            finallongfract = longfract+(896-longadjustmentoffset)
            latmain = int(math.floor(float(newlat)))
            longmain = int(math.floor(float(newlong)))
            finallatlong = str(latmain)+"."+str(finallatfract)+","+str(longmain)+"."+str(finallongfract)
            try:
                resultaddress = mydict[finallatlong]
                resultaddress = (resultaddress.split(","))[:2]
            except:
                resultaddress = "Out of Mumbai."
            #ajit code block 2 ends here


            finalresultaddress = ""
            finalresultaddress = finalresultaddress.join(resultaddress)
            finalresultaddress = finalresultaddress[0:40]
            finalresultaddress = finalresultaddress.replace("(", " ")
            finalresultaddress = finalresultaddress.replace(")", " ")
            charcount = 40
            if(len(finalresultaddress) == 40):
                while(finalresultaddress[charcount-1]!= " " ):
                    charcount-=1
            finalresultaddress = finalresultaddress = finalresultaddress[0:charcount]

            finalspeed = ""
            finalspeed = finalspeed.join(str(each_vehicle_record.speed))


            if(pagerowcounter == 0):
                staticdata = """\n%%%%%%%%%SECONDPAGE
%%SECOND_PAGE_NUMBERS_TO_BE_PRINTED%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
1
{
%TABLE BORDER
newpath
50 54 moveto     %BOTTOM CORNER
0 680 rlineto    %Y-AXIS UP
496 0 rlineto    %X-AXIS RIGHT
0 -680 rlineto   %Y-AXIS DOWN
-496 0 rlineto   %X-AXIS LEFT
0 setlinewidth   %THICKNESS
stroke           %PRINT

%COLUMN LINES(1,2,3,4,5)
newpath
85 54 moveto    %TO CHANGE VERTICAL LINES
0 680 rlineto   %BOTTOM-UP LENGTH
stroke

newpath
150 54 moveto
0 680 rlineto
stroke

newpath
215 54 moveto
0 680 rlineto
stroke

newpath
270 54 moveto
0 680 rlineto
stroke

newpath
490 54 moveto
0 680 rlineto
stroke

newpath
50 734 moveto
496 0 rlineto
stroke

newpath
50 714 moveto
496 0 rlineto
stroke

newpath
50 694 moveto
496 0 rlineto
stroke

newpath
50 674 moveto
496 0 rlineto
stroke

newpath
50 654 moveto
496 0 rlineto
stroke

newpath
50 634 moveto
496 0 rlineto
stroke

newpath
50 614 moveto
496 0 rlineto
stroke

newpath
50 594 moveto
496 0 rlineto
stroke

newpath
50 574 moveto
496 0 rlineto
stroke

newpath
50 554 moveto
496 0 rlineto
stroke

newpath
50 534 moveto
496 0 rlineto
stroke

newpath
50 514 moveto
496 0 rlineto
stroke

newpath
50 494 moveto
496 0 rlineto
stroke

newpath
50 474 moveto
496 0 rlineto
stroke

newpath
50 454 moveto
496 0 rlineto
stroke

newpath
50 434 moveto
496 0 rlineto
stroke

newpath
50 414 moveto
496 0 rlineto
stroke

newpath
50 394 moveto
496 0 rlineto
stroke

newpath
50 374 moveto
496 0 rlineto
stroke

newpath
50 354 moveto
496 0 rlineto
stroke

newpath
50 334 moveto
496 0 rlineto
stroke

newpath
50 314 moveto
496 0 rlineto
stroke

newpath
50 294 moveto
496 0 rlineto
stroke

newpath
50 274 moveto
496 0 rlineto
stroke

newpath
50 254 moveto
496 0 rlineto
stroke

newpath
50 234 moveto
496 0 rlineto
stroke

newpath
50 214 moveto
496 0 rlineto
stroke

newpath
50 194 moveto
496 0 rlineto
stroke

newpath
50 174 moveto
496 0 rlineto
stroke

newpath
50 154 moveto
496 0 rlineto
stroke

newpath
50 134 moveto
496 0 rlineto
stroke

newpath
50 114 moveto
496 0 rlineto
stroke

newpath
50 94 moveto
496 0 rlineto
stroke

newpath
50 74 moveto
496 0 rlineto
stroke

%-----------------------
%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 55 720 moveto   %CHANGE THIS TO MOVE HEADERS
HEADER_FONT setfont
(Index) show

%COLUMN_DATA_2st_PAGE
0 setgray 98 720 moveto   %CHANGE THIS TO MOVE HEADERS
HEADER_FONT setfont
(Vehicle) show

%COLUMN_DATA_2st_PAGE
0 setgray 168 720 moveto   %CHANGE THIS TO MOVE HEADERS
HEADER_FONT setfont
(Date) show

%COLUMN_DATA_2st_PAGE
0 setgray 231 720 moveto   %CHANGE THIS TO MOVE HEADERS
HEADER_FONT setfont
(Time) show

%COLUMN_DATA_2st_PAGE
0 setgray 350 720 moveto   %CHANGE THIS TO MOVE HEADERS
HEADER_FONT setfont
(Location) show

%COLUMN_DATA_2st_PAGE
0 setgray 505 720 moveto   %CHANGE THIS TO MOVE HEADERS
HEADER_FONT setfont
(Speed) show
%----------------------------
%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 700 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 700 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 700 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 700 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 700 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 700 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------
"""
                
                psfile.write(staticdata)
                pagerowcounter+=2
                loopcounter+=1




            elif(pagerowcounter == 2):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 680 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 680 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 680 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 680 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 680 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 680 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1


            elif(pagerowcounter == 3):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 660 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 660 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 660 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 660 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 660 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 660 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1

            elif(pagerowcounter == 4):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 640 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 640 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 640 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 640 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 640 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 640 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1


            elif(pagerowcounter == 5):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 620 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 620 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 620 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 620 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 620 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 620 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1

            elif(pagerowcounter == 6):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 600 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 600 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 600 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 600 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 600 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 600 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1


            elif(pagerowcounter == 7):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 580 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 580 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 580 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 580 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 580 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 580 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1


            elif(pagerowcounter == 8):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 560 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 560 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 560 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 560 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 560 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 560 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1

            elif(pagerowcounter == 9):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 540 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 540 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 540 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 540 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 540 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 540 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1

            elif(pagerowcounter == 10):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 520 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 520 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 520 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 520 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 520 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 520 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1


            elif(pagerowcounter == 11):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 500 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 500 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 500 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 500 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 500 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 500 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1

            elif(pagerowcounter == 12):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 480 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 480 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 480 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 480 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 480 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 480 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1

            elif(pagerowcounter == 13):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 460 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 460 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 460 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 460 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 460 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 460 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1

            elif(pagerowcounter == 14):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 440 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 440 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 440 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 440 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 440 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 440 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1


            elif(pagerowcounter == 15):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 420 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 420 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 420 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 420 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 420 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 420 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1



            elif(pagerowcounter == 16):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 400 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 400 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 400 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 400 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 400 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 400 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1


            elif(pagerowcounter == 17):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 380 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 380 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 380 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 380 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 380 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 380 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1


            elif(pagerowcounter == 18):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 360 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 360 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 360 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 360 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 360 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 360 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1

            elif(pagerowcounter == 19):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 340 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 340 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 340 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 340 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 340 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 340 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1

            elif(pagerowcounter == 20):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 320 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 320 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 320 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 320 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 320 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 320 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1

            elif(pagerowcounter == 21):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 300 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 300 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 300 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 300 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 300 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 300 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1

            elif(pagerowcounter == 22):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 280 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 280 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 280 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 280 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 280 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 280 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1


            elif(pagerowcounter == 23):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 260 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 260 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 260 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 260 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 260 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 260 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1

            elif(pagerowcounter == 24):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 240 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 240 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 240 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 240 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 240 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 240 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1

            elif(pagerowcounter == 25):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 220 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 220 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 220 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 220 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 220 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 220 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1

            elif(pagerowcounter == 26):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 200 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 200 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 200 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 200 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 200 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 200 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1

            elif(pagerowcounter == 27):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 180 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 180 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 180 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 180 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 180 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 180 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1

            elif(pagerowcounter == 28):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 160 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 160 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 160 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 160 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 160 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 160 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1

            elif(pagerowcounter == 29):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 140 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 140 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 140 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 140 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 140 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 140 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1

            elif(pagerowcounter == 30):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 120 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 120 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 120 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 120 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 120 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 120 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1

            elif(pagerowcounter == 31):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 100 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 100 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 100 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 100 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 100 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 100 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1

            elif(pagerowcounter == 32):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 80 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 80 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 80 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 80 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 80 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 80 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------"""

                psfile.write(appenddata)
                pagerowcounter+=1
                loopcounter+=1

            elif(pagerowcounter == 33):
                appenddata = """%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 58 60 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 92 60 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 158 60 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 225 60 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 275 60 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 510 60 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalspeed+""") show
%----------------------------
showpage
} repeat"""

                psfile.write(appenddata)
                pagerowcounter = 0
                loopcounter+=1

        if(pagerowcounter != 33):
            appenddata = """
showpage
} repeat"""
            psfile.write(appenddata)
        psfile.close()
        pdfgenerationcommand = "ps2pdf -dNOSAFER "+psfilename+" "+pdffilename
        
        """ each_vehicle_record_data = dict()
        each_vehicle_record_data['vehicle']     = plate_no
        each_vehicle_record_data['date']        = str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))
        each_vehicle_record_data['time']        = str(each_vehicle_record.datetime.strftime("%H:%M:%S"))
        each_vehicle_record_data['area']        = resultaddress
        each_vehicle_record_data['speed']       = str(each_vehicle_record.speed)
        response_data['data'].append(each_vehicle_record_data) """
        os.system(pdfgenerationcommand)
        os.remove(psfilename)
        #pdfaccesslink = "http://swm.vtms.cleanupmumbai.com/static/pdfreports/"+str(plate_no)+"_"+str(from_time)+"_to_"+str(to_time)+".pdf"
        return HttpResponse(pdffilelink)
    return render(request,'reports/vehicle_route_report.html',{ 'form_params' : form_params})

#API PART

@api_view(['POST'])
def sendWeighEntryData(request):
    if request.method == 'POST':
     data = request.data
     
     if len(data) == 12:
      
      try:
        connection = psycopg2.connect(user="mcgm",
                                  password="mcgm",
                                  host="localhost",
                                  port="5432",
                                  database="mcgm")
        cursor = connection.cursor()
        postgres_insert_query = """ INSERT INTO swm.sendweighentrydata (unique_transaction_id, weighbridge, trans_date, trans_time, vehicle_no, dc_no, act_shift, type_of_garage, vehicletype, gross_weight, new_weight, updatedby) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    
        #record_to_insert = (1663602, 'WB-D-Test', '2020\/12\/24', '1:56 PM', 'MH03CV0943', 10652, 'I', 'DEBRIS', 'PVT TORAS', 26960, 17460, 'SOMNATHS')
        #record_to_insert = (data["Unique_Transaction_ID"], data["Weighbridge_UL"], data["Trans_Date_UL"], data["Trans_Time_UL"], data["Vehicle_No"], data["Act_Shift_UL"], data["Unladen_Weight"], data["Act_Net_Weight"], data["Updated_by_UL"], data["Ward"], data["Image"])
        record_to_insert = (data["Unique_Transaction_ID"], data["Weighbridge"], data["Trans_Date"], data["Trans_Time"], data["Vehicle_No"], data["DC_No"], data["Act_Shift"], data["Type_of_Garbage"], data["Vehicle_Type"], data["Gross_Weight"], data["Net_Weight"], data["Updated_by"])
        cursor.execute(postgres_insert_query, record_to_insert)
        connection.commit()
        count = cursor.rowcount
      
      except (Exception, psycopg2.Error) as error:  
        print("Failed to insert ", error)  
      finally:
       if connection:
        cursor.close()
        connection.close()
        print("PostgreSQL connection is closed")  
        
      return JsonResponse({"response":"ACK","Transaction_ID": data["Unique_Transaction_ID"]},content_type="application/json")
    return JsonResponse({"response": "Error - Resend Packet"},content_type="application/json")   
  
  
@api_view(['POST'])
def sendWeighExitData(request):
    if request.method == 'POST':
     data = request.data
     
     if len(data) == 11:
      
      try:
        connection = psycopg2.connect(user="mcgm",
                                  password="mcgm",
                                  host="localhost",
                                  port="5432",
                                  database="mcgm")
        cursor = connection.cursor()
        postgres_insert_query = """ INSERT INTO swm.sendweighexitdata (unique_transaction_id, weighbridge_ul, trans_date_ul, trans_time_ul, vehicle_no, act_shift_ul, unladen_weight, act_net_weight, updatedby_ul, ward, invehicle_image) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        #record_to_insert = (24546, 'WB-D-Test', '2020\/12\/24', '1:49 PM', 'MH01AP7022', 'I', 9790, 6090, data["Updated_by"], 'N', 'http:\/\/45.117.74.126\/vehicleImages\/1663527.jpg')
        record_to_insert = (data["Unique_Transaction_ID"], data["Weighbridge_UL"], data["Trans_Date_UL"], data["Trans_Time_UL"], data["Vehicle_No"], data["Act_Shift_UL"], data["Unladen_Weight"], data["Act_Net_Weight"], data["Updated_by_UL"], data["Ward"], data["Image"])
        cursor.execute(postgres_insert_query, record_to_insert)
        connection.commit()
        count = cursor.rowcount
      
      except (Exception, psycopg2.Error) as error:  
        print("Failed to insert ", error)  
      finally:
       if connection:
        cursor.close()
        connection.close()
        print("PostgreSQL connection is closed")  
        
      return JsonResponse({"response":"ACK","Transaction_ID": data["Unique_Transaction_ID"]},content_type="application/json")
    return JsonResponse({"response": "Error - Resend Packet"},content_type="application/json")
