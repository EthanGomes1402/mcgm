from django.shortcuts import render
from django.contrib.auth.models import User
from django.http import HttpResponse,JsonResponse
from .models import Ward,Zone,Div
from django.shortcuts import render,redirect,get_object_or_404
from django.http import Http404
from .forms import NewWardForm,WardEditForm,NewZoneForm,ZoneEditForm,NewDivForm,DivEditForm
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import CreateView,UpdateView,ListView,View,DetailView,DeleteView
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import datetime
timestamp_from = datetime.now().date()
from openpyxl import load_workbook
import json
import re
import string
import random
from fastkml import kml
from django.contrib.gis.gdal.datasource import DataSource
from django.contrib.gis.geos import GEOSGeometry,Point,LineString
from django.contrib.gis.gdal import SpatialReference, CoordTransform
from django.contrib import messages
from django.contrib.gis import geos
from django.db import connection

gcoord = SpatialReference(3857)
mycoord = SpatialReference(4326)
trans = CoordTransform(gcoord, mycoord)

class WardCreateView(CreateView):
    model=Ward
    form_class=NewWardForm
    template_name = 'common/add_ward.html'
    success_url= '/wards/'

    def form_valid(self,form):
        Ward = form.save(commit=False)
        Ward.created_by = self.request.user
        Ward.created_at = timezone.now()
        Ward.save()
        return redirect('wards')

class WardUpdateView(UpdateView):
    model = Ward
    form_class=WardEditForm
    context_object_name= 'ward'
    template_name = 'common/edit_ward.html'
    success_url = '/wards/'

    def form_valid(self,form):
        Ward = form.save(commit=False)
        Ward.updated_at = timezone.now()
        Ward.updated_by = self.request.user
        Ward.save()
        return redirect('wards')

# Create your views here.
def upload_wards(request):
    if request.method == 'POST':
        mykmlfile = request.FILES["excel_file"]
        with open('/home/mcgm/Development/mcgm/mcgm/fulldata/wards.kml','wb+') as destination:
            for chunk in mykmlfile.chunks():
                destination.write(chunk)

        ds = DataSource('/home/mcgm/Development/mcgm/mcgm/fulldata/wards.kml')
        for layer in ds:
            for feat in layer:
                geom = feat.geom
                ward = Ward.objects.create(
                    name=feat.get('name'),
                    code=feat.get('name'),
                    ward_fence=geom.geos,
                    created_by = request.user,
                    created_at = timezone.now()
                )
        return redirect('wards')
    return render(request,'common/upload_wards.html',{})

class ZoneCreateView(CreateView):
    model=Zone
    form_class=NewZoneForm
    template_name = 'common/add_zone.html'
    success_url= '/zones'

    def form_valid(self,form):
        zone_data = form.cleaned_data
        all_wards_from_zone = zone_data.pop('wards')
        all_wards = list(all_wards_from_zone)
        all_ward_fence = list()

        for each_ward in all_wards:
            all_ward_fence.append(each_ward.ward_fence)

        all_ward_fence_union =  all_ward_fence[0]
        all_ward_fence = all_ward_fence[1:]

        for each_ward_fence in all_ward_fence:
            all_ward_fence_union = all_ward_fence_union.union(each_ward_fence)

        zone_fence = all_ward_fence_union
        if isinstance(zone_fence, geos.Polygon):
            zone_fence = geos.MultiPolygon(zone_fence)

        zone_data['zone_fence'] = zone_fence
        zone_data['created_by'] = self.request.user
        zone_data['created_at'] = timezone.now()
        zone = Zone.objects.create(**zone_data)

        for each_ward in all_wards:
            each_ward.zone = zone
            each_ward.save()

        return redirect('zones')

class ZoneUpdateView(UpdateView):
    model = Zone
    form_class=ZoneEditForm
    context_object_name= 'zone'
    template_name = 'common/edit_zone.html'
    success_url = '/zones/'

    def form_valid(self,form):
        zone = self.object
        zone.wards.clear()

        zone_data = form.cleaned_data
        all_wards_from_zone = zone_data.pop('wards')
        all_wards = list(all_wards_from_zone)
        all_ward_fence = list()

        for each_ward in all_wards:
            all_ward_fence.append(each_ward.ward_fence)

        all_ward_fence_union =  all_ward_fence[0]
        all_ward_fence = all_ward_fence[1:]

        for each_ward_fence in all_ward_fence:
            all_ward_fence_union = all_ward_fence_union.union(each_ward_fence)

        zone_fence = all_ward_fence_union

        if isinstance(zone_fence, geos.Polygon):
            zone_fence = geos.MultiPolygon(zone_fence)

        zone.zone_fence = zone_fence
        zone.updated_by = self.request.user
        zone.updated_at = timezone.now()
        zone.wards.set(all_wards)
        zone.save()

        div_of_zone = zone.div
        if div_of_zone:
            all_zone_fences = div_of_zone.zones.all().values_list('zone_fence',flat=True)
            all_zone_fence_union =  all_zone_fences[0]
            all_zone_fences = all_zone_fences[1:]

            for each_zone_fence in all_zone_fences:
                all_zone_fence_union = all_zone_fence_union.union(each_zone_fence)

            div_fence = all_zone_fence_union
            if isinstance(div_fence, geos.Polygon):
                div_fence = geos.MultiPolygon(div_fence)

            div_of_zone.div_fence = div_fence
            div_of_zone.save()
        return redirect('zones')

