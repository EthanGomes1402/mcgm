from django.conf.urls import url
from django.contrib import admin
from django.urls import path,include
from accounts import views as accounts_views
from django.contrib.auth import views as auth_views

#trial checking if both are in sync
urlpatterns = [
    path('accounts/signup/', accounts_views.SignUpView.as_view(), name='signup'),
    path('accounts/signup/contractor/',accounts_views.ContractorSignUpView.as_view(), name='contractor_signup'),
    path('accounts/signup/officer/', accounts_views.OfficerSignUpView.as_view(), name='officer_signup'),
    path('accounts/login/',auth_views.LoginView.as_view(template_name = 'accounts/login.html'),name='login'),
    path('logout/',auth_views.LogoutView.as_view(),name='logout'),
    path('update_profile/',accounts_views.UpdateUserProfile.as_view(success_url="/dashboard/"),name='update_profile' )
    #path('reset/',auth_views.PasswordResetView.as_view(template_name='password_reset.html',email_template_name='password_reset_email.html', subject_template_name='password_reset_subject.txt'),name='password_reset'),
    #path('reset/done/',auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'),name='password_reset_done'),
    #path('reset/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    #path('reset/complete/',auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'),name='password_reset_complete'),
    #path('settings/password/', auth_views.PasswordChangeView.as_view(template_name='password_change.html'),
    #name='password_change'),
    #path('settings/password/done/', auth_views.PasswordChangeDoneView.as_view(template_name='password_change_done.html'),
    #name='password_change_done'),
]
