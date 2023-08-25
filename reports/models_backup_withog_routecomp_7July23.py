from django.db import models
from django.contrib.gis.db import models
from django.core.serializers import serialize
from django.contrib.auth.models import User
from swmadmin.models import Vehicle,Route,Bin
from swmadmin.models import Stop_station
from psqlextra.types import PostgresPartitioningMethod
from psqlextra.models import PostgresPartitionedModel
from common.models import Ward


class CustomManager(models.Manager):
    def get_queryset(self):
            return super().get_queryset().filter(is_active=True)

# Create your models here.
class Alert(models.Model):
    geo_fence = '1'
    power_disconnection = '2'
    route_deviation = '3'
    speed = '4'
    alert_category_choices = [
        (geo_fence,'Geo Fence'),
        (power_disconnection,'Power Disconnection'),
        (route_deviation,'Route Deviation'),
        (speed,'Speed Violation'),
    ]
    none = '0'
    central_workshop = '1'
    department_offices = '2'
    department_workshop = '3'
    dumping_ground = '4'
    garbage_collection_point = '5'
    maintainance_sites = '6'
    motor_loading_chowkies = '7'
    station_location = '8'
    swd_workshops = '9'
    swm_garages = '10'
    swm_offices = '11'
    transfer_stations = '12'
    ward_offices = '13'
    work_site = '14'
    alert_sub_category_choices = [
        (none , 'None'),
        (central_workshop , 'central workshop'),
        (department_offices , 'department offices'),
        (department_workshop , 'department workshop'),
        (dumping_ground , 'dumping ground'),
        (garbage_collection_point , 'garbage collection point'),
        (maintainance_sites , 'maintainance sites'),
        (motor_loading_chowkies , 'motor loading chowkies'),
        (station_location , 'station location'),
        (swd_workshops , 'swd workshops'),
        (swm_garages , 'swm garages'),
        (swm_offices , 'swm offices'),
        (transfer_stations , 'transfer stations'),
        (ward_offices , 'ward offices'),
        (work_site , 'work site'),
    ]
    category = models.CharField(max_length=1,choices=alert_category_choices,default=geo_fence)
    sub_category = models.CharField(max_length=2,choices=alert_sub_category_choices,default=none)
    message = models.TextField()
    location = models.PointField(null=True, blank=True)
    vehicle = models.ForeignKey(Vehicle, related_name='alerts',on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True,null=True)

    class Meta:
        db_table = "alerts"
        ordering = ['created_at',]

class Tracklog_history(models.Model):
    vehicle = models.ForeignKey(Vehicle, related_name='tracklog_historys',on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now=True,null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6,default=0,blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6,default=0,blank=True)
    speed = models.FloatField(default=0.0, blank=True)
    heading = models.IntegerField(null=True, blank=True)
    mps = models.BooleanField(default=0,null=True)
    miv = models.FloatField(default=0.0, blank=True)
    ibv = models.FloatField(default=0.0, blank=True)
    location = models.PointField(null=True, blank=True)
    ignition = models.BooleanField(default=1)
    emergency= models.CharField(max_length=4,null=True, blank=True)
    dio = models.CharField(max_length=150,null=True, blank=True)
    dod = models.DateField(auto_now=True,null=True)
    shift_choices = [
        ('1','Morning'),
        ('2','Afternoon'),
        ('3','Night')
    ]
    shift= models.CharField(max_length=1,choices=shift_choices,default='1')
    created_at = models.DateTimeField(auto_now=True,null=True,blank=True)

    def __str__(self):
        return (",".join([str(self.vehicle),str(self.datetime)]))

    class Meta:
        db_table = "tracklog_historys"
        ordering = ['vehicle','datetime']

