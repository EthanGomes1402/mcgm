from django import forms
from common.models import Ward,Zone,Div
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

class PointWidget(forms1.gis.PointWidget, forms1.gis.BaseOsmWidget):
    map_width = 1050
    map_height= 800
    template_name = 'common/custom_lonlat.html'
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
    map_height= 800
    template_name = 'common/custom_lonlat.html'
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
    map_height= 800
    template_name = 'common/custom_lonlat.html'
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
    map_height= 800
    template_name = 'common/custom_lonlat.html'
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

class NewWardForm(forms.ModelForm):
    name = forms.CharField(max_length=20)
    code = forms.CharField(max_length=20)
    description = forms.CharField(max_length=200)
    ward_fence = forms1.gis.MultiPolygonField(widget=MultiPolygonWidget(attrs={ 'map_width': 1050,'map_height': 800 }),required=False)
    class Meta:
        model= Ward 
        fields=['name','code','description','ward_fence']

class WardEditForm(NewWardForm):
    pass

class NewZoneForm(forms.ModelForm):
    name = forms.CharField(label = 'Name :')
    short_name = forms.CharField(label = 'Short Name :')
    description = forms.CharField(label = 'Description :')
    wards   = forms.ModelMultipleChoiceField(queryset=Ward.objects.filter(is_active=True).order_by('code')) 

    class Meta:
        model= Zone 
        fields=['name','short_name','description','wards']

class ZoneEditForm(NewZoneForm):
    pass

class NewDivForm(forms.ModelForm):
    name = forms.CharField(label = 'Name :')
    short_name = forms.CharField(label = 'Short Name :')
    description = forms.CharField(label = 'Description :')
    zones   = forms.ModelMultipleChoiceField(queryset=Zone.objects.filter(is_active=True).order_by('name')) 
    class Meta:
        model= Div 
        fields=['name','short_name','description','zones']

class DivEditForm(NewDivForm):
    pass
