from django.contrib import admin
from .models import Orphan, Donor, Sponsorship, Payment, Notification, OrphanDocument
from .models import Notification

admin.site.register(Notification)
admin.site.register(Orphan)
admin.site.register(Donor)
admin.site.register(Sponsorship)
admin.site.register(Payment)
@admin.register(OrphanDocument)
class OrphanDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'orphan', 'document_type', 'is_public', 'uploaded_at')
    list_filter = ('is_public', 'document_type', 'orphan')
    search_fields = ('title', 'orphan__name')