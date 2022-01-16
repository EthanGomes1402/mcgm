from django.db import models
from django.contrib.gis.db import models
from django.core.serializers import serialize
from django.contrib.auth.models import User
from swmadmin.models import Vehicle,Route,Bin
from swmadmin.models import Stop_station
from psqlextra.types import PostgresPartitioningMethod
from psqlextra.models import PostgresPartitionedModel

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
