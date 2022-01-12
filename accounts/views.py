from django.shortcuts import render,redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm,ContractorSignUpForm,OfficerSignUpForm 
from .forms import UpdateUserForm
from django.http import HttpResponse
from django.views.generic import CreateView,ListView,UpdateView
from django.contrib.auth.models import User
from django.views.generic import TemplateView
from .models import Appuser

class SignUpView(TemplateView):
    template_name = 'accounts/signup.html'

# Create your views here.
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})

@login_required
def dashboard(request):
    return render(request, 'base.html')

class UpdateUserProfile(UpdateView):
    model = User
    fields = ['username', 'email']
    template_name = 'accounts/user_profile.html'

    def get_object(self):
        return self.request.user


@login_required
def update_profile(request):
    if request.method == "POST":
        uform =  UpdateUserForm(data = request.POST)
        if uform.is_valid:
            user= uform.save()
        return redirect('dashboard')
    else:
        uform = UpdateUserForm()
    return  render(request, 'accounts/user_profile.html', {'form': uform})

class ContractorSignUpView(CreateView):
    model = Appuser
    form_class = ContractorSignUpForm
    template_name = 'accounts/contractor_signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'contractor'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('dashboard')


class OfficerSignUpView(CreateView):
    model = Appuser
    form_class = OfficerSignUpForm
    template_name = 'accounts/officer_signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'officer'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('dashboard')
