import uuid
from django.db import models
from django.utils import timezone

class ConfiguracionEvento(models.Model):
    """
    Modelo Singleton para guardar la información global del evento.
    Solo debe existir un registro en la base de datos.
    """
    titulo_evento = models.CharField(max_length=200, default="Fiesta de Graduación")
    fecha = models.DateField(verbose_name="Fecha del evento")
    hora = models.TimeField(verbose_name="Hora del evento")
    lugar = models.CharField(max_length=255, verbose_name="Lugar / Dirección")
    organizador = models.CharField(max_length=150, default="Instituto Ameyali", verbose_name="Nombre del organizador/instituto")

    class Meta:
        verbose_name = "Configuración del Evento"
        verbose_name_plural = "Configuración del Evento"

    def __str__(self):
        return f"Configuración: {self.titulo_evento}"

    def save(self, *args, **kwargs):
        # Forzar a que solo exista un registro (Singleton)
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Invitacion(models.Model):
    """
    Modelo para crear invitaciones personalizadas con link único.
    """
    nombre_invitado = models.CharField(
        max_length=150,
        verbose_name='Nombre del Invitado'
    )
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name='Correo Electrónico'
    )
    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='Token Único'
    )
    fecha_creacion = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de Creación'
    )
    activa = models.BooleanField(
        default=True,
        verbose_name='Invitación Activa'
    )

    class Meta:
        verbose_name = 'Invitación'
        verbose_name_plural = 'Invitaciones'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Invitación para {self.nombre_invitado}"

    def get_link_absoluto(self, request=None):
        """Genera el link completo de la invitación"""
        if request:
            return request.build_absolute_uri(f'/invitacion/{self.token}/')
        return f'/invitacion/{self.token}/'

    def tiene_respuesta(self):
        """Verifica si ya hay una respuesta registrada"""
        return hasattr(self, 'respuesta')


class RespuestaRSVP(models.Model):
    """
    Modelo para almacenar la respuesta RSVP de cada invitación.
    """
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADO', 'Confirmado (Asiste)'),
        ('RECHAZADO', 'Rechazado (No asiste)'),
    ]

    invitacion = models.OneToOneField(
        Invitacion,
        on_delete=models.CASCADE,
        related_name='respuesta',
        verbose_name='Invitación'
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='PENDIENTE',
        verbose_name='Estado'
    )
    lleva_acompanantes = models.BooleanField(
        default=False,
        verbose_name='¿Lleva acompañantes?'
    )
    cantidad_acompanantes = models.PositiveIntegerField(
        default=0,
        verbose_name='Cantidad de Acompañantes'
    )
    mensaje = models.TextField(
        blank=True,
        null=True,
        verbose_name='Mensaje o Dedicatoria'
    )
    fecha_respuesta = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de Respuesta'
    )

    class Meta:
        verbose_name = 'Respuesta RSVP'
        verbose_name_plural = 'Respuestas RSVP'
        ordering = ['-fecha_respuesta']

    def __str__(self):
        return f"{self.invitacion.nombre_invitado} - {self.get_estado_display()}"

    def total_personas(self):
        """Calcula el total de personas (invitado + acompañantes)"""
        if self.estado == 'CONFIRMADO':
            return 1 + self.cantidad_acompanantes
        return 0