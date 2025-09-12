from django.contrib import admin
from .models import Product
from users.models import Profile

# Register your models here.
admin.site.register(Product)

# Register Profile with admin options
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'verified')  # show fields in list
    list_filter = ('role', 'verified')           # filter sidebar
    search_fields = ('user__username', 'user__email')  # quick search