class DivCreateView(CreateView):
    model=Div
    form_class=NewDivForm
    template_name = 'common/add_div.html'
    success_url= '/divs'

    def form_valid(self,form):
        div_data = form.cleaned_data
        all_zones_from_div = div_data.pop('zones')
        all_zones = list(all_zones_from_div)
        all_zone_fence = list()

        for each_zone in all_zones:
            all_zone_fence.append(each_zone.zone_fence)

        all_zone_fence_union =  all_zone_fence[0]
        all_zone_fence = all_zone_fence[1:]

        for each_zone_fence in all_zone_fence:
            all_zone_fence_union = all_zone_fence_union.union(each_zone_fence)

        div_fence = all_zone_fence_union
        if isinstance(div_fence, geos.Polygon):
            div_fence = geos.MultiPolygon(div_fence)

        div_data['div_fence'] = div_fence
        div_data['created_by'] = self.request.user
        div_data['created_at'] = timezone.now()
        div = Div.objects.create(**div_data)

        for each_zone in all_zones:
            each_zone.div = div
            each_zone.save()

        return redirect('divs')

class DivUpdateView(UpdateView):
    model = Div
    form_class=DivEditForm
    context_object_name= 'div'
    template_name = 'common/edit_div.html'
    success_url = '/divs/'

    def form_valid(self,form):
        div = self.object
        div.zones.clear()

        div_data = form.cleaned_data
        all_zones_from_div = div_data.pop('zones')
        all_zones = list(all_zones_from_div)
        all_zone_fence = list()

        for each_zone in all_zones:
            all_zone_fence.append(each_zone.zone_fence)

        all_zone_fence_union =  all_zone_fence[0]
        all_zone_fence = all_zone_fence[1:]

        for each_zone_fence in all_zone_fence:
            all_zone_fence_union = all_zone_fence_union.union(each_zone_fence)

        div_fence = all_zone_fence_union

        if isinstance(div_fence, geos.Polygon):
            div_fence = geos.MultiPolygon(div_fence)

        div.div_fence = div_fence
        div.updated_by = self.request.user
        div.updated_at = timezone.now()
        div.zones.set(all_zones)
        div.save()
        return redirect('divs')

class WardListView(ListView):
    model = Ward
    context_object_name='wards'
    template_name = 'common/wards.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tenant'] = self.request.tenant.name
        return context

    def get_queryset(self):
        print(self.request.tenant.name)
        qs = super(WardListView,self).get_queryset().filter(is_active=True).order_by('name')
        return qs

class ZoneListView(ListView):
    model = Zone
    context_object_name='zones'
    template_name = 'common/zones.html'

    def get_queryset(self):
        qs = super(ZoneListView,self).get_queryset().filter(is_active=True).order_by('name')
        return qs

class DivListView(ListView):
    model = Div
    context_object_name='divs'
    template_name = 'common/divs.html'

    def get_queryset(self):
        qs = super(DivListView,self).get_queryset().filter(is_active=True).order_by('name')
        return qs

def delete_ward(request):
    ward = Ward.objects.get(pk=request.POST['id'])
    ward.is_active = 'f'
    ward.save()
    response_data={}
    response_data['status'] = 'success'
    return HttpResponse(json.dumps(response_data),content_type="application/json")

def delete_zone(request):
    zone = Zone.objects.get(pk=request.POST['id'])
    zone.is_active = 'f'
    zone.save()
    response_data={}
    response_data['status'] = 'success'
    return HttpResponse(json.dumps(response_data),content_type="application/json")

def delete_div(request):
    div = Div.objects.get(pk=request.POST['id'])
    div.is_active = 'f'
    div.save()
    response_data={}
    response_data['status'] = 'success'
    return HttpResponse(json.dumps(response_data),content_type="application/json")

def get_ward_area(request):
    ward = Ward.objects.get(pk=request.GET['id'])
    response_data={}
    response_data['ward_fence'] = ward.ward_fence.geojson
    response_data['status'] = 'success'
    return HttpResponse(json.dumps(response_data),content_type="application/json")

def get_zone_area(request):
    zone = Zone.objects.get(pk=request.GET['id'])
    all_ward_fence = zone.wards.filter(is_active='t').values_list('ward_fence',flat=True)

    response_data={}
    response_data['status'] = 'success'

    if all_ward_fence :
        all_ward_fence_union =  all_ward_fence[0]
        all_ward_fence = all_ward_fence[1:]

        for each_ward_fence in all_ward_fence:
            all_ward_fence_union = all_ward_fence_union.union(each_ward_fence)

        zone_fence = all_ward_fence_union

        if isinstance(zone_fence, geos.Polygon):
            zone_fence = geos.MultiPolygon(zone_fence)

        response_data['zone_fence'] = zone_fence.geojson
    else:
        response_data['status'] = 'failure'
        response_data['zone_fence'] = ''

    return HttpResponse(json.dumps(response_data),content_type="application/json")

def get_div_area(request):
    div = Div.objects.get(pk=request.GET['id'])
    all_zone_fence = div.zones.filter(is_active='t').values_list('zone_fence',flat=True)

    all_zone_fence_union =  all_zone_fence[0]
    all_zone_fence = all_zone_fence[1:]

    for each_zone_fence in all_zone_fence:
        all_zone_fence_union = all_zone_fence_union.union(each_zone_fence)

    div_fence = all_zone_fence_union

    if isinstance(div_fence, geos.Polygon):
        div_fence = geos.MultiPolygon(div_fence)

    response_data={}
    response_data['div_fence'] = div_fence.geojson
    response_data['status'] = 'success'
    return HttpResponse(json.dumps(response_data),content_type="application/json")
