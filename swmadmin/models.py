from django.db import models
from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.core.serializers import serialize
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from django.contrib.gis.gdal import SpatialReference, CoordTransform
from django.contrib.gis.geos import GEOSGeometry,Point
from common.models import Ward

#floppyform by default use srid 3857 so to make it use 4326
gcoord = SpatialReference(3857)
mycoord = SpatialReference(4326)
trans = CoordTransform(gcoord, mycoord)

VEHICLE_TYPE = (
        ("mc","Mini Compactor"),
        ("lc","Large Compactor"),
        ("scv","Small Compactor Vehicle"),
        ("sw","Sweeper Vehicle"),
        ("ww","Watch & Ward"),
    )

SHIFT = (
        ('1', "Morning"),
        ('2', "Afternoon"),
        ('3', "Night"),
    )

class Contractor(models.Model):
    name         = models.CharField(max_length=20)
    user         = models.OneToOneField(User,on_delete=models.CASCADE,null=True)
    company_name = models.CharField(max_length=50)
    telephone    = models.CharField(max_length=20)
    mobile       = models.CharField(max_length=20)
    fax          = models.CharField(max_length=20)
    email        = models.EmailField(max_length=70)
    is_active    = models.BooleanField(default=1)
    created_at   = models.DateTimeField(auto_now=True,null=True,blank=True)
    created_by   = models.ForeignKey(User, related_name='+',on_delete=models.PROTECT,verbose_name ='Created by',null=True )
    updated_at   = models.DateTimeField(auto_now=True,null=True,blank=True)
    updated_by   = models.ForeignKey(User,related_name='+',on_delete=models.PROTECT,verbose_name='Updated by', null=True)

    class Meta:
        db_table = "contractors"

    def __str__(self):
        return self.user.username

class Route(models.Model):
    name         = models.CharField(max_length=20, unique=True)
    code         = models.CharField(max_length=20, unique=True,null=True)
    ward         = models.ForeignKey(Ward, related_name='routes',on_delete=models.PROTECT,null=True)
    route_fence  = models.LineStringField(null=True, blank=True)
    is_active    = models.BooleanField(default=1)
    created_at   = models.DateTimeField(auto_now=True,null=True,blank=True)
    created_by   = models.ForeignKey(User, related_name='+',on_delete=models.PROTECT,verbose_name ='Created by',null=True )
    updated_at   = models.DateTimeField(auto_now=True,null=True,blank=True)
    updated_by   = models.ForeignKey(User,related_name='+',on_delete=models.PROTECT,verbose_name='Updated by', null=True)

    class Meta:
        db_table = "routes"

    def __str__(self):
        return self.name

    def bins_from_route(self):
        bins=serialize('geojson',  self.bins.all() ,geometry_field='bin_location')
        return bins 

    def route_serialized(self):
        routes = serialize('geojson', [ self ] ,geometry_field='route_fence') 
        return routes 

class Vehicle(models.Model):
    plate_number      = models.CharField(max_length=20, unique=True)
    vehicle_type      = models.CharField(max_length=10, choices=VEHICLE_TYPE,default='scv')
    engine_number     = models.CharField(max_length=20, unique=True)
    chassis_number    = models.CharField(max_length=20, unique=True)
    contractor        = models.ForeignKey(Contractor,on_delete=models.CASCADE,null=True)
    ward              = models.ForeignKey(Ward, related_name='vehicles',on_delete=models.PROTECT,null=True)
    maker             = models.CharField(max_length=20)
    manufactured_year = models.IntegerField()
    is_active         = models.BooleanField(default=1)
    created_at        = models.DateTimeField(auto_now=True,null=True,blank=True)
    created_by        = models.ForeignKey(User, related_name='+',on_delete=models.PROTECT,verbose_name ='Created by',null=True )
    updated_at        = models.DateTimeField(auto_now=True,null=True,blank=True)
    updated_by        = models.ForeignKey(User,related_name='+',on_delete=models.PROTECT,verbose_name='Updated by', null=True)

    class Meta:
        db_table = "vehicles"
        ordering = ['plate_number',]

    def __str__(self):
        return self.plate_number

class Halt(models.Model):
    name       = models.CharField(max_length=50)
    is_active  = models.BooleanField(default=1)
    created_at = models.DateTimeField(auto_now=True,null=True,blank=True)
    created_by = models.ForeignKey(User, related_name='+',on_delete=models.PROTECT,verbose_name ='Created by',null=True )
    updated_at = models.DateTimeField(auto_now=True,null=True,blank=True)
    updated_by = models.ForeignKey(User,related_name='+',on_delete=models.PROTECT,verbose_name='Updated by', null=True)

    class Meta:
        db_table = "halts"

