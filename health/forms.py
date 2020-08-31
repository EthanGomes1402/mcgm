from django import forms
from common.models import Ward
from .models import Vehicle
from django.contrib.auth.models import User
import floppyforms as forms1
from dal import autocomplete

VEHICLE_TYPE = (
        ("mc","Mini Compactor"),
        ("lc","Large Compactor"),
        ("swm","Sweeper Vehicle Machine"),
        ("scv","Small Compactor Vehicle"),
        ("sl","Sleeper Vehicle"),
    )
YEARS = [(year,year) for year in range(1950,2021,1)]
SHIFT = (
        ('1', "Morning"),
        ('2', "Afternoon"),
        ('3', "Night"),
    )
#GARAGES = [(each_garage['id'],each_garage['name']) for each_garage in Stop_station.objects.filter(is_active='t').filter(is_garage=True).values('id','name').order_by('name') ]

#GARAGES = [('','')]
class NewVehicleForm(forms.ModelForm):
    plate_number = forms.CharField(label = 'Plate Number :')
    engine_number = forms.CharField(label = 'Engine Number :')
    chassis_number = forms.CharField(label = 'Chassis Number :')
    maker = forms.CharField(label = 'Maker :')
    vehicle_type = forms.ChoiceField(choices=VEHICLE_TYPE)
    manufactured_year = forms.ChoiceField(choices=YEARS)

    class Meta:
        model= Vehicle 
        fields=['plate_number','engine_number','chassis_number','maker','vehicle_type','manufactured_year']

class VehicleEditForm(NewVehicleForm):
    pass
