from django import forms
from common.models import Ward
from .models import Route,Bin,Stop_station,Vehicle,Route_schedule,Contractor,Ward_Contractor_Mapping,Vehicle_Garage_Mapping,Installation
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

class PointWidget(forms1.gis.PointWidget, forms1.gis.BaseOsmWidget):
    map_width = 1050
    map_height= 1050
    template_name = 'swmadmin/custom_lonlat.html'
    default_lon='72.9275398'
    default_lat='19.1123702'

    def get_context_data(self):
        ctx = super(PointWidget, self).get_context_data()
        ctx.update({
            'lon': self.default_lon,
            'lat': self.default_lat,
        })
        return ctx

class LineStringWidget(forms1.gis.LineStringWidget, forms1.gis.BaseOsmWidget):
    map_width = 1050
    map_height= 1050
    template_name = 'swmadmin/custom_lonlat.html'
    default_lon='72.9275398'
    default_lat='19.1123702'

    def get_context_data(self):
        ctx = super(LineStringWidget, self).get_context_data()
        ctx.update({
            'lon': self.default_lon,
            'lat': self.default_lat,
        })
        return ctx

class GeometryCollectionWidget(forms1.gis.GeometryCollectionWidget, forms1.gis.BaseOsmWidget):
    pass

class PolygonWidget(forms1.gis.PolygonWidget, forms1.gis.BaseOsmWidget):
    map_width = 1050
    map_height= 1050
    template_name = 'swmadmin/custom_lonlat.html'
    default_lon='72.9275398'
    default_lat='19.1123702'

    def get_context_data(self):
        ctx = super(PolygonWidget, self).get_context_data()
        ctx.update({
            'lon': self.default_lon,
            'lat': self.default_lat,
        })
        return ctx

class MultiPolygonWidget(forms1.gis.MultiPolygonWidget, forms1.gis.BaseOsmWidget):
    map_width = 1050
    map_height= 1050
    template_name = 'swmadmin/custom_lonlat.html'
    default_lon='72.9275398'
    default_lat='19.1123702'

    def get_context_data(self):
        ctx = super(MultiPolygonWidget, self).get_context_data()
        ctx.update({
            'lon': self.default_lon,
            'lat': self.default_lat,
        })
        return ctx

class GeometryWidget(forms1.gis.GeometryWidget, forms1.gis.BaseOsmWidget):
    pass

class MultiPointWidget(forms1.gis.MultiPointWidget, forms1.gis.BaseOsmWidget):
    pass

class MultiLineStringWidget(forms1.gis.MultiLineStringWidget,forms1.gis.BaseOsmWidget):
    pass

class NewBinForm(forms.ModelForm):
    name = forms.CharField(label = 'Name : ')
    bin_location = forms1.gis.PointField(widget=PointWidget,required=False)
    class Meta:
        model= Bin 
        fields=['name','tag','bin_location']

class BinEditForm(NewBinForm):
    pass

class NewRouteForm(forms.ModelForm):
    name = forms.CharField(label = 'Name :')
    code = forms.CharField(label = 'Code :')
    route_fence = forms1.gis.LineStringField(widget=LineStringWidget(attrs={ 'map_width': 1050,'map_height': 1050 }),required=False)

    class Meta:
        model= Route 
        fields=['name','code','route_fence']

class RouteEditForm(NewRouteForm):
    pass

class NewVehicleForm(forms.ModelForm):
    plate_number = forms.CharField(label = 'Plate Number :')
    engine_number = forms.CharField(label = 'Engine Number :')
    chassis_number = forms.CharField(label = 'Chassis Number :')
    maker = forms.CharField(label = 'Maker :')
    vehicle_type = forms.ChoiceField(choices=VEHICLE_TYPE)
    manufactured_year = forms.ChoiceField(choices=YEARS)
    ward = forms.ModelChoiceField(queryset = Ward.objects.filter(is_active='t').order_by('name'),required=False)

    class Meta:
        model= Vehicle 
        fields=['plate_number','engine_number','chassis_number','maker','vehicle_type','manufactured_year', 'contractor','ward']

class VehicleEditForm(NewVehicleForm):
    pass

class NewStopStationForm(forms.ModelForm):
    name = forms.CharField(label = 'Name :')
    is_mlc    = forms.BooleanField(required=False) 
    is_chkpst = forms.BooleanField(required=False)
    is_tnsstn = forms.BooleanField(required=False)
    is_dmpgnd = forms.BooleanField(required=False)
    is_garage = forms.BooleanField(required=False)
    ward = forms.ModelChoiceField(queryset = Ward.objects.filter(is_active='t').order_by('name'),required=False)
    stop_station_fence =forms1.gis.PolygonField(widget=PolygonWidget(attrs={ 'map_width': 1050,'map_height': 1050 }),required=False) 
    class Meta:
        model= Stop_station 
        fields=['name','is_mlc','is_chkpst','is_tnsstn','is_dmpgnd','is_garage','ward','stop_station_fence']

class StopStationEditForm(NewStopStationForm):
    pass

class NewRouteScheuleForm(forms.ModelForm):
    name = forms.CharField(label = 'Name :')
    shift = forms.ChoiceField(choices=SHIFT)

    class Meta:
        model= Route_schedule 
        fields=['name','shift','route','vehicle']

class RouteScheduleEditForm(NewRouteScheuleForm):
    pass

class NewContractorForm(forms.ModelForm):
    name = forms.CharField(label = 'Name :')
    company_name = forms.CharField(label = 'Company Name :')
    telephone = forms.CharField(label = 'Telephone :')
    mobile = forms.CharField(label = 'Mobile :')
    fax = forms.CharField(label = 'Fax :',required=False)
    email = forms.CharField(label = 'Email :')

    class Meta:
        model= Contractor 
        fields=['name','user','company_name','telephone','mobile','fax','email']

class ContractorEditForm(NewContractorForm):
    pass

class NewWCMForm(forms.ModelForm):
    ward = forms.ModelChoiceField(queryset = Ward.objects.filter(is_active='t'))
    contractor = forms.ModelChoiceField(queryset = Contractor.objects.filter(is_active='t'))

    class Meta:
        model= Ward_Contractor_Mapping 
        fields=['ward','contractor']

class WCMEditForm(NewWCMForm):
    pass

class NewVGMForm(forms.ModelForm):
    vehicle  = forms.ModelChoiceField(queryset = Vehicle.objects.filter(is_active='t').filter(contractor_id=31).order_by('plate_number'))
    garage   = forms.ModelChoiceField(queryset = Stop_station.objects.filter(is_active='t').filter(is_garage=True))

    class Meta:
        model= Vehicle_Garage_Mapping 
        fields=['vehicle','garage']

class VGMEditForm(NewVGMForm):
    pass

class NewInstallationForm(forms.ModelForm):
    vehicle = forms.ModelChoiceField(queryset = Vehicle.objects.filter(is_active='t').order_by('plate_number'))
    imei = forms.CharField(label = 'IMEI Number :')
    sim  = forms.CharField(label = 'Sim Number :')
    wnld_tag = forms.CharField(label = 'Windschield Tag :')

    class Meta:
        model= Installation 
        fields=['vehicle','imei','sim','wnld_tag']

class InstallationEditForm(NewInstallationForm):
    pass
