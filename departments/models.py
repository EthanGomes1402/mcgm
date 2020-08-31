from django.db import models
from tenant_schemas.models import TenantMixin

# Create your models here.
class department(TenantMixin):
    name = models.CharField(max_length=100)

    # default true, schema will be automatically created and synced when it is saved
    auto_create_schema = True