class Stop_station(Halt):
    is_mlc    = models.BooleanField(default=0,verbose_name ='MLC')
    is_chkpst = models.BooleanField(default=0,verbose_name ='CHECKPOST')
    is_tnsstn = models.BooleanField(default=0,verbose_name ='TRANSFER STATION')
    is_dmpgnd = models.BooleanField(default=0,verbose_name ='DUMPING GROUND')
    is_garage = models.BooleanField(default=0,verbose_name ='GARAGE')
    ward      = models.ForeignKey(Ward, related_name='stop_stations',on_delete=models.CASCADE,null=True)
    stop_station_fence = models.PolygonField()

    class Meta:
        db_table = "stop_stations"

    def __str__(self):
        return self.name

class Bin(Halt):
    code        = models.CharField(max_length=25, unique=True,null=True, blank=True)
    tag         = models.CharField(max_length=50,null=True, blank=True)
    longitude   = models.DecimalField(max_digits=9, decimal_places=6,default=0,blank=True)
    latitude    = models.DecimalField(max_digits=9, decimal_places=6,default=0,blank=True)
    bin_location= models.PointField(null=True, blank=True)
    bin_fence   = models.PolygonField(null=True, blank=True)
    ward        = models.ForeignKey(Ward, related_name='bins',on_delete=models.CASCADE,null=True)
    route       = models.ForeignKey(Route, related_name='bins',on_delete=models.CASCADE,null=True)

    class Meta:
        db_table = "bins"
        ordering = ['code',]

class Route_schedule(models.Model):
    name        = models.CharField(max_length=20, unique=True)
    vehicle     = models.ForeignKey(Vehicle, related_name='route_schedules',on_delete=models.CASCADE) 
    route       = models.ForeignKey(Route, related_name='route_schedules',on_delete=models.CASCADE) 
    shift       = models.CharField(max_length=1, choices=SHIFT,default=1)
    is_active   = models.BooleanField(default=1)
    created_at  = models.DateTimeField(auto_now=True,null=True,blank=True)
    created_by  = models.ForeignKey(User, related_name='+',on_delete=models.PROTECT,verbose_name ='Created by',null=True )
    updated_at  = models.DateTimeField(auto_now=True,null=True,blank=True)
    updated_by  = models.ForeignKey(User,related_name='+',on_delete=models.PROTECT,verbose_name='Updated by', null=True)

    class Meta:
        db_table = "route_schedules"

class Ward_Contractor_Mapping(models.Model):
    ward        = models.ForeignKey(Ward,on_delete=models.CASCADE,null=True)
    contractor  = models.ForeignKey(Contractor,on_delete=models.CASCADE,null=True)
    is_active   = models.BooleanField(default=1)
    created_at  = models.DateTimeField(auto_now_add=True,verbose_name ='Created at')
    created_by  = models.ForeignKey(User, related_name='+',on_delete=models.PROTECT,verbose_name ='Created by')
    updated_at  = models.DateTimeField(auto_now=True,null=True,blank=True,verbose_name ='Updated at')
    updated_by  = models.ForeignKey(User,related_name='+',on_delete=models.PROTECT,verbose_name ='Updated by',null=True) 

    class Meta:
        db_table = "ward_contractor_mappings"
   
class Vehicle_Garage_Mapping(models.Model):
    vehicle     = models.OneToOneField(Vehicle,on_delete=models.CASCADE,null=True)
    garage      = models.ForeignKey(Stop_station,on_delete=models.CASCADE,null=True,limit_choices_to={'is_garage': True} )
    is_active   = models.BooleanField(default=1)
    created_at  = models.DateTimeField(auto_now_add=True,verbose_name ='Created at')
    created_by  = models.ForeignKey(User, related_name='+',on_delete=models.PROTECT,verbose_name ='Created by')
    updated_at  = models.DateTimeField(auto_now=True,null=True,blank=True,verbose_name ='Updated at')
    updated_by  = models.ForeignKey(User,related_name='+',on_delete=models.PROTECT,verbose_name ='Updated by',null=True) 

    class Meta:
        db_table = "vehicle_garage_mappings"

class Installation(models.Model):
    vehicle     = models.ForeignKey(Vehicle,on_delete=models.CASCADE,null=True)
    imei        = models.CharField(max_length=25, unique=True)
    sim         = models.CharField(max_length=20, unique=True)
    wnld_tag    = models.CharField(max_length=30, unique=True,null=True)
    is_active   = models.BooleanField(default=1)
    created_at  = models.DateTimeField(auto_now_add=True,verbose_name ='Created at')
    created_by  = models.ForeignKey(User, related_name='+',on_delete=models.PROTECT,verbose_name ='Created by')
    updated_at  = models.DateTimeField(auto_now=True,null=True,blank=True,verbose_name ='Updated at')
    updated_by  = models.ForeignKey(User,related_name='+',on_delete=models.PROTECT,verbose_name ='Updated by',null=True)   

    class Meta:
        db_table = "installations"
