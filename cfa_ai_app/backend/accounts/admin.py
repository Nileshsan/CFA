from django.contrib import admin
from .models import Client, User, TallyTransaction
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class TallyTransactionAdmin(admin.ModelAdmin):
    list_display = ('party_name', 'voucher_no', 'date', 'amount', 'register_type', 'client')
    list_filter = ('register_type', 'date', 'client')
    search_fields = ('party_name', 'voucher_no', 'narration')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('client')

class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password', 'client', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'client', 'role', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'username', 'client', 'role', 'is_staff', 'is_active')
    search_fields = ('email', 'username')
    ordering = ('email',)

admin.site.register(Client)
admin.site.register(User, UserAdmin)
admin.site.register(TallyTransaction, TallyTransactionAdmin)
