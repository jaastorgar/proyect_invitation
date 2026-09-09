from django.contrib import admin
from django.utils.html import format_html, mark_safe
from .models import Invitacion, RespuestaRSVP, ConfiguracionEvento

@admin.register(ConfiguracionEvento)
class ConfiguracionEventoAdmin(admin.ModelAdmin):
    list_display = ('titulo_evento', 'fecha', 'hora', 'lugar', 'organizador')
    
    def has_add_permission(self, request):
        # Evitar crear más de un registro desde el admin
        if ConfiguracionEvento.objects.exists():
            return False
        return super().has_add_permission(request)

@admin.register(Invitacion)
class InvitacionAdmin(admin.ModelAdmin):
    list_display = ('nombre_invitado', 'email', 'estado_respuesta', 'link_acceso', 'fecha_creacion', 'activa')
    list_filter = ('activa', 'fecha_creacion')
    search_fields = ('nombre_invitado', 'email', 'token')
    readonly_fields = ('token', 'link_qr', 'fecha_creacion')

    fieldsets = (
        ('Información del Invitado', {
            'fields': ('nombre_invitado', 'email')
        }),
        ('Configuración', {
            'fields': ('activa', 'token', 'fecha_creacion')
        }),
        ('Link de Acceso', {
            'fields': ('link_qr',),
            'classes': ('collapse',)
        }),
    )

    def estado_respuesta(self, obj):
        if hasattr(obj, 'respuesta'):
            estado = obj.respuesta.estado
            if estado == 'CONFIRMADO':
                return mark_safe('<span style="color: green;">✓ Confirmado</span>')
            elif estado == 'RECHAZADO':
                return mark_safe('<span style="color: red;">✗ Rechazado</span>')
        return mark_safe('<span style="color: orange;">⏳ Sin respuesta</span>')
    estado_respuesta.short_description = 'Estado'

    def link_acceso(self, obj):
        url = f'/invitacion/{obj.token}/'
        return format_html(
            '<a href="{}" target="_blank" style="color: #00ff9d;">🔗 Ver Invitación</a>',
            url
        )
    link_acceso.short_description = 'Acceso'

    def link_qr(self, obj):
        url = obj.get_link_absoluto()
        qr_api = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={url}"
        return mark_safe(
            f'<div style="text-align: center;">'
            f'<img src="{qr_api}" alt="QR" style="border: 2px solid #00ff9d; border-radius: 8px;"><br>'
            f'<small style="color: #94a3b8; word-break: break-all;">{url}</small>'
            f'</div>'
        )
    link_qr.short_description = 'Código QR y Link'

@admin.register(RespuestaRSVP)
class RespuestaRSVPAdmin(admin.ModelAdmin):
    list_display = ('invitacion_nombre', 'estado', 'lleva_acompanantes', 'cantidad_acompanantes', 'total_personas', 'fecha_respuesta')
    list_filter = ('estado', 'lleva_acompanantes', 'fecha_respuesta')
    search_fields = ('invitacion__nombre_invitado', 'mensaje')
    readonly_fields = ('invitacion', 'fecha_respuesta', 'total_personas')

    def invitacion_nombre(self, obj):
        return obj.invitacion.nombre_invitado
    invitacion_nombre.short_description = 'Invitado'