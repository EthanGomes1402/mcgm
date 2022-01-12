from django.db import models
from django.contrib.auth.models import User
from common.models import Ward

# Create your models here.

class Appuser(User):
    is_contractor = models.BooleanField(default=False)
    is_officer    = models.BooleanField(default=False)
    is_admin      = models.BooleanField(default=False)


class Bmc_contractor(models.Model):
    user         = models.OneToOneField(Appuser,on_delete=models.CASCADE,primary_key=True)
    company_name = models.CharField(max_length=50)
    ward         = models.ForeignKey(Ward, related_name='bmc_contractors',on_delete=models.CASCADE,null=True)

    class Meta:
        db_table = "bmc_contractors"

    def __str__(self):
        return self.user.username

class Bmc_officer(models.Model):
    user         = models.OneToOneField(Appuser,on_delete=models.CASCADE,null=True)
    company_name = models.CharField(max_length=50)
    ward         = models.ForeignKey(Ward, related_name='bmc_officers',on_delete=models.CASCADE,null=True)

    class Meta:
        db_table = "bmc_officers"

    def __str__(self):
        return self.user.username
