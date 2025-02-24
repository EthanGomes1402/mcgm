from django.shortcuts import render
from django.http import HttpResponse,JsonResponse
import json,re,string,random,inspect
from common.models import Ward
from swmadmin.models import Vehicle,Installation
from swmadmin.models import Ewd
from reports.models import Current_tracklog_history
from reports.models import Vehicle_tracklog_history
from django.db.models.aggregates import Max
from django.contrib.gis.geos import GEOSGeometry,Point,LineString
from django.contrib.auth.decorators import login_required,user_passes_test
from datetime import datetime
from datetime import timedelta
import codecs
import math
import time
import ast
#import django
#import os
import shutil
import os.path




#+++++++++++++++++++++++++++++++-------GENERATE 2 PDF-------------++++++++++++++++++++++++++++++
import os
import psycopg2
from common.models import Ward,Zone,Div
from swmadmin.models import Vehicle,Contractor,Ward_Contractor_Mapping,Bin,Route,Stop_station,Vehicle_Garage_Mapping,Ewd
from reports.models import Alert,Tracklog_history,Route_Allocation,Helpdesk,Route_Compliance,Route_Compliance_Demo
from django.shortcuts import render,redirect,get_object_or_404
from django.http import Http404
from datetime import datetime
from openpyxl import load_workbook
import json,re,string,random,inspect
from django.http import QueryDict, HttpResponse  # Ensure these imports
import dateutil.parser  # Ensure this importfrom django.http import QueryDict
from itertools import chain
from django.contrib.auth.models import User
from django.templatetags.static import static
from django.conf import settings

# png to eps
from PIL import Image
from io import BytesIO


import base64
from django.http import JsonResponse

from django.http import HttpResponse, FileResponse



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
        tm = each_th_record.datetime + timedelta(minutes=0)
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
    wards = Ward.objects.filter(is_active=True).order_by('code')
    vehicles = Vehicle.objects.filter(is_active=True).order_by('plate_number')

    all_wards = list();
    all_vehicles = dict();
    iward = None
    if not request.user.is_superuser:
        if request.user.appuser.is_contractor:
            iward = request.user.appuser.bmc_contractor.ward
            vehicles = Vehicle.objects.filter(ward=iward).order_by('plate_number')
            wards = Ward.objects.filter(id=iward.id)
        else:
            iward = request.user.appuser.bmc_officer.ward
            vehicles = Vehicle.objects.filter(ward=iward).order_by('plate_number')
            wards = Ward.objects.filter(id=iward.id)

    for ward in wards:
        ward_info = dict()
        ward_info['id'] = ward.id
        ward_info['name'] = ward.name
        all_wards.append(ward_info)

    form_parameters['wards'] = all_wards

    for each_vehicle in vehicles:
        veh_type = str(each_vehicle.vehicle_type)
        all_vehicles[veh_type]=list()

    for each_vehicle in vehicles:
        vehicle_info = dict()
        vehicle_info['id'] = each_vehicle.id
        vehicle_info['plate_number'] = each_vehicle.plate_number
        vehicle_info['type'] = str(each_vehicle.vehicle_type)
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
    response_data['status']         = 'success'
    response_data['data']           = dict()
    response_data['data']['online'] = list()
    response_data['data']['offline']= list()
    installations                   = dict()
    scvcount                        = 0
    lccount                         = 0
    mccount                         = 0
    wwcount                         = 0
    dwcount                         = 0
    swcount                         = 0
    othercount                      = 0
    totalcount                      = 0

    """
    #ajit's code block 1 starts - initializing the dictionary from txt file.
    mydict = {}
    filename = "../../../../../tmp/fulldata.txt"
    a_file = codecs.open(filename, encoding="utf-8")
    for line in a_file:
        key, value = line.split(":::")
        mydict[key] = value
    #ajit code block 1 ends here
    """
   
    iward = None
    if not request.user.is_superuser:
        if request.user.appuser.is_contractor:
            iward = request.user.appuser.bmc_contractor.ward
        else:
            iward = request.user.appuser.bmc_officer.ward

    for each_th_record_dict in Current_tracklog_history.objects.values('vehicle').annotate(max_dt=Max('datetime')).order_by('max_dt'):
        each_th_record = Current_tracklog_history.objects.get(datetime=each_th_record_dict['max_dt'],vehicle_id=each_th_record_dict['vehicle'])
        each_vehicle_record_data = dict()
        each_vehicle_record_data['veh'] = str(each_th_record.vehicle)
        each_vehicle_record_data['veh_ward'] = str(each_th_record.vehicle.ward)
        each_vehicle_record_data['veh_contractor'] = str(each_th_record.vehicle.contractor)
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
            resultaddress.strip()
        except:
            resultaddress = "Out of Mumbai."
        #each_vehicle_record_data['address'] = resultaddress
        each_vehicle_record_data['ward'] = resultaddress.split(",")[0] if resultaddress.split(",")[0] else ' '

        #ajit code block 2 ends here

        #try:
            #each_vehicle_record_data['ward'] = Ewd.objects.filter(is_active=True).filter(ewd_fence__contains=each_vehicle_record_data['location']).get()
        #except:
            #each_vehicle_record_data['ward'] = None

        tm = each_th_record.datetime + timedelta(minutes=0)
        each_vehicle_record_data['time'] = str(tm.strftime("%Y-%m-%d %H:%M:%S"))
        #logic will check if current time is in assigned route schedule for a vehicle
        #Below code commented out by ajit because it is not being used in the front end.
        if(str(each_th_record.vehicle.vehicle_type) == "SCV"):
            scvcount+=1
        elif(str(each_th_record.vehicle.vehicle_type) == "LC"):
            lccount+=1
        elif(str(each_th_record.vehicle.vehicle_type) == "MC"):
            mccount+=1
        elif(str(each_th_record.vehicle.vehicle_type) == "WW"):
            wwcount+=1
        elif(str(each_th_record.vehicle.vehicle_type) == "dw"):
            dwcount+=1
        elif(str(each_th_record.vehicle.vehicle_type) == "sw"):
            swcount+=1
        else:
            othercount+=1

        totalcount+=1
        if tm.date() < datetime.today().date():
           response_data['data']['offline'].append(each_vehicle_record_data)
        else:
           response_data['data']['online'].append(each_vehicle_record_data)

    #all_vth_record = Vehicle_tracklog_history.objects.filter(vehicle_id__in=installations.keys()).values('vehicle').annotate(max_dt=Max('datetime')).order_by('max_dt') 
        #for each_th_record in all_vth_record:
        #    each_vehicle_record_data = dict()

    #print(all_vth_record)
    #vehicles  = list(map(lambda vehicle : Vehicle.objects.get(pk=vehicle) , form_data['selectVehicle'].split("_")))
    return render(request,'dashboard/latest_vehicle_status.html',{ 'all_online_entries' : response_data['data']['online'],'all_offline_entries' : response_data['data']['offline'] , 'scvcount' : scvcount, 'lccount' : lccount, 'mccount' : mccount, 'swcount' : swcount, 'dwcount' : dwcount, 'wwcount': wwcount, 'othercount' : othercount,'totalvehiclecount' : totalcount })







