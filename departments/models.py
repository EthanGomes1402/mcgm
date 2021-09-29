from django.db import models
from tenant_schemas.models import TenantMixin

# Create your models here.
class department(TenantMixin):
    name = models.CharField(max_length=100)
    auto_create_schema = True
    auto_drop_schema = True
