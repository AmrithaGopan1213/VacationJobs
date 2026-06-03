from django.contrib import admin
from django.utils.html import format_html
from .models import Task, Wallet ,TaskUserAssignment,Register,UserReferral

admin.site.register(Task)
admin.site.register(Wallet)

@admin.register(Register)
class RegisterAdmin(admin.ModelAdmin):
    list_display = ['user', 'first_name', 'email', 'phone','is_verified','created_at'] 
    search_fields = ['user__username', 'first_name', 'email', 'phone','is_verified','created_at','updated_at']
    list_filter = ['user', 'first_name', 'email', 'phone','created_at','is_verified','updated_at']
    
@admin.register(UserReferral)
class UserReferralAdmin(admin.ModelAdmin):
    list_display = ['user','parent', 'referral_link']
    search_fields = ['user__username', 'parent','referral_link']
    list_filter = ['user','parent', 'referral_link']


@admin.register(TaskUserAssignment)
class TaskUserAssignmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'task', 'get_screenshot', 'submission_status', 'created_at')
    list_filter = ('submission_status', 'created_at')
    search_fields = ('user__username', 'task__title')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_screenshot(self, obj):
        if obj.screenshot:
            return format_html('<img src="{}" width="50" height="50" />', obj.screenshot.url)
        return "No screenshot"
    get_screenshot.short_description = 'Screenshot'
    
    fieldsets = (
        ('Assignment Info', {
            'fields': ('user', 'task', 'submission_status')
        }),
        ('Proof Details', {
            'fields': ('screenshot', 'proof_text', 'proof_video')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Make clicked_at and submission_status fields readonly
    # readonly_fields = ['clicked_at', 'submission_status']
