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

    
    iwardfilenamestr = ""
    #FOR WARD OWNER REQUESTS:
    if iward:

        iwardfilenamestr = str(iward).replace("/","")
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
    filename = "../../../../../tmp/fulldata.txt"
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
    filename = "../../../../../tmp/fulldata.txt"
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






