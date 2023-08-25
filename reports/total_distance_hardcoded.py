import psycopg2      
import math
import geopy.distance


connection = psycopg2.connect(user="mcgm",
                                  password="mcgm",
                                  host="localhost",
                                  port="5432",
                                  database="mcgm")
cursor = connection.cursor()

iward = 'B'       
        
date = "2023-01-04"
fromtime = " 00:00:00+05:30"
totime = " 23:59:59+05:30"

fromdate = date+fromtime
todate = date+totime
       
    #print("Fromdate ", fromdate)
    #print("Todate ", todate)    
        #shift  = form_data['shift']
shift = "1"

postgreSQL_select_Query0 = "select id from common_ward where name = '"+iward+"'"
        #select0 = (iward)
cursor.execute(postgreSQL_select_Query0)
fetch0 = cursor.fetchone()
    #print("WARD ID IS :",fetch0[0])
ward_id = str(fetch0[0])
    #print("This is ward id",ward_id)
        #for row0 in fetch0:
        #    ward_id = row0[0]

    
postgreSQL_select_Query1 = "select t1.id,t2.route_code,t2.route_name from swm.vehicles t1, swm.route_allocation t2 where t1.ward_id = '"+ward_id+"' and t1.vehicle_type IN ('Refuse_Compactor','Refuse_Mini_Compactor','Small_Closed_Vehicle') AND t1.id = t2.vehicle_id AND t2.is_active = 't' AND t1.ward_id= t2.ward_id AND t2.shift = '"+shift+"';"
    #select1 = (ward_id)
cursor.execute(postgreSQL_select_Query1)
        
fetch1 = cursor.fetchall()
    #print("These are all vehicle IDs in ward",iward,": ",fetch1)
    #print("This is fetch 1 ", fetch1)
vehicle_id_array = []

for row in fetch1:
            #print("Id = ", row[0])
            vehicle_id = row[0]
            vehicle_id_array.append(vehicle_id)
            count_vehicle_ids = len(vehicle_id_array)

    #print("Array of vehicle id is ",vehicle_id_array)
    #print("No of vehicles in array is ",count_vehicle_ids)

    