class Unlogged_tracklog_history(models.Model):
    vehicle = models.ForeignKey(Vehicle, related_name='unlogged_tracklog_historys',on_delete=models.CASCADE,db_index=False)
    datetime = models.DateTimeField(auto_now=True,null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6,default=0,blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6,default=0,blank=True)
    speed = models.FloatField(default=0.0, blank=True)
    heading = models.IntegerField(null=True, blank=True)
    mps = models.BooleanField(default=0,null=True)
    miv = models.FloatField(default=0.0, blank=True)
    ibv = models.FloatField(default=0.0, blank=True)
    location = models.PointField(null=True, blank=True)
    ignition = models.BooleanField(default=1)
    emergency= models.CharField(max_length=4,null=True, blank=True)
    dio = models.CharField(max_length=150,null=True, blank=True)
    dod = models.DateField(auto_now=True,null=True)
    shift_choices = [
        ('1','Morning'),
        ('2','Afternoon'),
        ('3','Night')
    ]
    shift= models.CharField(max_length=1,choices=shift_choices,default='1')
    created_at = models.DateTimeField(auto_now=True,null=True,blank=True)

    def __str__(self):
        return (",".join([str(self.vehicle),str(self.datetime)]))

    class Meta:
        db_table = "unlogged_tracklog_historys"
        ordering = ['vehicle','datetime']

class Unlogged_tracklog_history_v2(models.Model):
    vehicle = models.ForeignKey(Vehicle, related_name='unlogged_tracklog_historys_v2s',on_delete=models.CASCADE,db_index=False)
    datetime = models.DateTimeField(auto_now=True,null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6,default=0,blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6,default=0,blank=True)
    speed = models.FloatField(default=0.0, blank=True)
    heading = models.IntegerField(null=True, blank=True)
    mps = models.BooleanField(default=0,null=True)
    miv = models.FloatField(default=0.0, blank=True)
    ibv = models.FloatField(default=0.0, blank=True)
    location = models.PointField(null=True, blank=True,spatial_index=False)
    ignition = models.BooleanField(default=1)
    emergency= models.CharField(max_length=4,null=True, blank=True)
    dio = models.CharField(max_length=150,null=True, blank=True)
    dod = models.DateField(auto_now=True,null=True)
    shift_choices = [
        ('1','Morning'),
        ('2','Afternoon'),
        ('3','Night')
    ]
    shift= models.CharField(max_length=1,choices=shift_choices,default='1')
    created_at = models.DateTimeField(auto_now=True,null=True,blank=True)

    def __str__(self):
        return (",".join([str(self.vehicle),str(self.datetime)]))

    class Meta:
        db_table = "unlogged_tracklog_historys_v2"
        ordering = ['vehicle','datetime']

class Current_tracklog_history(PostgresPartitionedModel):
    class PartitioningMeta:
        method = PostgresPartitioningMethod.LIST
        key = ["shift"]

    vehicle = models.ForeignKey(Vehicle, related_name='current_tracklog_historys',on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now=True,null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6,default=0,blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6,default=0,blank=True)
    speed = models.FloatField(default=0.0, blank=True)
    heading = models.IntegerField(null=True, blank=True)
    mps = models.BooleanField(default=0,null=True)
    miv = models.FloatField(default=0.0, blank=True)
    ibv = models.FloatField(default=0.0, blank=True)
    location = models.PointField(null=True, blank=True)
    ignition = models.BooleanField(default=1)
    emergency= models.CharField(max_length=4,null=True, blank=True)
    dio = models.CharField(max_length=150,null=True, blank=True)
    dod = models.DateField(auto_now=True,null=True)
    shift_choices = [
        ('1','Morning'),
        ('2','Afternoon'),
        ('3','Night')
    ]
    shift= models.CharField(max_length=1,choices=shift_choices,default='1')
    created_at = models.DateTimeField(auto_now=True,null=True,blank=True)

    def __str__(self):
        return (",".join([str(self.vehicle),str(self.datetime)]))

    class Meta:
        db_table = "current_tracklog_historys"
        ordering = ['vehicle','datetime']


class Live_tracklog_history(PostgresPartitionedModel):
    class PartitioningMeta:
        method = PostgresPartitioningMethod.LIST
        key = ["shift"]

    vehicle = models.ForeignKey(Vehicle, related_name='live_tracklog_historys',on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now=True,null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6,default=0,blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6,default=0,blank=True)
    speed = models.FloatField(default=0.0, blank=True)
    heading = models.IntegerField(null=True, blank=True)
    mps = models.BooleanField(default=0,null=True)
    miv = models.FloatField(default=0.0, blank=True)
    ibv = models.FloatField(default=0.0, blank=True)
    location = models.PointField(null=True, blank=True)
    ignition = models.BooleanField(default=1)
    emergency= models.CharField(max_length=4,null=True, blank=True)
    dio = models.CharField(max_length=150,null=True, blank=True)
    dod = models.DateField(auto_now=True,null=True)
    shift_choices = [
        ('1','Morning'),
        ('2','Afternoon'),
        ('3','Night')
    ]
    shift= models.CharField(max_length=1,choices=shift_choices,default='1')
    created_at = models.DateTimeField(auto_now=True,null=True,blank=True)

    def __str__(self):
        return (",".join([str(self.vehicle),str(self.datetime)]))

    class Meta:
        db_table = "live_tracklog_historys"
        ordering = ['vehicle','datetime']

