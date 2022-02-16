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
        to_time   = dateutil.parser.parse(form_data['to_time'])
        plate_no  = form_data['vehicle']
        vehicle   = Vehicle.objects.get(plate_number=plate_no)
        vc = chain(vehicle.vehicle_tracklog_historys.filter(datetime__range=(from_time,to_time)).order_by('datetime').distinct('datetime'), vehicle.current_tracklog_historys.filter(datetime__range=(from_time,to_time)).order_by('datetime').distinct('datetime'))
        sorted_vc = sorted(vc,key=by_datetime)

        seen        = dict()
        speed_zero  = dict()

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

            each_vehicle_record_data = dict()
            each_vehicle_record_data['vehicle']     = plate_no
            each_vehicle_record_data['date']        = str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))
            each_vehicle_record_data['time']        = str(each_vehicle_record.datetime.strftime("%H:%M:%S"))
            each_vehicle_record_data['area']        = ''
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
        response_data['data'].append(each_vehicle_record_data)
    #vehicles  = list(map(lambda vehicle : Vehicle.objects.get(pk=vehicle) , form_data['selectVehicle'].split("_")))
    return HttpResponse(json.dumps(response_data),content_type="application/json")
