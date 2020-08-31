from django.db import models
from django.contrib.auth.models import User

# Create your models here.
VEHICLE_TYPE = (
        ("mc","Mini Compactor"),
        ("lc","Large Compactor"),
        ("swm","Sweeper Vehicle Machine"),
        ("scv","Small Compactor Vehicle"),
        ("sl","Sleeper Vehicle"),
    )

class Contractor(models.Model):
    name = models.CharField(max_length=20)
    user = models.OneToOneField(User,related_name='contractor_of_water',on_delete=models.CASCADE,null=True)
    company_name = models.CharField(max_length=50)
    telephone = models.CharField(max_length=20)
    mobile = models.CharField(max_length=20)
    fax = models.CharField(max_length=20)
    email = models.EmailField(max_length=70)
    is_active    = models.BooleanField(default=1)
    created_at = models.DateTimeField(auto_now=True,null=True,blank=True)
    created_by = models.ForeignKey(User, related_name='+',on_delete=models.PROTECT,verbose_name ='Created by',null=True )
    updated_at = models.DateTimeField(auto_now=True,null=True,blank=True)
    updated_by = models.ForeignKey(User,related_name='+',on_delete=models.PROTECT,verbose_name='Updated by', null=True)

    def __str__(self):
        return self.user.username

class Vehicle(models.Model):
    plate_number = models.CharField(max_length=20, unique=True)
    vehicle_type = models.CharField(max_length=10, choices=VEHICLE_TYPE,default='scv')
    engine_number = models.CharField(max_length=20, unique=True)
    chassis_number = models.CharField(max_length=20, unique=True)
    contractor = models.ForeignKey(Contractor,on_delete=models.CASCADE,null=True)
    maker = models.CharField(max_length=20)
    manufactured_year = models.IntegerField()
    is_active    = models.BooleanField(default=1)
    created_at = models.DateTimeField(auto_now=True,null=True,blank=True)
    created_by = models.ForeignKey(User, related_name='+',on_delete=models.PROTECT,verbose_name ='Created by',null=True )
    updated_at = models.DateTimeField(auto_now=True,null=True,blank=True)
    updated_by = models.ForeignKey(User,related_name='+',on_delete=models.PROTECT,verbose_name='Updated by', null=True)

    class Meta:
        ordering = ['plate_number',]

    def __str__(self):
        return self.plate_number