#for all_vehicle_id in vehicle_id_array: 
#if 1==1:
for all_vehicle_id in vehicle_id_array: 
            vehicle_type_array = []
            plate_number_array = []
            location_array = []
            distance_array = []
            distance_arraymain = []
            distance_array2 = []
            latitude_array = []
            longitude_array = []
            count = 0
            #print("Count before loop", count)
            all_vehicle_id = str(all_vehicle_id)
            #print("Vehicle IDs are : ",vehicle_id_array)
            postgreSQL_select_Query2 = "select vehicle_type,plate_number from swm.vehicles where id = '"+all_vehicle_id+"'"
            #postgreSQL_select_Query2 = "select vehicle_type,plate_number from swm.vehicles where id = 1687"
            #select2 = int(all_vehicle_id)
            
            cursor.execute(postgreSQL_select_Query2)
        
            fetch2 = cursor.fetchall()
            #print("This is fetch2 for vehicle id",all_vehicle_id, ": " ,fetch2)
            for row2 in fetch2:
            
                vehicle_type = row2[0]
                vehicle_type.strip()
                #print("Vehicle Type is ",vehicle_type)
                plate_number = row2[1]
                plate_number.strip()
                #print("plate number is ",plate_number) 

                vehicle_type_array.append(vehicle_type)
            
                plate_number_array.append(plate_number)
        
            #print("Vehicle Ids Are ", all_vehicle_id)   
            postgreSQL_select_Query3 = "select latitude,longitude from swm.vehicle_tracklog_historys where datetime between '"+fromdate+"' and '"+todate+"' and shift = '"+shift+"' and vehicle_id = '"+all_vehicle_id+"' order by datetime asc;"
            #postgreSQL_select_Query3 = "select latitude,longitude from swm.vehicle_tracklog_historys where datetime between '"+fromdate+"' and '"+todate+"' and shift = '"+shift+"' and vehicle_id = '1687' order by datetime asc;"
            #select3 = (fromdate,todate,shift,all_vehicle_id)
            cursor.execute(postgreSQL_select_Query3)
        
            fetch3 = cursor.fetchall()
            countlatlong = len(fetch3)
            latitude_array = [18.928,18.91,18.91,18.917,18.928,18.984,18.928,18.918,18.919,18.921,18.921,18.927,18.927,18.927,18.928,18.928,18.928,18.928,18.928,18.928,18.928,18.929,18.929,18.928]
            longitude_array = [72.83,72.817,72.817,72.823,72.83,72.826,72.83,72.824,72.826,72.826,72.826,72.826,72.825,72.825,72.825,72.824,72.824,72.824,72.824,72.824,72.823,72.823,72.823,72.83]


                
                #print("Location is ", location)
                #print("-------------------------------------------------------------")
                
            
                #print("No of latitudes for vehicle id", all_vehicle_id, "are : ", count_latitudes)
                #print("No of longitudes for vehicle id", all_vehicle_id, "are : ", count_longitudes)
                #print("No of locations for vehicle id", all_vehicle_id, "are : ", count_locations)




            
            for i in range(len(latitude_array)-1):

                #print(i,"th location is ", int(location_array[i]))
                #print(i+1,"th location is ", int(location_array[i+1]))

            
                #print(i,"th latitude is ", latitude_array[i])
                #print(i+1,"th latitude is ", latitude_array[i+1])


                #print(i,"th longitude is ", longitude_array[i])
                #print(i+1,"th longitude is ", longitude_array[i+1])


                source_lat = latitude_array[i]
                destination_lat = latitude_array[i+1]

                #print("Source Latitude ",i,": ", source_lat)
                #print("Destination Latitude ",i+1,": ", destination_lat)



                source_long = longitude_array[i]
                destination_long = longitude_array[i+1]
                
                #print("Source Longitude ",i,": ", source_long)
                #print("Destination Longitude ",i+1,": ", destination_long)

                #source_location = location_array[i]
                #destination_location = location_array[i+1]

                source_coords = (source_lat,source_long)
                destination_coords = (destination_lat,destination_long)
                #postgreSQL_select_Query4 = "select (point(%s,%s) <@> point(%s,%s)) as distance;"
                #select4 = (source_lat,source_long,destination_lat,destination_long)
                #cursor.execute(postgreSQL_select_Query4,select4)
                

                #fetch4 = cursor.fetchall()
                #print("this is fetch4 ", fetch4)
                #for row4 in fetch4:
                distance_1 = geopy.distance.distance(source_coords, destination_coords).km
                distance_2 = geopy.distance.great_circle(source_coords, destination_coords).km
                #postgreSQL_select_Query4 = "select (point(%s,%s) <@> point(%s,%s)) as distance;"
                #select4 = (source_lat,source_long,destination_lat,destination_long)
                #cursor.execute(postgreSQL_select_Query4,select4)
                distance_main = (distance_1 + distance_2)/2
                
                #fetch4 = cursor.fetchall()

                #for row4 in fetch4:
                #    distance = row4[0]
                    #print(type(distance))
                    #print("this is distance ", distance)
               # print("dist1", distance_1)
               # print("dist2", distance_2)
               # print("distmain", distance_main)
                #if distance_1 < 0.21748:
                distance_array.append(distance_1)

                #if distance_2 < 0.21748:
                distance_array2.append(distance_2)

                #if distance_main < 0.21748:
                distance_arraymain.append(distance_main)
                #    distance = row4[0]
                    #print(type(distance))
                    #print("this is distance ", distance)

                
                        #print(type(distance_array))
            #print("this is distance array of 1687", distance_array)
            total_distance_in_miles = math.fsum(distance_array)

            total_distance_in_miles_2 = math.fsum(distance_array2)
            total_distance_in_miles_main = math.fsum(distance_arraymain)
            #print(total_distance_in_miles)
            total_distance_in_km = total_distance_in_miles * 1.60934
            total_distance_in_km = format(total_distance_in_km, '.1f')

            total_distance_in_km_2 = total_distance_in_miles_2 * 1.60934
            total_distance_in_km_2 = format(total_distance_in_km_2, '.1f')

            total_distance_in_km_main = total_distance_in_miles_main * 1.60934
            total_distance_in_km_main = format(total_distance_in_km_main, '.1f')

            #total_distance_in_km = round(total_distance_in_km,1)
            count = count + 1
            #print("Count after loop",count)
print("This is actual distance ",total_distance_in_km)

print("This is actual distance 2 ",total_distance_in_km_2)

print("This is actual distance main ",total_distance_in_km_main)
            #coords_1 = (18.948599,72.835434)
            #coords_2 = (19.153103,72.956070)

            #qwe = geopy.distance.geodesic(coords_1, coords_2).km
            #print(qwe)
            
            #postgreSQL_select_Query8 = "select (point(18.948599,72.835434) <@> point(19.153103,72.956070)) as distance;"
            #cursor.execute(postgreSQL_select_Query8)

            #fetch8 = cursor.fetchall()
                #print("this is fetch4 ", fetch4)
            #for row8 in fetch8:
            #        distance8 = row8[0]
            #        distance8 = distance8 * 1.60934
            #        print("D", distance8)
            
            #for single_distance in distance_array:
            #    total_distance =  total_distance + distance_array[single_distance]
            #total_distance = sum(distance_array) 
            #total_distance = total_distance * 1.61

            #print("total Distance ", total_distance)
            #distance_array = []

