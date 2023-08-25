from django import forms
from common.models import Ward
from swmadmin.models import Route,Bin,Stop_station,Vehicle,Route_schedule,Contractor,Ward_Contractor_Mapping,Vehicle_Garage_Mapping,Installation,Ewd
from django.contrib.auth.models import User
import floppyforms as forms1
from dal import autocomplete
from .models import Route_Allocation,Helpdesk
from django.db.models.fields import BLANK_CHOICE_DASH



SHIFT = [
     ('',
       (
           ('1','6am-2pm'),
        ('2','2pm-10pm'),
        ('3','10pm-6am')
           )
)
]

     

class RouteAllocationForm(forms.ModelForm):
    shift = forms.ChoiceField(choices=BLANK_CHOICE_DASH + SHIFT,label = 'Add Shift ', required=True)
    #choices=BLANK_CHOICE_DASH + SAMPLE_STRINGS, label='Please select a string', required=True
    
    route_code = forms.CharField(label = 'Route Code :')
    route_name = forms.CharField(label = 'Route Name :')
    vehicle = forms.ModelChoiceField(queryset = Vehicle.objects.filter(is_active='t').order_by('plate_number'))
    
    #ward = forms.ModelChoiceField(queryset = Ward.objects.filter(is_active='t').order_by('name'),required=False)

    class Meta:
        model= Route_Allocation
        fields=['shift','route_code','route_name','vehicle']          
        
        
  
class AllocationEditForm(RouteAllocationForm):
    pass         
        
        
        
class DistanceForm(forms.Form):
    date = forms.DateField()
    shift = forms.ChoiceField(choices=BLANK_CHOICE_DASH + SHIFT,label = 'Add Shift ', required=True)
   
        
    
    
class QueryForm(forms.ModelForm):
    
    email = forms.CharField(widget=forms.Textarea(attrs={'rows': 1}))
    phone_number = forms.CharField(label='Phone number', max_length=15)
    query = forms.CharField(
        widget=forms.Textarea(
          attrs={'rows': 5, 'placeholder': 'Please Enter your Query'}
        ),
        max_length=4000,
        help_text='Max length of the text is 4000.'
    )       
    
    
    class Meta:
        model= Helpdesk
        fields=['email','phone_number','query']     
        
        

class QueryResponseForm(forms.ModelForm):
    """
    email = forms.CharField(widget=forms.Textarea(attrs={'rows': 1}))
    phone_number = forms.CharField(label='Phone number', max_length=15)
    query = forms.CharField(
        widget=forms.Textarea(
          attrs={'rows': 5, 'placeholder': 'Please Enter your Query'}
        ),
        max_length=4000,
        help_text='Max length of the text is 4000.'
    )       
    """
    action = forms.CharField(
        widget=forms.Textarea(
          attrs={'rows': 5, 'placeholder': 'Enter Query'}
        ),
        max_length=4000,
        help_text='Max length of the text is 4000.'
    )
    
    class Meta:
        model= Helpdesk
        fields=['action']    
    
        
          