@login_required
@user_passes_test(lambda user: user.is_superuser or (user.appuser.is_contractor or user.appuser.is_officer))
def latest_vehicle_status_v3(request):
    
    
    
    response_data=dict()
    response_data['status']         = 'success'
    response_data['data']           = dict()
    response_data['data']['online'] = list()
    response_data['data']['offline']= list()
    """ installations                   = dict()
    scvcount                        = 0
    lccount                         = 0
    mccount                         = 0
    wwcount                         = 0
    dwcount                         = 0
    swcount                         = 0
    othercount                      = 0
    totalcount                      = 0 """

    
    
    

    """
    #ajit's code block 1 starts - initializing the dictionary from txt file.
    mydict = {}
    filename = "../../../../../tmp/fulldata.txt"
    a_file = codecs.open(filename, encoding="utf-8")
    for line in a_file:
        key, value = line.split(":::")
        mydict[key] = value
    #ajit code block 1 ends here
    """

    iward = None
    if not request.user.is_superuser:
        if request.user.appuser.is_contractor:
            iward = request.user.appuser.bmc_contractor.ward
        else:
            iward = request.user.appuser.bmc_officer.ward

    
    iwardfilenamestr = ""
    #FOR WARD OWNER REQUESTS:
    if iward:
        
        
        #ajit's code block 1 starts - initializing the dictionary from txt file.
        mydict = {}
        
        iwardfilenamestr = str(iward).replace("/","") 
        
        #filename = "../../../../../tmp/"+ str(iwardfilenamestr)+ "_fulldata.txt"
        filename = "/home/mcgm/Development/mcgm/mcgm/fulldata/fulldata.txt"
        a_file = codecs.open(filename, encoding="utf-8")
        for line in a_file:
          key, value = line.split(":::")
          mydict[key] = value
        #ajit code block 1 ends here
        
        
        
        timefilepath = "/home/mcgm/Development/mcgm/mcgm/dashboard/loaddatafast/ward_"+str(iwardfilenamestr)+"_updatetimestamp.txt"

        timenow = int(time.time())
        if(os.path.exists(timefilepath)):
            pass
        else:
            a = open(timefilepath, "w")
            a.write(str(timenow))
            a.close()
            create_response_data_for_warduser(iward)


        file_check_previousupdatetime = open(timefilepath, "r")
        timelastupdated = int(file_check_previousupdatetime.read())
        
        file_check_previousupdatetime.close()

        if(timenow - timelastupdated >=300):
            
            file_check_previousupdatetime = open(timefilepath, "w")
            file_check_previousupdatetime.write(str(timenow))
            file_check_previousupdatetime.close()
            create_response_data_for_warduser(iward)


        """ for each_th_record_dict in Current_tracklog_history.objects.values('vehicle').annotate(max_dt=Max('datetime')).order_by('max_dt'):
            each_th_record = Current_tracklog_history.objects.get(datetime=each_th_record_dict['max_dt'],vehicle_id=each_th_record_dict['vehicle'])
            each_vehicle_record_data = dict()
            each_vehicle_record_data['veh'] = str(each_th_record.vehicle)
            each_vehicle_record_data['veh_ward'] = str(each_th_record.vehicle.ward)
            each_vehicle_record_data['veh_contractor'] = str(each_th_record.vehicle.contractor)
            if iward!= each_th_record.vehicle.ward:
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
                resultaddress.strip()
            except:
                resultaddress = "Out of Mumbai."
            #each_vehicle_record_data['address'] = resultaddress
            each_vehicle_record_data['ward'] = resultaddress.split(",")[0] if resultaddress.split(",")[0] else ' '

            #ajit code block 2 ends here

            #try:
                #each_vehicle_record_data['ward'] = Ewd.objects.filter(is_active=True).filter(ewd_fence__contains=each_vehicle_record_data['location']).get()
            #except:
                #each_vehicle_record_data['ward'] = None

            tm = each_th_record.datetime + timedelta(minutes=0)
            each_vehicle_record_data['time'] = str(tm.strftime("%Y-%m-%d %H:%M:%S"))
            
            
            if tm.date() < datetime.today().date():
                response_data['data']['offline'].append(each_vehicle_record_data)
            else:
                response_data['data']['online'].append(each_vehicle_record_data)

        #all_vth_record = Vehicle_tracklog_history.objects.filter(vehicle_id__in=installations.keys()).values('vehicle').annotate(max_dt=Max('datetime')).order_by('max_dt') 
            #for each_th_record in all_vth_record:
            #    each_vehicle_record_data = dict()

        #print(all_vth_record)
        #vehicles  = list(map(lambda vehicle : Vehicle.objects.get(pk=vehicle) , form_data['selectVehicle'].split("_"))) """
        
        #Following while loop and try catch added to code to make sure that the file being read doesn't get picked up while another process is writing into it
        flag = 0
        while(flag != 1):
            try:
                file_data = open("/home/mcgm/Development/mcgm/mcgm/dashboard/loaddatafast/"+str(iwardfilenamestr)+"_warddata.txt", "r", encoding="utf-8")
                contents = file_data.read()
                resultdict = ast.literal_eval(contents)
                file_data.close()
                flag = 1
            except: 
                flag = 0


        return render(request,'dashboard/latest_vehicle_status.html',{ 'all_online_entries' : resultdict['data']['online'],'all_offline_entries' : resultdict['data']['offline']})



    #FOR SUPERUSER REQUESTS:
    else:
        
        #ajit's code block 1 starts - initializing the dictionary from txt file.
        mydict = {}
        filename = "/home/mcgm/Development/mcgm/mcgm/fulldata/fulldata.txt"
        a_file = codecs.open(filename, encoding="utf-8")
        for line in a_file:
          key, value = line.split(":::")
          mydict[key] = value
        #ajit code block 1 ends here
        
        
        file_check_previousupdatetime = open("/home/mcgm/Development/mcgm/mcgm/dashboard/loaddatafast/superuserupdatetimestamp.txt", "r")
        timelastupdated = int(file_check_previousupdatetime.read())
        timenow = int(time.time())
        file_check_previousupdatetime.close()
        """ if(timenow - timelastupdated >=180): """
            #spawn thread to update data
        """ t = threading.Thread(target=create_response_data_for_superuser,args=[request])
        t.setDaemon(True)
        t.start() """
        if(timenow - timelastupdated >=180):
            
            file_check_previousupdatetime = open("/home/mcgm/Development/mcgm/mcgm/dashboard/loaddatafast/superuserupdatetimestamp.txt", "w")
            file_check_previousupdatetime.write(str(timenow))
            file_check_previousupdatetime.close()
            create_response_data_for_superuser()
            #getdata =  sync_to_async(create_response_data_for_superuser)
            #loop.run_in_executor(None, create_response_data_for_superuser)
            """ loop = asyncio.new_event_loop()
            ss = loop.run_until_complete(create_response_data_for_superuser)
            loop.close() """
            
            try:
                """ loop = asyncio.get_event_loop()
                loop.run_in_executor(None, create_response_data_for_superuser) """
                pass
            except:
                pass
            """ t = threading.Thread(target=create_response_data_for_superuser)
            t.setDaemon(True)
            t.start() """


            
        
        
        
        """ for each_th_record_dict in Current_tracklog_history.objects.values('vehicle').annotate(max_dt=Max('datetime')).order_by('max_dt'):
            each_th_record = Current_tracklog_history.objects.get(datetime=each_th_record_dict['max_dt'],vehicle_id=each_th_record_dict['vehicle'])
            each_vehicle_record_data = dict()
            each_vehicle_record_data['veh'] = str(each_th_record.vehicle)
            each_vehicle_record_data['veh_ward'] = str(each_th_record.vehicle.ward)
            each_vehicle_record_data['veh_contractor'] = str(each_th_record.vehicle.contractor)
            each_vehicle_record_data['type'] = str(each_th_record.vehicle.vehicle_type)
            each_vehicle_record_data['lat'] = str(each_th_record.latitude)
            each_vehicle_record_data['lon'] = str(each_th_record.longitude)
            #each_vehicle_record_data['location']=Point(float(each_th_record.longitude), float(each_th_record.latitude))

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
                resultaddress.strip()
            except:
                resultaddress = "Out of Mumbai."
            #each_vehicle_record_data['address'] = resultaddress
            each_vehicle_record_data['ward'] = resultaddress.split(",")[0] if resultaddress.split(",")[0] else ' '

        #ajit code block 2 ends here

        #try:
            #each_vehicle_record_data['ward'] = Ewd.objects.filter(is_active=True).filter(ewd_fence__contains=each_vehicle_record_data['location']).get()
        #except:
            #each_vehicle_record_data['ward'] = None

            tm = each_th_record.datetime + timedelta(minutes=0)
            each_vehicle_record_data['time'] = str(tm.strftime("%Y-%m-%d %H:%M:%S"))
            #logic will check if current time is in assigned route schedule for a vehicle
            #Below code commented out by ajit because it is not being used in the front end.
            if(str(each_th_record.vehicle.vehicle_type) == "SCV"):
                scvcount+=1
            elif(str(each_th_record.vehicle.vehicle_type) == "LC"):
                lccount+=1
            elif(str(each_th_record.vehicle.vehicle_type) == "MC"):
                mccount+=1
            elif(str(each_th_record.vehicle.vehicle_type) == "WW"):
                wwcount+=1
            elif(str(each_th_record.vehicle.vehicle_type) == "dw"):
                dwcount+=1
            elif(str(each_th_record.vehicle.vehicle_type) == "sw"):
                swcount+=1
            else:
                othercount+=1

            totalcount+=1
            if tm.date() < datetime.today().date():
                response_data['data']['offline'].append(each_vehicle_record_data)
            else:
                response_data['data']['online'].append(each_vehicle_record_data) """

        #all_vth_record = Vehicle_tracklog_history.objects.filter(vehicle_id__in=installations.keys()).values('vehicle').annotate(max_dt=Max('datetime')).order_by('max_dt') 
        #for each_th_record in all_vth_record:
        #    each_vehicle_record_data = dict()
        #f.write("\nTime taken to retrieve all data for superuser from Database was %s seconds" % (time.time() - start_time))
        #f.write("\n------Log ends here------")
        #f.close()

    #print(all_vth_record)
    #vehicles  = list(map(lambda vehicle : Vehicle.objects.get(pk=vehicle) , form_data['selectVehicle'].split("_")))
        """ file_eachrecord.write(str(response_data))
        file_eachrecord.close()
        fileread = open("/home/mcgm/Development/mcgm/mcgm/dashboard/tempdb.txt", "r", encoding="utf-8")
        contents = fileread.read()
        resultdict = ast.literal_eval(contents)
        fileread.close() """

        #Following while loop and try catch added to code to make sure that the file being read doesn't get picked up while another process is writing into it
        flag = 0
        while(flag != 1):
            try:
                file_data = open("/home/mcgm/Development/mcgm/mcgm/dashboard/loaddatafast/superuserdata.txt", "r", encoding="utf-8")
                contents = file_data.read()
                resultdict = ast.literal_eval(contents)
                file_data.close()
                flag = 1
            except:
                flag = 0

        ###NEXT 27 LINES CONSISTS OF A LOGIC TO GENERATE A HTML COPY OF THE DASHBOARD, WHICH CAN LATER BE USED TO CONVERT TO PDF####
        """ htmltemplate = open("/home/mcgm/Development/mcgm/mcgm/static/html2pdf/final-html/index.html", "r", encoding="utf-8")
        htmltemplatecontents = htmltemplate.read()

        count = 0
        for each_online in reversed(resultdict['data']['online']):
            count+=1
            htmltemplatecontents = htmltemplatecontents.replace("tablebodyrows", "<tr><td>"+str(count)+"</td><td>"+str(each_online['veh'])+"</td><td>"+str(each_online['type'])+"</td><td>"+str(each_online['ward'])+"</td><td>"+str(each_online['time'])+"</td><td>"+str(each_online['veh_ward'])+"</td><td>"+str(each_online['veh_contractor'])+"</td></tr>"+"\ntablebodyrows")

        onlinevehicle_count = count
        htmltemplatecontents = htmltemplatecontents.replace("totalonlinevehicles", str(onlinevehicle_count))


        for each_offline in reversed(resultdict['data']['offline']):
            count+=1
            htmltemplatecontents = htmltemplatecontents.replace("tablebodyrows", "<tr><td>"+str(count)+"</td><td>"+str(each_offline['veh'])+"</td><td>"+str(each_offline['type'])+"</td><td>"+str(each_offline['ward'])+"</td><td>"+str(each_offline['time'])+"</td><td>"+str(each_offline['veh_ward'])+"</td><td>"+str(each_offline['veh_contractor'])+"</td></tr>"+"\ntablebodyrows")


        offlinevehicle_count = count - onlinevehicle_count
        htmltemplatecontents = htmltemplatecontents.replace("totalofflinevehicles", str(offlinevehicle_count))

        htmltemplatecontents = htmltemplatecontents.replace("totalnumberofvehicles", str(count))
        htmltemplatecontents = htmltemplatecontents.replace("tablebodyrows", "")

        
        htmltemplate2 = open("/home/mcgm/Development/mcgm/mcgm/static/html2pdf/final-html/index2.html", "w", encoding="utf-8")
        htmltemplate2.write(htmltemplatecontents)
        htmltemplate2.close() """
        


        return render(request,'dashboard/latest_vehicle_status.html',{ 'all_online_entries' : resultdict['data']['online'],'all_offline_entries' : resultdict['data']['offline'] })

            






    

