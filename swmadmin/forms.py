from django import forms
from common.models import Ward
from .models import Route,Bin,Stop_station,Vehicle,Route_schedule,Contractor,Ward_Contractor_Mapping,Vehicle_Garage_Mapping,Installation,Ewd
from django.contrib.auth.models import User
import floppyforms as forms1
from dal import autocomplete

VEHICLE_TYPE = (
    ('---Please select vehicle type---',    
       (
        ("DGV","Dog Van"),
        ("BKV","Break Down"),
        ("LC","Refuse Compactor"),
        ("JCB","Bakayantra (JCB)"),
        ("DMP","Dumper"),
        ("MC","Refuse Mini Compactor"),
        ("SUMO","Sumo"),
        ("BUS","Bus"),
        ("HERV","Hearse"),
        ("AMB ","Ambulance"),
        ("SCO","Scorpio"),
        ("BOL","Bolero"),
        ("CAR","Car"),
        ("WAT","Water Tanker"),
        ("MMO","Mobile Medical Opthalmic Van"),
        ("RDV","Raid Van"),
        ("BB","Blood Bank"),
        ("DW","Dry Waste Tempo"),
        ("TRUCK","Truck"),
        ("CIMP","Cattle Impound Van"),
        ("ENCR","Encrochment"),
        ("MPS","Mechanical Power Sweeper"),
        ("TEC","Mak Lifton (Tree Cutting)"),
        ("WRE","Wrecker"),
        ("HYVA","HYVA Prime Mover"),
        ("CET","Cesspool Tanker"),
        ("JEEP","Jeep"),
        ("WW","Ward & Watch"),
        ("MEV","Meatvan"),
        ("SCV","Small Closed Vehicle"),
        ("SL","Side Loading Compactor"),
        ("FT","Tanker Fire Fighter"),
        ("BCM","Beach Cleaning Machine"),
        ("SSL","Steer Skid Loader"),
        ("TT","Tractor Trailer"),
        ("IV","Insecticide Vehicle"),
       )
    ),
)
YEARS = [(year,year) for year in range(1950,2023,1)]
SHIFT = (
        ('1', "Morning"),
        ('2', "Afternoon"),
        ('3', "Night"),
    )
ROUTE_TYPE = (
        ('S', "Sweaper"),
        ('N', "Normal"),
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
    route_type = forms.ChoiceField(choices=ROUTE_TYPE)
    route_fence = forms1.gis.LineStringField(widget=LineStringWidget(attrs={ 'map_width': 1050,'map_height': 1050 }),required=False)

    class Meta:
        model= Route
        fields=['name','code','route_type','route_fence']

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
    is_mlc    = forms.BooleanField(required=False,label = 'IS_ML_CHOWKI')
    is_chkpst = forms.BooleanField(required=False,label = 'IS_CHECKPOST')
    is_tnsstn = forms.BooleanField(required=False,label = 'IS_TRANSFER_STATION')
    is_dmpgnd = forms.BooleanField(required=False,label = 'IS_DUMPING_GROUND')
    is_garage = forms.BooleanField(required=False,label = 'IS_GARAGE')
    ward = forms.ModelChoiceField(queryset = Ward.objects.filter(is_active='t').order_by('name'),required=False)
    stop_station_fence =forms1.gis.PolygonField(widget=PolygonWidget(attrs={ 'map_width': 1050,'map_height': 1050 }),required=False)
    class Meta:
        model= Stop_station
        fields=['name','is_mlc','is_chkpst','is_tnsstn','is_dmpgnd','is_garage','ward','stop_station_fence']
      
        
class StopStationEditForm(NewStopStationForm):
    pass

class NewRouteScheuleForm(forms.ModelForm):
    name     = forms.CharField(label = 'Name :')
    shift    = forms.ChoiceField(choices=SHIFT,label = 'Shift :')
    mlc      = forms.ModelChoiceField(queryset = Stop_station.objects.filter(is_mlc='t').order_by('name'),required=False,label = 'MLC :')
    chkpst   = forms.ModelChoiceField(queryset = Stop_station.objects.filter(is_chkpst='t').order_by('name'),required=False, label = 'CHECKPOST :')

    class Meta:
        model= Route_schedule
        fields=['name','route','shift','vehicle','mlc','chkpst' ]

class RouteScheduleEditForm(NewRouteScheuleForm):
    pass

class NewContractorForm(forms.ModelForm):
    name = forms.CharField(label = 'Name :')
    company_name = forms.CharField(label = 'Company :')
    telephone = forms.CharField(label = 'Telephone :')
    mobile = forms.CharField(label = 'Mobile :')
    fax = forms.CharField(label = 'Fax :',required=False)
    email = forms.CharField(label = 'Email :')
    user  = forms.ModelChoiceField(queryset=User.objects.order_by('username'))

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
    vehicle  = forms.ModelChoiceField(queryset = Vehicle.objects.filter(is_active='t').order_by('plate_number'))
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

class NewEwdForm(forms.ModelForm):
    name = forms.CharField(max_length=20)
    code = forms.CharField(max_length=20)
    description = forms.CharField(max_length=200)
    ewd_fence = forms1.gis.MultiPolygonField(widget=MultiPolygonWidget(attrs={ 'map_width': 1050,'map_height': 800 }),required=False)
    class Meta:
        model= Ewd
        fields=['name','code','description','ewd_fence']

class EwdEditForm(NewEwdForm):
    pass