class Vehicle_tracklog_history(PostgresPartitionedModel):
    class PartitioningMeta:
        method = PostgresPartitioningMethod.RANGE
        key = ["datetime"]

    vehicle = models.ForeignKey(Vehicle, related_name='vehicle_tracklog_historys',on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now=True,null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6,default=0,blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6,default=0,blank=True)
    speed = models.FloatField(default=0.0, blank=True)
    heading = models.IntegerField(null=True, blank=True)
    mps = models.BooleanField(default=0,null=True)
    miv = models.FloatField(default=0.0, blank=True)
    ibv = models.FloatField(default=0.0, blank=True)
    location = models.PointField(null=True, blank=True)
    ignition = models.BooleanField(default=1)
    emergency= models.CharField(max_length=4,null=True, blank=True)
    dio = models.CharField(max_length=150,null=True, blank=True)
    dod = models.DateField(auto_now=True,null=True)
    shift_choices = [
        ('1','Morning'),
        ('2','Afternoon'),
        ('3','Night')
    ]
    shift= models.CharField(max_length=1,choices=shift_choices,default='1')
    created_at = models.DateTimeField(auto_now=True,null=True,blank=True)

    def __str__(self):
        return (",".join([str(self.vehicle),str(self.datetime)]))

    class Meta:
        db_table = "vehicle_tracklog_historys"
        ordering = ['vehicle','datetime']

class Weight_history(models.Model):
    vehicle = models.ForeignKey(Vehicle, related_name='weight_historys',on_delete=models.CASCADE)
    stop_station  = models.ForeignKey(Stop_station,related_name='weight_historys',on_delete=models.CASCADE,limit_choices_to={'is_dmpgnd': True},null=True)
    weight = models.FloatField(default=0.0, blank=True)
    datetime = models.DateTimeField(auto_now=True,null=True,blank=True)
    shift_choices = [
        ('1','Morning'),
        ('2','Afternoon'),
        ('3','Night')
    ]
    shift= models.CharField(max_length=1,choices=shift_choices,default='1')

    def __str__(self):
        return (",".join([str(self.vehicle),str(self.datetime),str(self.weight),str(self.stop_station)]))

    class Meta:
        db_table = "weight_historys"
        ordering = ['datetime']

class Tag_read_history(models.Model):
    vehicle = models.ForeignKey(Vehicle, related_name='tag_read_historys',on_delete=models.CASCADE)
    longitude = models.DecimalField(max_digits=9, decimal_places=6,default=0,blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6,default=0,blank=True)
    tag     = models.CharField(max_length=30,null=True)
    read_at = models.DateTimeField(auto_now=True,null=True,blank=True)
    is_registered     = models.BooleanField(default=0)
    tag_type_choices = [
        ('B','Bin'),
        ('W','Windschield'),
    ]
    tag_type= models.CharField(max_length=1,choices=tag_type_choices,default='B')

    def __str__(self):
        return (",".join([str(self.vehicle),str(self.read_at),str(self.tag),str(self.tag_type)]))

    class Meta:
        db_table = "tag_read_historys"


class Route_status(models.Model):
    route = models.ForeignKey(Route, related_name='route_statuses',on_delete=models.CASCADE)
    bins  = models.ForeignKey(Bin, related_name='route_statuses',on_delete=models.CASCADE)
    shift_choices = [
        ('1','Morning'),
        ('2','Afternoon'),
        ('3','Night')
    ]
    shift= models.CharField(max_length=1,choices=shift_choices,default='1')
    status= models.BooleanField(default=0)
    date  = models.DateField()

    class Meta:
        db_table = "route_statuses"

