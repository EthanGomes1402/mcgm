from django.shortcuts import render
from django.http import HttpResponse,JsonResponse
import json,re,string,random,inspect
from common.models import Ward
from swmadmin.models import Vehicle
from reports.models import Current_tracklog_history
from django.db.models.aggregates import Max
from django.contrib.gis.geos import GEOSGeometry,Point,LineString
from django.contrib.auth.decorators import login_required,user_passes_test

# Create your views here.
@login_required
@user_passes_test(lambda user: user.is_superuser or (user.appuser.is_contractor or user.appuser.is_officer))
def latest_vehicle_status(request):
    response_data=dict()
    response_data['status'] = 'success'
    response_data['data'] = list()

    for each_th_record_dict in Current_tracklog_history.objects.values('vehicle').annotate(max_id=Max('id')).order_by('max_id'):
        each_th_record = Current_tracklog_history.objects.get(id=each_th_record_dict['max_id'])
        each_vehicle_record_data = dict()
        each_vehicle_record_data['veh'] = str(each_th_record.vehicle)
        each_vehicle_record_data['veh_ward'] = str(each_th_record.vehicle.ward)
        each_vehicle_record_data['type'] = str(each_th_record.vehicle.vehicle_type)
        each_vehicle_record_data['lat'] = str(each_th_record.latitude)
        each_vehicle_record_data['lon'] = str(each_th_record.longitude)
        each_vehicle_record_data['location']=Point(float(each_th_record.longitude), float(each_th_record.latitude))
        try:
            each_vehicle_record_data['ward'] = Ward.objects.filter(is_active=True).filter(ward_fence__contains=each_vehicle_record_data['location']).get()
        except:
            each_vehicle_record_data['ward'] = None
        each_vehicle_record_data['time'] = str(each_th_record.datetime.strftime("%Y-%m-%d %H:%M:%S"))
        #logic will check if current time is in assigned route schedule for a vehicle
        each_vehicle_record_data['trip_status'] = 'In trip'
        each_vehicle_record_data['speed'] = each_th_record.speed
        if each_vehicle_record_data['speed']:
            if each_vehicle_record_data['speed'] > 60:
                each_vehicle_record_data['speed_status']='Above Alarming'
                each_vehicle_record_data['speed_class'] ='red'
                each_vehicle_record_data['veh_status'] ='Running'
                each_vehicle_record_data['veh_class'] ='green'
            elif each_vehicle_record_data['speed'] > 40 and each_vehicle_record_data['speed'] <= 60:
                each_vehicle_record_data['speed_status']='Alarming'
                each_vehicle_record_data['speed_class'] ='green'
                each_vehicle_record_data['veh_status'] ='Running'
                each_vehicle_record_data['veh_class'] ='green'
            else:
                each_vehicle_record_data['speed_status']='Normal'
                each_vehicle_record_data['speed_class'] ='orange'
                each_vehicle_record_data['veh_status'] ='Running'
                each_vehicle_record_data['veh_class'] ='green'
        else:
            each_vehicle_record_data['speed_status']='No Speed'
            each_vehicle_record_data['speed_class'] ='aqua'
            each_vehicle_record_data['veh_status'] ='Idle'
            each_vehicle_record_data['veh_class'] ='orange'

        each_vehicle_record_data['mps'] = str(each_th_record.mps)
        each_vehicle_record_data['miv'] = str(each_th_record.miv)
        each_vehicle_record_data['ibv'] = str(each_th_record.ibv)
        #each_vehicle_record_data['location'] = str(each_th_record.location)
        each_vehicle_record_data['ignition_status'] = str(each_th_record.ignition)
        each_vehicle_record_data['emergency_status'] = str(each_th_record.emergency)
        each_vehicle_record_data['digital_io_status'] = str(each_th_record.dio)
        response_data['data'].append(each_vehicle_record_data)
    #vehicles  = list(map(lambda vehicle : Vehicle.objects.get(pk=vehicle) , form_data['selectVehicle'].split("_")))
    return render(request,'dashboard/latest_vehicle_status.html',{ 'all_entries' : response_data['data'] })

@login_required
@user_passes_test(lambda user: user.is_superuser or (user.appuser.is_contractor or user.appuser.is_officer))
def quick_view(request):
    return render(request,'dashboard/quick_view.html',{})

def get_quick_view_form_param(request):
    form_parameters = dict()
    form_parameters['wards'] = []
    form_parameters['vehicles'] = []
    wards = Ward.objects.filter(is_active=True)
    vehicles = Vehicle.objects.filter(is_active=True)
    all_wards = list();
    all_vehicles = dict();

    for ward in wards:
        ward_info = dict()
        ward_info['id'] = ward.id
        ward_info['name'] = ward.name
        all_wards.append(ward_info)

    form_parameters['wards'] = all_wards

    for each_vehicle in vehicles:
        veh_type = str(each_vehicle.vehicle_type).lower()
        all_vehicles[veh_type]=list()

    for each_vehicle in vehicles:
        vehicle_info = dict()
        vehicle_info['id'] = each_vehicle.id
        vehicle_info['plate_number'] = each_vehicle.plate_number
        vehicle_info['type'] = str(each_vehicle.vehicle_type).lower()
        all_vehicles[vehicle_info['type']].append(vehicle_info)

    form_parameters['vehicles'] = all_vehicles

    response_data={}
    response_data['form_params'] = form_parameters
    response_data['status'] = 'success'
    return HttpResponse(json.dumps(response_data),content_type="application/json")