def create_response_data_for_superuser():

    """ import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mcgm.settings')
    import django
    django.setup()
    from reports.models import Current_tracklog_history """
    
    #os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mcgm.mcgm.settings')
    """ os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mcgm.settings")"""
    #django.setup()
    response_data2=dict()
    response_data2['status']         = 'success'
    response_data2['data']           = dict()
    response_data2['data']['online'] = list()
    response_data2['data']['offline']= list()
    """ installations                   = dict()
    scvcount                        = 0
    lccount                         = 0
    mccount                         = 0
    wwcount                         = 0
    dwcount                         = 0
    swcount                         = 0
    othercount                      = 0
    totalcount                      = 0 """

    #now = datetime.now()
    # dd/mm/YY H:M:S
    #dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

    #start_time = time.time()
    #ajit's code block 1 starts - initializing the dictionary from txt file.
    
    mydict = {}
    filename = "/home/mcgm/Development/mcgm/mcgm/fulldata/fulldata.txt"
    a_file = codecs.open(filename, encoding="utf-8")
    for line in a_file:
        key, value = line.split(":::")
        mydict[key] = value
    #ajit code block 1 ends here

    #abc = Current_tracklog_history.objects.values('vehicle').annotate(max_dt=Max('datetime')).order_by('max_dt')
    file_superuserdata_writing = open("/home/mcgm/Development/mcgm/mcgm/dashboard/loaddatafast/superuserdata_writing.txt", "w", encoding="utf-8")
    
    

    for each_th_record_dict in Current_tracklog_history.objects.values('vehicle').annotate(max_dt=Max('datetime')).order_by('max_dt'):
        
        
        each_th_record_pre = Current_tracklog_history.objects.filter(datetime=each_th_record_dict['max_dt'],vehicle_id=each_th_record_dict['vehicle'])
        each_th_record = each_th_record_pre[0]
        each_vehicle_record_data = dict()
        each_vehicle_record_data['veh'] = str(each_th_record.vehicle)
        each_vehicle_record_data['veh_ward'] = str(each_th_record.vehicle.ward)
        each_vehicle_record_data['veh_contractor'] = str(each_th_record.vehicle.contractor)
        each_vehicle_record_data['type'] = str(each_th_record.vehicle.vehicle_type)
        each_vehicle_record_data['lat'] = str(each_th_record.latitude)
        each_vehicle_record_data['lon'] = str(each_th_record.longitude)
        #each_vehicle_record_data['location']=Point(float(each_th_record.longitude), float(each_th_record.latitude))

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
            resultaddress.strip()
        except:
            resultaddress = "Out of Mumbai."
        #each_vehicle_record_data['address'] = resultaddress
        each_vehicle_record_data['ward'] = resultaddress.split(",")[0] if resultaddress.split(",")[0] else ' '

    #ajit code block 2 ends here

    #try:
        #each_vehicle_record_data['ward'] = Ewd.objects.filter(is_active=True).filter(ewd_fence__contains=each_vehicle_record_data['location']).get()
    #except:
        #each_vehicle_record_data['ward'] = None

        tm = each_th_record.datetime + timedelta(minutes=0)
        each_vehicle_record_data['time'] = str(tm.strftime("%Y-%m-%d %H:%M:%S"))
        #logic will check if current time is in assigned route schedule for a vehicle
        #Below code commented out by ajit because it is not being used in the front end.
        """ if(str(each_th_record.vehicle.vehicle_type) == "SCV"):
            scvcount+=1
        elif(str(each_th_record.vehicle.vehicle_type) == "LC"):
            lccount+=1
        elif(str(each_th_record.vehicle.vehicle_type) == "MC"):
            mccount+=1
        elif(str(each_th_record.vehicle.vehicle_type) == "WW"):
            wwcount+=1
        elif(str(each_th_record.vehicle.vehicle_type) == "dw"):
            dwcount+=1
        elif(str(each_th_record.vehicle.vehicle_type) == "sw"):
            swcount+=1
        else:
            othercount+=1

        totalcount+=1 """
        if tm.date() < datetime.today().date():
            response_data2['data']['offline'].append(each_vehicle_record_data)
        else:
            response_data2['data']['online'].append(each_vehicle_record_data)

        #all_vth_record = Vehicle_tracklog_history.objects.filter(vehicle_id__in=installations.keys()).values('vehicle').annotate(max_dt=Max('datetime')).order_by('max_dt') 
        #for each_th_record in all_vth_record:
        #    each_vehicle_record_data = dict()
        #f.write("\nTime taken to retrieve all data for superuser from Database was %s seconds" % (time.time() - start_time))
        #f.write("\n------Log ends here------")
        #f.close()
    
    #print(all_vth_record)
    #vehicles  = list(map(lambda vehicle : Vehicle.objects.get(pk=vehicle) , form_data['selectVehicle'].split("_")))
    file_superuserdata_writing.write(str(response_data2))
    file_superuserdata_writing.close()

    src = "/home/mcgm/Development/mcgm/mcgm/dashboard/loaddatafast/superuserdata_writing.txt"
    dst = "/home/mcgm/Development/mcgm/mcgm/dashboard/loaddatafast/superuserdata.txt"
    shutil.copyfile(src, dst)
    
    """ fileread = open("/home/mcgm/Development/mcgm/mcgm/dashboard/stored_data/swm_superuser_response_data.txt", "r", encoding="utf-8")
    contents = fileread.read()
    resultdict = ast.literal_eval(contents)
    fileread.close() """
    








