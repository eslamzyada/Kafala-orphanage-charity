from django.contrib import admin
from .models import Orphan, Donor, Sponsorship, Payment, Document, Notification, OrphanDocument

admin.site.register(Orphan)
admin.site.register(Donor)
admin.site.register(Sponsorship)
admin.site.register(Payment)
admin.site.register(Document)
admin.site.register(Notification)

@admin.register(OrphanDocument)
class OrphanDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'orphan', 'document_type', 'is_public', 'uploaded_at')
    list_filter = ('is_public', 'document_type', 'orphan')
    search_fields = ('title', 'orphan__name')