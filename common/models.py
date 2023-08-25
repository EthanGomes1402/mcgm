from django.db import models
from django.contrib.gis.db import models
from django.core.serializers import serialize
from django.contrib.auth.models import User

class Div(models.Model):
    name = models.CharField(max_length=20, unique=True)
    short_name = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=50,default='')
    div_fence = models.MultiPolygonField()
    is_active    = models.BooleanField(default=1)
    created_at = models.DateTimeField(auto_now=True,null=True,blank=True)
    created_by = models.ForeignKey(User, related_name='+',on_delete=models.PROTECT,verbose_name ='Created by',null=True )
    updated_at = models.DateTimeField(auto_now=True,null=True,blank=True)
    updated_by = models.ForeignKey(User,related_name='+',on_delete=models.PROTECT,verbose_name='Updated by', null=True)

    def __str__(self):
        return (self.name)

class Zone(models.Model):
    name = models.CharField(max_length=20, unique=True)
    short_name = models.CharField(max_length=10,unique=True)
    description = models.CharField(max_length=50,default='')
    div = models.ForeignKey(Div, related_name='zones',on_delete=models.PROTECT,verbose_name ='Zone',null=True)
    zone_fence = models.MultiPolygonField(null=True, blank=True) 
    is_active    = models.BooleanField(default=1)
    created_at = models.DateTimeField(auto_now=True,null=True,blank=True)
    created_by = models.ForeignKey(User, related_name='+',on_delete=models.PROTECT,verbose_name ='Created by',null=True )
    updated_at = models.DateTimeField(auto_now=True,null=True,blank=True)
    updated_by = models.ForeignKey(User,related_name='+',on_delete=models.PROTECT,verbose_name='Updated by', null=True)

    def __str__(self):
        return (self.name)

class Ward(models.Model):
    name = models.CharField(max_length=20, unique=True)
    code = models.CharField(max_length=20, unique=True,default='')
    description = models.CharField(max_length=50,default='')
    ward_fence = models.MultiPolygonField() 
    zone = models.ForeignKey(Zone, related_name='wards',on_delete=models.PROTECT,verbose_name ='Ward',null=True)
    is_active    = models.BooleanField(default=1)
    created_at = models.DateTimeField(auto_now=True,null=True,blank=True)
    created_by = models.ForeignKey(User, related_name='+',on_delete=models.PROTECT,verbose_name ='Created by',null=True )
    updated_at = models.DateTimeField(auto_now=True,null=True,blank=True)
    updated_by = models.ForeignKey(User,related_name='+',on_delete=models.PROTECT,verbose_name='Updated by', null=True)

    def __str__(self):
        return (self.code)