def create_response_data_for_warduser(iward):


    response_data=dict()
    response_data['status']         = 'success'
    response_data['data']           = dict()
    response_data['data']['online'] = list()
    response_data['data']['offline']= list()


    mydict = {}
    
    iwardfilenamestr = str(iward).replace("/","") 
        
    #filename = "../../../../../tmp/"+ str(iwardfilenamestr)+ "_fulldata.txt"
    
    filename = "/home/mcgm/Development/mcgm/mcgm/fulldata/fulldata.txt"
    a_file = codecs.open(filename, encoding="utf-8")
    for line in a_file:
        key, value = line.split(":::")
        mydict[key] = value
    #ajit code block 1 ends here

    #abc = Current_tracklog_history.objects.values('vehicle').annotate(max_dt=Max('datetime')).order_by('max_dt')
    



    iwardfilenamestr = str(iward).replace("/","")
    for each_th_record_dict in Current_tracklog_history.objects.values('vehicle').annotate(max_dt=Max('datetime')).order_by('max_dt'):
        each_th_record_pre = Current_tracklog_history.objects.filter(datetime=each_th_record_dict['max_dt'],vehicle_id=each_th_record_dict['vehicle'])
        each_th_record = each_th_record_pre[0]
        each_vehicle_record_data = dict()
        if iward!= each_th_record.vehicle.ward:
            continue
        each_vehicle_record_data['veh'] = str(each_th_record.vehicle)
        each_vehicle_record_data['veh_ward'] = str(each_th_record.vehicle.ward)
        each_vehicle_record_data['veh_contractor'] = str(each_th_record.vehicle.contractor)
        
        each_vehicle_record_data['type'] = str(each_th_record.vehicle.vehicle_type)
        each_vehicle_record_data['lat'] = str(each_th_record.latitude)
        each_vehicle_record_data['lon'] = str(each_th_record.longitude)
        #each_vehicle_record_data['location']=Point(float(each_th_record.longitude), float(each_th_record.latitude))

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
            resultaddress.strip()
        except:
            resultaddress = "Out of Mumbai."
        #each_vehicle_record_data['address'] = resultaddress
        each_vehicle_record_data['ward'] = resultaddress.split(",")[0] if resultaddress.split(",")[0] else ' '

            #ajit code block 2 ends here

            #try:
                #each_vehicle_record_data['ward'] = Ewd.objects.filter(is_active=True).filter(ewd_fence__contains=each_vehicle_record_data['location']).get()
            #except:
                #each_vehicle_record_data['ward'] = None

        tm = each_th_record.datetime + timedelta(minutes=0)
        each_vehicle_record_data['time'] = str(tm.strftime("%Y-%m-%d %H:%M:%S"))
        #logic will check if current time is in assigned route schedule for a vehicle
        #Below code commented out by ajit because it is not being used in the front end.
        

        if tm.date() < datetime.today().date():
            response_data['data']['offline'].append(each_vehicle_record_data)
        else:
            response_data['data']['online'].append(each_vehicle_record_data)

        #all_vth_record = Vehicle_tracklog_history.objects.filter(vehicle_id__in=installations.keys()).values('vehicle').annotate(max_dt=Max('datetime')).order_by('max_dt') 
            #for each_th_record in all_vth_record:
            #    each_vehicle_record_data = dict()

        #print(all_vth_record)
        #vehicles  = list(map(lambda vehicle : Vehicle.objects.get(pk=vehicle) , form_data['selectVehicle'].split("_")))
        writefilename = "/home/mcgm/Development/mcgm/mcgm/dashboard/loaddatafast/warddata_"+str(iwardfilenamestr)+"_writing.txt"
        file_warddata_writing = open(writefilename, "w", encoding="utf-8")
        file_warddata_writing.write(str(response_data))
        file_warddata_writing.close()

        src = "/home/mcgm/Development/mcgm/mcgm/dashboard/loaddatafast/warddata_"+str(iwardfilenamestr)+"_writing.txt"
        dst = "/home/mcgm/Development/mcgm/mcgm/dashboard/loaddatafast/"+str(iwardfilenamestr)+"_warddata.txt"
        shutil.copyfile(src, dst)












#+++++++++++++++++++++++++++++++-------GENERATE 2 PDF-------------++++++++++++++++++++++++++++++
def by_datetime(ele):
    return ele.datetime


def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string




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