class Activity_log_history(models.Model):
    vehicle = models.ForeignKey(Vehicle, related_name='activity_log_historys',on_delete=models.CASCADE)
    time    = models.DateTimeField(auto_now=True,null=True,blank=True)
    speed   = models.FloatField(default=0.0, blank=True)
    halt_type_choices = [
        ('S','Stop_station'),
        ('B','Bin'),
    ]
    halt_type = models.CharField(max_length=1,choices=halt_type_choices,default='S')
    day_of_duty  = models.DateField()

    def __str__(self):
        return (",".join([str(self.vehicle),str(self.time),str(self.speed),str(self.tag_type)]))

    class Meta:
        db_table = "activity_log_historys"

class Faulty_records(models.Model):
    message = models.TextField()
    created_at = models.DateTimeField(auto_now=True,null=True)

    class Meta:
        db_table = "faulty_records"
        ordering = ['created_at',]
        
        
class Route_Allocation(models.Model):  
    
    shift_choices = [
        ('1','6am-2pm'),
        ('2','2pm-10pm'),
        ('3','10pm-6am')
    ]
    
    
     
    shift = models.CharField(max_length=1,choices=shift_choices,default='1')
    #route_code = models.ForeignKey(Route_Codes,on_delete=models.CASCADE,null=True) 
    #route_code = models.CharField(max_length=20,unique=True)
    route_code = models.CharField(max_length=20)
    route_name = models.CharField(max_length=150,null=True)
    vehicle = models.ForeignKey(Vehicle,on_delete=models.CASCADE,null=True)
    #ward_name = models.CharField(max_length=20,null=True)
    ward = models.ForeignKey(Ward, related_name='route_allocation_2',on_delete=models.PROTECT,null=True)
    #models.ForeignKey(Ward, related_name='vehicles',on_delete=models.PROTECT,null=True)
    #models.ForeignKey(Ward, related_name='route_allocation',on_delete=models.PROTECT,null=True)
    is_active  = models.BooleanField(default=1)
    created_at = models.DateTimeField(auto_now=True,null=True)
    created_by   = models.ForeignKey(User, related_name='+',on_delete=models.PROTECT,verbose_name ='Created by',null=True )
    bin_count = models.CharField(max_length=20,null=True)
    
    objects     = CustomManager()
    
    class Meta:
        db_table = "route_allocation"

    def __str__(self):
        return self.route_code    
           

class Helpdesk(models.Model):
    
    
    email = models.EmailField(max_length=100)
    phone_number = models.CharField(max_length=15,null=True)
    query = models.CharField(max_length=1000)
    action = models.CharField(max_length=1000,null=True)
    is_active  = models.BooleanField(default=1)
    created_at = models.DateTimeField(auto_now=True,null=True)
    created_by   = models.ForeignKey(User, related_name='+',on_delete=models.PROTECT,verbose_name ='Created by',null=True )  
    ward = models.ForeignKey(Ward, related_name='helpdesk',on_delete=models.PROTECT,null=True)
    updated_at = models.DateTimeField(auto_now=True,null=True)
    updated_by = models.ForeignKey(User, related_name='+',on_delete=models.PROTECT,verbose_name ='Updated by',null=True )  
    
    objects     = CustomManager()
    
    class Meta:
        db_table = "helpdesk"



class Route_Compliance(models.Model):
    
    bin_code = models.CharField(max_length=20,null=True)
    bin_location = models.CharField(max_length=100)
    #bin_geofence = models.CharField(max_length=1000)
    route_code = models.ForeignKey(Route_Allocation, related_name='bin_data',on_delete=models.PROTECT,null=True)
    bin_name = models.CharField(max_length=200,null=True)
    is_active  = models.BooleanField(default=1)
    created_at = models.DateTimeField(auto_now=True,null=True)
    created_by   = models.ForeignKey(User, related_name='+',on_delete=models.PROTECT,verbose_name ='Created by',null=True )
    ward = models.ForeignKey(Ward, related_name='route_compliance',on_delete=models.PROTECT,null=True)
    
    objects     = CustomManager()
    
    class Meta:
        db_table = "route_compliance"

    #def __str__(self):
    #    return self.assigned_route_code    