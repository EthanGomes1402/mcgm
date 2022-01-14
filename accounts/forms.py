from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from accounts.models import Appuser,Bmc_contractor,Bmc_officer
from common.models import Ward
from django.db import transaction

WARDS = [(w.id,w.name) for w in Ward.objects.all().order_by('name')]

class SignUpForm(UserCreationForm):
    email = forms.CharField(max_length=254,required=True,widget=forms.EmailInput())
    class meta:
        model=User
        fields = ('username', 'email', 'password1', 'password2')

class UpdateUserForm(forms.ModelForm):
    class meta:
        model = User
        fields =('username', 'email', 'password1', 'password2')

class ContractorSignUpForm(UserCreationForm):
    email = forms.CharField(max_length=254,required=True,widget=forms.EmailInput())
    company_name = forms.CharField(label = 'Company :')
    ward = forms.ChoiceField(choices=WARDS, widget=forms.RadioSelect)

    class Meta(UserCreationForm.Meta):
        model = Appuser

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.is_contractor = True
        user.save()
        bmc_contractor = Bmc_contractor.objects.create(user=user)
        bmc_contractor.ward=Ward.objects.get(id =self.cleaned_data.get('ward'))
        bmc_contractor.company_name=self.cleaned_data.get('company_name')
        bmc_contractor.save()
        return user

class OfficerSignUpForm(UserCreationForm):
    email = forms.CharField(max_length=254,required=True,widget=forms.EmailInput())
    ward = forms.ChoiceField(choices=WARDS, widget=forms.RadioSelect)

    class Meta(UserCreationForm.Meta):
        model = Appuser

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_officer = True
        user.save()
        bmc_officer = Bmc_officer.objects.create(user=user)
        bmc_officer.ward=Ward.objects.get(id =self.cleaned_data.get('ward'))
        bmc_officer.save()
        return user