def generateps_2pdf(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']
    data_array = []

    if request.method == 'POST':

        #banned_vehicle_list = ["MH47Y5832","MH47Y5831","MH47Y5842","MH47Y5843","MH47Y6348","MH47Y6345","MH47Y6423","MH47Y6352","MH47Y6424","MH47Y6349","MH47Y6351","MH47Y6420","MH47Y6356","MH47Y6353","MH47Y6359","MH47Y6367","MH47Y6368","MH47Y6347","MH47Y6350","MH47Y6344","MH47Y6355","MH47Y6357","MH47Y6419","MH47Y6365","MH47Y6418","MH47Y6421","MH47Y6435","MH47Y6434","MH47Y6436","MH47Y6437","MH47Y6362","MH47Y6369","MH47Y6360","MH47Y6346","MH47Y6361","MH47Y6366","MH47Y5849","MH47Y6410","MH47Y6409","MH47Y6416","MH47Y6339","MH47Y6341","MH47Y6340","MH47Y6343","MH47Y6334","MH47Y6335","MH47Y6408","MH47Y6342","MH47Y6445","MH47Y6405","MH47Y6413","MH47Y6415","MH47Y6441","MH47Y6414","MH47Y6404","MH47Y6407","MH47Y6411","MH47Y6406","MH47Y6412","MH47Y6338","MH47Y6439","MH47Y6440","MH47Y6443","MH47Y6329","MH47Y6330","MH47Y6332","MH47Y6328","MH47Y6331","MH47Y6337","MH47Y6442","MH47Y6438","MH47Y6333","MH47Y5850","MH47Y6495","MH47Y6484","MH47Y6482","MH47Y6483","MH47Y6481","MH47Y6485","MH47AS1364","MH47AS1366","MH47AS1365","MH47Y7471","MH47Y7481","MH47Y7484","MH47Y7482","MH47Y7479","MH47Y7478","MH47Y7472","MH47Y7476","MH47Y7473","MH47Y7464","MH47Y7483","MH47Y7469","MH47Y7462","MH47Y7467","MH47Y7461","MH47Y7486","MH47Y7457","MH47Y7459","MH47Y7460","MH47Y7485","MH47Y7466","MH47Y7488","MH47Y7468","MH47Y7458","MH47Y7456","MH47Y7463","MH47Y7743","MH47Y7746","MH47Y7748","MH47Y8025","MH47Y8016","MH47Y7750","MH47Y7751","MH47Y7747","MH47Y8024","MH47Y8013","MH47Y8011","MH47Y8014","MH47Y8009","MH47Y8017","MH47Y8012","MH47Y8015","MH47Y7465","MH47Y8003","MH47Y7993","MH47Y7995","MH47Y7998","MH47Y7994","MH47Y7996","MH47Y8006","MH47Y8004","MH47Y8099","MH47Y8098","MH47Y8101","MH47Y8097","MH47Y8088","MH47Y8092","MH47Y8094","MH47Y8087","MH47Y8089","MH47Y8086","MH47Y8085","MH47Y8093","MH47Y8095","MH47Y8096","MH47Y8005","MH47Y8018","MH47Y7489","MH47Y7744","MH47Y7480","MH47Y8007","MH47Y8465","MH47Y8746","MH47Y8747"]
        banned_vehicle_list = []
        noPDF = "https://swm.vtms.cleanupmumbai.com/static/pdfreports/no_vehicle_route_report.pdf"
        #response_data=dict()
        #response_data['status'] = 'success'
        #response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
        img_data = request.POST['map_image']
        log_file_path = "/home/mcgm/Development/mcgm/mcgm/static/eps/error/whole_data.txt"


        # changed by hari-------------------------------------------> MAP
        # if img_data:
        #     img_data = img_data.split(',')[1] if ',' in img_data else img_data
            
        #     try:
        #         img_data = base64.b64decode(img_data)

        #         with Image.open(BytesIO(img_data)) as img:
        #             if img.mode in ("RGBA", "P"):
        #                 img = img.convert("RGB")

        #             eps_io = BytesIO()
                    
        #             img.save(eps_io, format='EPS')
        #             eps_io.seek(0)
        if img_data:
            img_data = img_data.split(',')[1] if ',' in img_data else img_data

            try:
                img_data = base64.b64decode(img_data)
                with Image.open(BytesIO(img_data)) as img:
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")

                    # Resize to specific resolution if needed
                    target_resolution = (800, 800)  # Width, Height in pixels
                    img = img.resize(target_resolution, Image.ANTIALIAS)

                    eps_io = BytesIO()
                    img.save(eps_io, format='EPS')
                    eps_io.seek(0)

                    with open('/home/mcgm/Development/mcgm/mcgm/static/eps/image.eps', 'wb') as f:
                        f.write(eps_io.getvalue())

                    with open(log_file_path, "a") as log_file:
                        log_file.write("EPS file created successfully.\n")
            
            except Exception as e:
                with open(log_file_path, "a") as log_file:
                    log_file.write(f"An error occurred: {e}\n")
        else:
            with open(log_file_path, "a") as log_file:
                log_file.write("No image data found in the request.\n")

        # end----------------------------------------------------------------->




        from_time = dateutil.parser.parse(form_data['from_time'])
        #response_data['fromtime'] = str(from_time)
        to_time   = dateutil.parser.parse(form_data['to_time'])
        vehicle_type = form_data.get('selectVehType')
        #response_data['totime'] = str(to_time)
        plate_no  = form_data['vehicle']
        if plate_no in banned_vehicle_list:
            return HttpResponse(noPDF)
        timedelay = form_data['timedelay']
        vehicle   = Vehicle.objects.get(plate_number=plate_no)

        # changed by hari------------------------------------------------------->
        if vehicle:
            ward_id = vehicle.ward_id
            contractor_id = vehicle.contractor_id

            try:
                user = User.objects.get(id=contractor_id)
                contractor_name = user.username
            except User.DoesNotExist:
                contractor_name = "N/A"

            try:
                ward = Ward.objects.get(id=ward_id)
                ward_name = ward.name
            except Ward.DoesNotExist:
                ward_name = "N/A"
        else:
            print ("Not Found")
        #end----------------------------------------------------------------------->












        vc = chain(vehicle.vehicle_tracklog_historys.filter(datetime__range=(from_time,to_time)).order_by('datetime').distinct('datetime'), vehicle.current_tracklog_historys.filter(datetime__range=(from_time,to_time)).order_by('datetime').distinct('datetime'))
        sorted_vc = sorted(vc,key=by_datetime)
        
        all_data_array = []
       
        for all_data in sorted_vc:
            # latitude = all_data.latitude
            all_data_array.append(all_data)
            # Write each latitude value to the file
        count_all_records = len(all_data_array)

        if count_all_records == 0:
            # utkarsh
            # noPDF2 = "https://swm.vtms.cleanupmumbai.com/static/pdfreports/no_vehicle_route_report_2.pdf"
            # return HttpResponse(noPDF2)
            
            # Hari
            return HttpResponse(str(count_all_records))
        

        seen        = dict()
        speed_zero  = dict()

        iward = None
        if not request.user.is_superuser:
          if request.user.appuser.is_contractor:
            iward = request.user.appuser.bmc_contractor.ward
          else:
            iward = request.user.appuser.bmc_officer.ward

    
        iwardfilenamestr = ""
        #FOR WARD USERS
        if iward:
          #ajit's code block 1 starts - initializing the dictionary from txt file.
          mydict = {}
        
          iwardfilenamestr = str(iward).replace("/","") 
        
          filename = "/home/mcgm/Development/mcgm/mcgm/fulldata/"+ str(iwardfilenamestr)+ "_fulldata.txt"
          a_file = codecs.open(filename, encoding="utf-8")
          for line in a_file:
            key, value = line.split(":::")
            mydict[key] = value
          #ajit code block 1 ends here
          
        #FOR SUPERUSER  
        else:  
          #ajit's code block 1 starts - initializing the dictionary from txt file.
          mydict = {}
          filename = "/home/mcgm/Development/mcgm/mcgm/fulldata/fulldata.txt"
          a_file = codecs.open(filename, encoding="utf-8")
          for line in a_file:
            key, value = line.split(":::")
            mydict[key] = value
          #ajit code block 1 ends here


        psfilename = "/home/mcgm/Development/mcgm/mcgm/static/pdfreports/"+str(plate_no)+"_"+str(from_time)+"_to_"+str(to_time)+".ps"
        pdffilename = "/home/mcgm/Development/mcgm/mcgm/static/pdfreports/"+str(plate_no)+"_"+str(from_time)+"_to_"+str(to_time)+".pdf"
        pdffilelink = "//swm.hari.cleanupmumbai.in/static/pdfreports/"+str(plate_no)+"_"+str(from_time)+"_to_"+str(to_time)+".pdf"
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
        dt_string = now.strftime("%d-%m-%Y %H:%M %p")



        # date_time = [
        #     from_time,
        #     to_time,
        #     dt_string
        # ]
        # date_array = []
        # date_array.append(date_time)

        # Convert to the same format as dt_string with AM/PM
        formatted_from_time = from_time.strftime("%d-%m-%Y %I:%M %p")
        formatted_to_time = to_time.strftime("%d-%m-%Y %I:%M %p")

        # changed by Hari------------------>24/07/2024
        # file_path = "/home/mcgm/hari/test/time_values.txt"

        # # Writing to a file
        # with open(file_path, "w") as file:
        #     file.write(f"from_time: {formatted_from_time}\n")
        #     file.write(f"to_time: {formatted_to_time}\n")
        #     file.write(f"dt_string: {dt_string}\n")


        page1 = """%!PS
/MCGM_LOGO {
    save
    /showpage {} bind def
    10 690 translate
    0.4 0.4 scale
    (/home/mcgm/Development/mcgm/mcgm/static/pdfreports/mcgmlogo.eps) run
    restore
} def

%%PROCEDURE
/ReportNamefont
/Times-Roman findfont 30 scalefont def

/Textfont
/Times-Roman findfont 15 scalefont def




/PrintReportName {
    0 setgray
    160 729 moveto
    ReportNamefont setfont
    (Vehicle Travel Report) show
} def


%%MAIN
PrintReportName
MCGM_LOGO

/TEXT_FONT /Helvetica findfont 15 scalefont def
/HEADER_FONT /Helvetica-Bold findfont 11 scalefont def 
/DATA_FONT  /Helvetica findfont 9 scalefont def

%Table_created_code
newpath
60 660 moveto
HEADER_FONT setfont
(Report Generated Date:-) show
370 660 moveto
DATA_FONT setfont
("""+str(dt_string)+""") show

newpath
50 650 moveto
0 25 rlineto
500 0 rlineto
0 -25 rlineto
-500 0 rlineto
stroke
newpath
300 650 moveto
0 25 rlineto
stroke

newpath
60 635 moveto
HEADER_FONT setfont
(From:-) show
370 635 moveto
DATA_FONT setfont
("""+str(formatted_from_time)+""") show

newpath
50 625 moveto
0 25 rlineto
500 0 rlineto
0 -25 rlineto
-500 0 rlineto
stroke
newpath
300 625 moveto
0 25 rlineto
stroke

newpath
60 610 moveto
HEADER_FONT setfont
(To:-) show
370 610 moveto
DATA_FONT setfont
("""+str(formatted_to_time)+""") show

newpath
50 600 moveto
0 25 rlineto
500 0 rlineto
0 -25 rlineto
-500 0 rlineto
stroke
newpath
300 600 moveto
0 30 rlineto
stroke

newpath
60 585 moveto
HEADER_FONT setfont
(Vehicle Registration No:-) show
383 585 moveto
DATA_FONT setfont
("""+str(plate_no)+""") show

newpath
50 575 moveto
0 25 rlineto
500 0 rlineto
0 -25 rlineto
-500 0 rlineto
stroke
newpath
300 575 moveto
0 30 rlineto
stroke

newpath
60 560 moveto
HEADER_FONT setfont
(Vehicle Type:-) show
370 560 moveto
DATA_FONT setfont
("""+str(vehicle_type)+""") show

newpath
50 550 moveto
0 25 rlineto
500 0 rlineto
0 -25 rlineto
-500 0 rlineto
stroke
newpath
300 550 moveto
0 30 rlineto
stroke

newpath
60 535 moveto
HEADER_FONT setfont
(Ward:-) show
400 535 moveto
DATA_FONT setfont
("""+str(ward_name)+""") show

newpath
50 525 moveto
0 25 rlineto
500 0 rlineto
0 -25 rlineto
-500 0 rlineto
stroke
newpath
300 525 moveto
0 30 rlineto
stroke

/MAP_IMG {
    save
    /showpage {} bind def
    20 10 translate
    0.71 0.61 scale
    (/home/mcgm/Development/mcgm/mcgm/static/eps/image.eps) run
    restore
} def





MAP_IMG


showpage
"""

        # Append-adds at last
        #htmlfile = open(htmlfilename, "a")  # append mode
        psfile = open(psfilename, "a", encoding="utf-8")
        psfile.write(page1)



        data = []
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
            """ try:
                resultaddress = mydict[finallatlong]
                resultaddress = (resultaddress.split(","))[:2]
            except:
                resultaddress = "Out of Mumbai." """
            
            if finallatlong not in mydict:
                resultaddress = "Out of Mumbai"
            else:
                resultaddress =  mydict[finallatlong]
                resultaddress = (resultaddress.split(","))[:2]
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

                
            # print(f"Successfully wrote '{finalresultaddress}' to '{filename}'")
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
87 54 moveto    %TO CHANGE VERTICAL LINES
0 680 rlineto   %BOTTOM-UP LENGTH
stroke

newpath
157 54 moveto
0 680 rlineto
stroke

newpath
223 54 moveto
0 680 rlineto
stroke

newpath
278 54 moveto
0 680 rlineto
stroke

newpath
493 54 moveto
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
0 setgray 101 720 moveto   %CHANGE THIS TO MOVE HEADERS
HEADER_FONT setfont
(Vehicle) show

%COLUMN_DATA_2st_PAGE
0 setgray 178 720 moveto   %CHANGE THIS TO MOVE HEADERS
HEADER_FONT setfont
(Date) show

%COLUMN_DATA_2st_PAGE
0 setgray 236 720 moveto   %CHANGE THIS TO MOVE HEADERS
HEADER_FONT setfont
(Time) show

%COLUMN_DATA_2st_PAGE
0 setgray 361 720 moveto   %CHANGE THIS TO MOVE HEADERS
HEADER_FONT setfont
(Location) show

%COLUMN_DATA_2st_PAGE
0 setgray 500 720 moveto   %CHANGE THIS TO MOVE HEADERS
HEADER_FONT setfont
(Speed) show
%----------------------------
%-----------------------
%HORIZONTAL_DATA
%COLUMN_DATA_2st_PAGE
0 setgray 65 700 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 700 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 700 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 700 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 700 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 700 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 680 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 680 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 680 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 680 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 680 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 680 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 660 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 660 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 660 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 660 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 660 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 660 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 640 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 640 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 640 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 640 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 640 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 640 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 620 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 620 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 620 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 620 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 620 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 620 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 600 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 600 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 600 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 600 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 600 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 600 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 580 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 580 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 580 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 580 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 580 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 580 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 560 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 560 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 560 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 560 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 560 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 560 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 540 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 540 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 540 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 540 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 540 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 540 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 520 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 520 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 520 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 520 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 520 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 520 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 500 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 500 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 500 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 500 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 500 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 500 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 480 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 480 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 480 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 480 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 480 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 480 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 460 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 460 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 460 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 460 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 460 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 460 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 440 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 440 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 440 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 440 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 440 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 440 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 420 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 420 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 420 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 420 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 420 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 420 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 400 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 400 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 400 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 400 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 400 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 400 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 380 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 380 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 380 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 380 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 380 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 380 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 360 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 360 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 360 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 360 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 360 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 360 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 340 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 340 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 340 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 340 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 340 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 340 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 320 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 320 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 320 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 320 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 320 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 320 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 300 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 300 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 300 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 300 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 300 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 300 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 280 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 280 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 280 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 280 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 280 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 280 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 260 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 260 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 260 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 260 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 260 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 260 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 240 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 240 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 240 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 240 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 240 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 240 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 220 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 220 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 220 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 220 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 220 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 220 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 200 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 200 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 200 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 200 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 200 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 200 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 180 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 180 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 180 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 180 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 180 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 180 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 160 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 160 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 160 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 160 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 160 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 160 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 140 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 140 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 140 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 140 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 140 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 140 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 120 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 120 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 120 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 120 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 120 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 120 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 100 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 100 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 100 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 100 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 100 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 100 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 80 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 80 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 80 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 80 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 80 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 80 moveto   %CHANGE THIS TO MOVE HEADERS
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
0 setgray 65 60 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(loopcounter)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 93 60 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(plate_no)+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 167 60 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%d-%m-%Y"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 232 60 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+str(each_vehicle_record.datetime.strftime("%H:%M:%S"))+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 290 60 moveto   %CHANGE THIS TO MOVE HEADERS
DATA_FONT setfont
("""+finalresultaddress+""") show

%COLUMN_DATA_2st_PAGE
0 setgray 513 60 moveto   %CHANGE THIS TO MOVE HEADERS
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
        response = FileResponse(open(pdffilename, 'rb'), as_attachment=True, filename=pdffilename)
        os.remove(psfilename)
        #pdfaccesslink = "http://swm.vtms.cleanupmumbai.com/static/pdfreports/"+str(plate_no)+"_"+str(from_time)+"_to_"+str(to_time)+".pdf"
        return HttpResponse(pdffilelink)
        # return response


    # return render(request,'reports/vehicle_route_report.html',{ 'form_params' : form_params})
    return render(request,'dashboard/quick_view.html')









def generateps_2pdf_map(request):
    set_session_reporting_form_params(request)
    form_params = request.session['reports_form_params']
    data_array = []

    if request.method == 'POST':

        #banned_vehicle_list = ["MH47Y5832","MH47Y5831","MH47Y5842","MH47Y5843","MH47Y6348","MH47Y6345","MH47Y6423","MH47Y6352","MH47Y6424","MH47Y6349","MH47Y6351","MH47Y6420","MH47Y6356","MH47Y6353","MH47Y6359","MH47Y6367","MH47Y6368","MH47Y6347","MH47Y6350","MH47Y6344","MH47Y6355","MH47Y6357","MH47Y6419","MH47Y6365","MH47Y6418","MH47Y6421","MH47Y6435","MH47Y6434","MH47Y6436","MH47Y6437","MH47Y6362","MH47Y6369","MH47Y6360","MH47Y6346","MH47Y6361","MH47Y6366","MH47Y5849","MH47Y6410","MH47Y6409","MH47Y6416","MH47Y6339","MH47Y6341","MH47Y6340","MH47Y6343","MH47Y6334","MH47Y6335","MH47Y6408","MH47Y6342","MH47Y6445","MH47Y6405","MH47Y6413","MH47Y6415","MH47Y6441","MH47Y6414","MH47Y6404","MH47Y6407","MH47Y6411","MH47Y6406","MH47Y6412","MH47Y6338","MH47Y6439","MH47Y6440","MH47Y6443","MH47Y6329","MH47Y6330","MH47Y6332","MH47Y6328","MH47Y6331","MH47Y6337","MH47Y6442","MH47Y6438","MH47Y6333","MH47Y5850","MH47Y6495","MH47Y6484","MH47Y6482","MH47Y6483","MH47Y6481","MH47Y6485","MH47AS1364","MH47AS1366","MH47AS1365","MH47Y7471","MH47Y7481","MH47Y7484","MH47Y7482","MH47Y7479","MH47Y7478","MH47Y7472","MH47Y7476","MH47Y7473","MH47Y7464","MH47Y7483","MH47Y7469","MH47Y7462","MH47Y7467","MH47Y7461","MH47Y7486","MH47Y7457","MH47Y7459","MH47Y7460","MH47Y7485","MH47Y7466","MH47Y7488","MH47Y7468","MH47Y7458","MH47Y7456","MH47Y7463","MH47Y7743","MH47Y7746","MH47Y7748","MH47Y8025","MH47Y8016","MH47Y7750","MH47Y7751","MH47Y7747","MH47Y8024","MH47Y8013","MH47Y8011","MH47Y8014","MH47Y8009","MH47Y8017","MH47Y8012","MH47Y8015","MH47Y7465","MH47Y8003","MH47Y7993","MH47Y7995","MH47Y7998","MH47Y7994","MH47Y7996","MH47Y8006","MH47Y8004","MH47Y8099","MH47Y8098","MH47Y8101","MH47Y8097","MH47Y8088","MH47Y8092","MH47Y8094","MH47Y8087","MH47Y8089","MH47Y8086","MH47Y8085","MH47Y8093","MH47Y8095","MH47Y8096","MH47Y8005","MH47Y8018","MH47Y7489","MH47Y7744","MH47Y7480","MH47Y8007","MH47Y8465","MH47Y8746","MH47Y8747"]
        banned_vehicle_list = []
        noPDF = "http://swm.hari.cleanupmumbai.in/static/pdfreports/no_vehicle_route_report.pdf"
        #response_data=dict()
        #response_data['status'] = 'success'
        #response_data['data'] = list()
        form_data = QueryDict(request.POST['form_data'].encode('ASCII'))
        img_data = request.POST['map_image']
        log_file_path = "/home/mcgm/Development/mcgm/mcgm/static/eps/error/whole_data.txt"


        # changed by hari-------------------------------------------> MAP
        # if img_data:
        #     img_data = img_data.split(',')[1] if ',' in img_data else img_data
            
        #     try:
        #         img_data = base64.b64decode(img_data)

        #         with Image.open(BytesIO(img_data)) as img:
        #             if img.mode in ("RGBA", "P"):
        #                 img = img.convert("RGB")

        #             eps_io = BytesIO()
                    
        #             img.save(eps_io, format='EPS')
        #             eps_io.seek(0)
        if img_data:
            img_data = img_data.split(',')[1] if ',' in img_data else img_data

            try:
                img_data = base64.b64decode(img_data)
                with Image.open(BytesIO(img_data)) as img:
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")

                    # Resize to specific resolution if needed
                    target_resolution = (800, 800)  # Width, Height in pixels
                    img = img.resize(target_resolution, Image.ANTIALIAS)

                    eps_io = BytesIO()
                    img.save(eps_io, format='EPS')
                    eps_io.seek(0)

                    with open('/home/mcgm/Development/mcgm/mcgm/static/eps/image.eps', 'wb') as f:
                        f.write(eps_io.getvalue())

                    with open(log_file_path, "a") as log_file:
                        log_file.write("EPS file created successfully.\n")
            
            except Exception as e:
                with open(log_file_path, "a") as log_file:
                    log_file.write(f"An error occurred: {e}\n")
        else:
            with open(log_file_path, "a") as log_file:
                log_file.write("No image data found in the request.\n")

        # end----------------------------------------------------------------->




        from_time = dateutil.parser.parse(form_data['from_time'])
        #response_data['fromtime'] = str(from_time)
        to_time   = dateutil.parser.parse(form_data['to_time'])
        vehicle_type = form_data.get('selectVehType')
        #response_data['totime'] = str(to_time)
        plate_no  = form_data['vehicle']
        if plate_no in banned_vehicle_list:
            return HttpResponse(noPDF)
        timedelay = form_data['timedelay']
        vehicle   = Vehicle.objects.get(plate_number=plate_no)

        # changed by hari------------------------------------------------------->
        if vehicle:
            ward_id = vehicle.ward_id
            contractor_id = vehicle.contractor_id

            try:
                user = User.objects.get(id=contractor_id)
                contractor_name = user.username
            except User.DoesNotExist:
                contractor_name = "N/A"

            try:
                ward = Ward.objects.get(id=ward_id)
                ward_name = ward.name
            except Ward.DoesNotExist:
                ward_name = "N/A"
        else:
            print ("Not Found")
        #end----------------------------------------------------------------------->












        vc = chain(vehicle.vehicle_tracklog_historys.filter(datetime__range=(from_time,to_time)).order_by('datetime').distinct('datetime'), vehicle.current_tracklog_historys.filter(datetime__range=(from_time,to_time)).order_by('datetime').distinct('datetime'))
        sorted_vc = sorted(vc,key=by_datetime)
        
        all_data_array = []
       
        for all_data in sorted_vc:
            # latitude = all_data.latitude
            all_data_array.append(all_data)
            # Write each latitude value to the file
        count_all_records = len(all_data_array)

        if count_all_records == 0:
            # utkarsh
            # noPDF2 = "https://swm.vtms.cleanupmumbai.com/static/pdfreports/no_vehicle_route_report_2.pdf"
            # return HttpResponse(noPDF2)
            
            # Hari
            return HttpResponse(str(count_all_records))
        

        seen        = dict()
        speed_zero  = dict()

        iward = None
        if not request.user.is_superuser:
          if request.user.appuser.is_contractor:
            iward = request.user.appuser.bmc_contractor.ward
          else:
            iward = request.user.appuser.bmc_officer.ward

    
        iwardfilenamestr = ""
        #FOR WARD USERS
        if iward:
          #ajit's code block 1 starts - initializing the dictionary from txt file.
          mydict = {}
        
          iwardfilenamestr = str(iward).replace("/","") 
        
          filename = "/home/mcgm/Development/mcgm/mcgm/fulldata/"+ str(iwardfilenamestr)+ "_fulldata.txt"
          a_file = codecs.open(filename, encoding="utf-8")
          for line in a_file:
            key, value = line.split(":::")
            mydict[key] = value
          #ajit code block 1 ends here
          
        #FOR SUPERUSER  
        else:  
          #ajit's code block 1 starts - initializing the dictionary from txt file.
          mydict = {}
          filename = "/home/mcgm/Development/mcgm/mcgm/fulldata/fulldata.txt"
          a_file = codecs.open(filename, encoding="utf-8")
          for line in a_file:
            key, value = line.split(":::")
            mydict[key] = value
          #ajit code block 1 ends here


        psfilename = "/home/mcgm/Development/mcgm/mcgm/static/pdfreports/"+str(plate_no)+"_"+str(from_time)+"_to_"+str(to_time)+".ps"
        pdffilename = "/home/mcgm/Development/mcgm/mcgm/static/pdfreports/"+str(plate_no)+"_"+str(from_time)+"_to_"+str(to_time)+".pdf"
        pdffilelink = "//swm.hari.cleanupmumbai.in/static/pdfreports/"+str(plate_no)+"_"+str(from_time)+"_to_"+str(to_time)+".pdf"
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
        dt_string = now.strftime("%d-%m-%Y %H:%M %p")



        # date_time = [
        #     from_time,
        #     to_time,
        #     dt_string
        # ]
        # date_array = []
        # date_array.append(date_time)

        # Convert to the same format as dt_string with AM/PM
        formatted_from_time = from_time.strftime("%d-%m-%Y %I:%M %p")
        formatted_to_time = to_time.strftime("%d-%m-%Y %I:%M %p")

        # changed by Hari------------------>24/07/2024
        # file_path = "/home/mcgm/hari/test/time_values.txt"

        # # Writing to a file
        # with open(file_path, "w") as file:
        #     file.write(f"from_time: {formatted_from_time}\n")
        #     file.write(f"to_time: {formatted_to_time}\n")
        #     file.write(f"dt_string: {dt_string}\n")


        page1 = """%!PS
/MCGM_LOGO {
    save
    /showpage {} bind def
    10 690 translate
    0.4 0.4 scale
    (/home/mcgm/Development/mcgm/mcgm/static/pdfreports/mcgmlogo.eps) run
    restore
} def

%%PROCEDURE
/ReportNamefont
/Times-Roman findfont 30 scalefont def

/Textfont
/Times-Roman findfont 15 scalefont def




/PrintReportName {
    0 setgray
    160 729 moveto
    ReportNamefont setfont
    (Vehicle Travel Report) show
} def


%%MAIN
PrintReportName
MCGM_LOGO

/TEXT_FONT /Helvetica findfont 15 scalefont def
/HEADER_FONT /Helvetica-Bold findfont 11 scalefont def 
/DATA_FONT  /Helvetica findfont 9 scalefont def

%Table_created_code
newpath
60 660 moveto
HEADER_FONT setfont
(Report Generated Date:-) show
370 660 moveto
DATA_FONT setfont
("""+str(dt_string)+""") show

newpath
50 650 moveto
0 25 rlineto
500 0 rlineto
0 -25 rlineto
-500 0 rlineto
stroke
newpath
300 650 moveto
0 25 rlineto
stroke

newpath
60 635 moveto
HEADER_FONT setfont
(From:-) show
370 635 moveto
DATA_FONT setfont
("""+str(formatted_from_time)+""") show

newpath
50 625 moveto
0 25 rlineto
500 0 rlineto
0 -25 rlineto
-500 0 rlineto
stroke
newpath
300 625 moveto
0 25 rlineto
stroke

newpath
60 610 moveto
HEADER_FONT setfont
(To:-) show
370 610 moveto
DATA_FONT setfont
("""+str(formatted_to_time)+""") show

newpath
50 600 moveto
0 25 rlineto
500 0 rlineto
0 -25 rlineto
-500 0 rlineto
stroke
newpath
300 600 moveto
0 30 rlineto
stroke

newpath
60 585 moveto
HEADER_FONT setfont
(Vehicle Registration No:-) show
383 585 moveto
DATA_FONT setfont
("""+str(plate_no)+""") show

newpath
50 575 moveto
0 25 rlineto
500 0 rlineto
0 -25 rlineto
-500 0 rlineto
stroke
newpath
300 575 moveto
0 30 rlineto
stroke

newpath
60 560 moveto
HEADER_FONT setfont
(Vehicle Type:-) show
370 560 moveto
DATA_FONT setfont
("""+str(vehicle_type)+""") show

newpath
50 550 moveto
0 25 rlineto
500 0 rlineto
0 -25 rlineto
-500 0 rlineto
stroke
newpath
300 550 moveto
0 30 rlineto
stroke

newpath
60 535 moveto
HEADER_FONT setfont
(Ward:-) show
400 535 moveto
DATA_FONT setfont
("""+str(ward_name)+""") show

newpath
50 525 moveto
0 25 rlineto
500 0 rlineto
0 -25 rlineto
-500 0 rlineto
stroke
newpath
300 525 moveto
0 30 rlineto
stroke


/MAP_IMG {
    save
    /showpage {} bind def
    20 10 translate
    0.71 0.61 scale
    (/home/mcgm/Development/mcgm/mcgm/static/eps/image.eps) run
    restore
} def





MAP_IMG


showpage
"""

        # Append-adds at last
        #htmlfile = open(htmlfilename, "a")  # append mode
        psfile = open(psfilename, "a", encoding="utf-8")
        psfile.write(page1)



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
        response = FileResponse(open(pdffilename, 'rb'), as_attachment=True, filename=pdffilename)
        os.remove(psfilename)
        #pdfaccesslink = "http://swm.vtms.cleanupmumbai.com/static/pdfreports/"+str(plate_no)+"_"+str(from_time)+"_to_"+str(to_time)+".pdf"
        return HttpResponse(pdffilelink)
        # return response


    # return render(request,'reports/vehicle_route_report.html',{ 'form_params' : form_params})
    return render(request,'dashboard/quick_view.html')
