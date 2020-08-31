from django.shortcuts import render,redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm
from .forms import UpdateUserForm
from django.http import HttpResponse
from django.views.generic import UpdateView
from django.contrib.auth.models import User


# Create your views here.
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
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

