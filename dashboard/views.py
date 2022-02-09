from django.shortcuts import render
from django.http import HttpResponse,JsonResponse
import json,re,string,random,inspect
from common.models import Ward
from swmadmin.models import Vehicle
from swmadmin.models import Ewd
from reports.models import Current_tracklog_history
from django.db.models.aggregates import Max
from django.contrib.gis.geos import GEOSGeometry,Point,LineString
from django.contrib.auth.decorators import login_required,user_passes_test
from datetime import datetime
from datetime import timedelta
import codecs
import math

# Create your views here.
@login_required
@user_passes_test(lambda user: user.is_superuser or (user.appuser.is_contractor or user.appuser.is_officer))
def latest_vehicle_status(request):
    response_data=dict()
    response_data['status'] = 'success'
    response_data['data'] = list()

    iward = None
    if not request.user.is_superuser:
        if request.user.appuser.is_contractor:
            iward = request.user.appuser.bmc_contractor.ward
        else:
            iward = request.user.appuser.bmc_officer.ward

    for each_th_record_dict in Current_tracklog_history.objects.values('vehicle').annotate(max_id=Max('id')).order_by('max_id'):
        each_th_record = Current_tracklog_history.objects.get(id=each_th_record_dict['max_id'])
        each_vehicle_record_data = dict()
        each_vehicle_record_data['veh'] = str(each_th_record.vehicle)
        each_vehicle_record_data['veh_ward'] = str(each_th_record.vehicle.ward)
        if iward and iward!= each_th_record.vehicle.ward:
            continue
        each_vehicle_record_data['type'] = str(each_th_record.vehicle.vehicle_type)
        each_vehicle_record_data['lat'] = str(each_th_record.latitude)
        each_vehicle_record_data['lon'] = str(each_th_record.longitude)
        each_vehicle_record_data['location']=Point(float(each_th_record.longitude), float(each_th_record.latitude))
        try:
            each_vehicle_record_data['ward'] = Ewd.objects.filter(is_active=True).filter(ewd_fence__contains=each_vehicle_record_data['location']).get()
        except:
            each_vehicle_record_data['ward'] = None
        tm = each_th_record.datetime + timedelta(minutes=330)
        each_vehicle_record_data['time'] = str(tm.strftime("%Y-%m-%d %H:%M:%S"))
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






@login_required
@user_passes_test(lambda user: user.is_superuser or (user.appuser.is_contractor or user.appuser.is_officer))
def latest_vehicle_status_v2(request):
    response_data=dict()
    response_data['status'] = 'success'
    response_data['data'] = list()

    #ajit's code block 1 starts - initializing the dictionary from txt file.
    mydict = {}
    filename = "../../../../../tmp/fulldata.txt"
    a_file = codecs.open(filename, encoding="utf-8")
    for line in a_file:
        key, value = line.split(":::")
        mydict[key] = value
    #ajit code block 1 ends here

    iward = None
    if not request.user.is_superuser:
        if request.user.appuser.is_contractor:
            iward = request.user.appuser.bmc_contractor.ward
        else:
            iward = request.user.appuser.bmc_officer.ward

    for each_th_record_dict in Current_tracklog_history.objects.values('vehicle').annotate(max_id=Max('id')).order_by('max_id'):
        each_th_record = Current_tracklog_history.objects.get(id=each_th_record_dict['max_id'])
        each_vehicle_record_data = dict()
        each_vehicle_record_data['veh'] = str(each_th_record.vehicle)
        each_vehicle_record_data['veh_ward'] = str(each_th_record.vehicle.ward)
        if iward and iward!= each_th_record.vehicle.ward:
            continue
        each_vehicle_record_data['type'] = str(each_th_record.vehicle.vehicle_type)
        each_vehicle_record_data['lat'] = str(each_th_record.latitude)
        each_vehicle_record_data['lon'] = str(each_th_record.longitude)
        each_vehicle_record_data['location']=Point(float(each_th_record.longitude), float(each_th_record.latitude))

        #from here: ajit's code block 2 starts - computing and saving the addresses in the response data dictionary
        inputlat = each_th_record.latitude
        inputlong = each_th_record.longitude
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
        except:
            resultaddress = "Out of Mumbai."
        #each_vehicle_record_data['address'] = resultaddress
        each_vehicle_record_data['ward'] = resultaddress
        #ajit code block 2 ends here

        #try:
            #each_vehicle_record_data['ward'] = Ewd.objects.filter(is_active=True).filter(ewd_fence__contains=each_vehicle_record_data['location']).get()
        #except:
            #each_vehicle_record_data['ward'] = None
        tm = each_th_record.datetime + timedelta(minutes=330)
        each_vehicle_record_data['time'] = str(tm.strftime("%Y-%m-%d %H:%M:%S"))
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
