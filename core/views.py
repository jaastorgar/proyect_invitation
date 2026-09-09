import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Invitacion, RespuestaRSVP, ConfiguracionEvento


def invitacion_view(request, token):
    """
    Vista pública: Muestra la invitación personalizada según el token.
    """
    invitacion = get_object_or_404(Invitacion, token=token, activa=True)
    
    # Verificar si ya existe una respuesta
    respuesta_existente = None
    if hasattr(invitacion, 'respuesta'):
        respuesta_existente = invitacion.respuesta
    
    # Cargar configuración global del evento
    config_evento = ConfiguracionEvento.load()
    
    context = {
        'invitacion': invitacion,
        'respuesta': respuesta_existente,
        'config_evento': config_evento,
    }
    
    return render(request, 'invitacion.html', context)


def responder_rsvp(request, token):
    """
    API endpoint: Procesa la respuesta RSVP de una invitación específica.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    invitacion = get_object_or_404(Invitacion, token=token, activa=True)
    
    # Verificar si ya respondió
    if hasattr(invitacion, 'respuesta'):
        return JsonResponse(
            {'error': 'Esta invitación ya tiene una respuesta registrada'},
            status=400
        )
    
    try:
        data = json.loads(request.body)
        asiste = data.get('asiste')
        lleva_acompanantes = data.get('lleva_acompanantes', False)
        cantidad_acompanantes = int(data.get('cantidad_acompanantes', 0))
        mensaje = data.get('mensaje', '').strip()
        
        # Validaciones
        if asiste and lleva_acompanantes and cantidad_acompanantes > 5:
            return JsonResponse(
                {'error': 'Máximo 5 acompañantes permitidos'},
                status=400
            )
        
        # Determinar estado
        estado = 'CONFIRMADO' if asiste else 'RECHAZADO'
        
        # Crear respuesta
        respuesta = RespuestaRSVP.objects.create(
            invitacion=invitacion,
            estado=estado,
            lleva_acompanantes=lleva_acompanantes if asiste else False,
            cantidad_acompanantes=cantidad_acompanantes if (asiste and lleva_acompanantes) else 0,
            mensaje=mensaje
        )
        
        return JsonResponse({
            'status': 'ok',
            'estado': respuesta.estado,
            'mensaje': 'Respuesta registrada correctamente'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Formato JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)


@login_required(login_url='/admin/login/')
def dashboard_view(request):
    """
    Vista protegida: Panel de control con estadísticas de invitaciones.
    """
    invitaciones = Invitacion.objects.all().prefetch_related('respuesta').order_by('-fecha_creacion')
    
    # Calcular métricas
    total_invitaciones = invitaciones.count()
    total_respuestas = invitaciones.filter(respuesta__isnull=False).count()
    total_confirmados = invitaciones.filter(respuesta__estado='CONFIRMADO').count()
    total_rechazados = invitaciones.filter(respuesta__estado='RECHAZADO').count()
    total_pendientes = total_invitaciones - total_respuestas
    
    # Calcular total de personas (invitados + acompañantes)
    total_personas = sum([
        inv.respuesta.total_personas()
        for inv in invitaciones
        if hasattr(inv, 'respuesta') and inv.respuesta.estado == 'CONFIRMADO'
    ])
    
    # Calcular total de acompañantes
    total_acompanantes = sum([
        inv.respuesta.cantidad_acompanantes
        for inv in invitaciones
        if hasattr(inv, 'respuesta') and inv.respuesta.estado == 'CONFIRMADO'
    ])
    
    context = {
        'invitaciones': invitaciones,
        'total_invitaciones': total_invitaciones,
        'total_respuestas': total_respuestas,
        'total_confirmados': total_confirmados,
        'total_rechazados': total_rechazados,
        'total_pendientes': total_pendientes,
        'total_personas': total_personas,
        'total_acompanantes': total_acompanantes,
    }
    
    return render(request, 'dashboard.html', context)


@login_required(login_url='/admin/login/')
def dashboard_api_view(request):
    """
    API endpoint: Devuelve métricas + lista de invitaciones en JSON para auto-refresh.
    """
    invitaciones = Invitacion.objects.all().prefetch_related('respuesta').order_by('-fecha_creacion')
    
    # Calcular métricas
    total_invitaciones = invitaciones.count()
    total_confirmados = invitaciones.filter(respuesta__estado='CONFIRMADO').count()
    total_rechazados = invitaciones.filter(respuesta__estado='RECHAZADO').count()
    total_pendientes = total_invitaciones - (total_confirmados + total_rechazados)
    
    total_personas = sum([
        1 + inv.respuesta.cantidad_acompanantes
        for inv in invitaciones
        if hasattr(inv, 'respuesta') and inv.respuesta.estado == 'CONFIRMADO'
    ])
    
    # Construir lista para la tabla
    lista_invitaciones = []
    for inv in invitaciones:
        tiene_respuesta = hasattr(inv, 'respuesta')
        respuesta = inv.respuesta if tiene_respuesta else None
        
        if respuesta:
            estado_texto = respuesta.get_estado_display()
            estado_clase = respuesta.estado.lower()
        else:
            estado_texto = 'Pendiente'
            estado_clase = 'pendiente'
        
        # HTML de acompañantes
        if respuesta and respuesta.estado == 'CONFIRMADO' and respuesta.lleva_acompanantes:
            acomp_html = f'<span class="acomp-tag"><i class="fa-solid fa-user-plus"></i> {respuesta.cantidad_acompanantes}</span>'
        else:
            acomp_html = '<span class="text-muted">-</span>'
        
        # HTML de mensaje
        if respuesta and respuesta.mensaje:
            msg = respuesta.mensaje[:40]
            msg_html = f'<i class="fa-regular fa-comment"></i> {msg}{"..." if len(respuesta.mensaje) > 40 else ""}'
        else:
            msg_html = '<span class="text-muted">-</span>'
        
        lista_invitaciones.append({
            'nombre': inv.nombre_invitado,
            'email': inv.email or 'Sin email',
            'estado_texto': estado_texto,
            'estado_clase': estado_clase,
            'acomp_html': acomp_html,
            'msg_html': msg_html,
            'token': str(inv.token),
        })
    
    return JsonResponse({
        'total_invitaciones': total_invitaciones,
        'total_confirmados': total_confirmados,
        'total_rechazados': total_rechazados,
        'total_pendientes': total_pendientes,
        'total_personas': total_personas,
        'lista_invitaciones': lista_invitaciones,
    })


@login_required(login_url='/admin/login/')
def crear_invitacion_view(request):
    """
    Vista para crear nuevas invitaciones desde un formulario web.
    """
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        email = request.POST.get('email', '').strip()
        
        if nombre:
            Invitacion.objects.create(
                nombre_invitado=nombre,
                email=email if email else None
            )
            messages.success(request, f'Invitación creada exitosamente para {nombre}.')
            return redirect('dashboard')
        else:
            messages.error(request, 'El nombre del invitado es obligatorio.')
            
    return render(request, 'crear_invitacion.html')


@login_required(login_url='/admin/login/')
def dashboard_api_view(request):
    """
    API endpoint: Devuelve métricas + lista de invitaciones en JSON.
    """
    invitaciones = Invitacion.objects.all().prefetch_related('respuesta').order_by('-fecha_creacion')
    
    # Calcular métricas
    total_invitaciones = invitaciones.count()
    total_confirmados = invitaciones.filter(respuesta__estado='CONFIRMADO').count()
    total_rechazados = invitaciones.filter(respuesta__estado='RECHAZADO').count()
    total_pendientes = total_invitaciones - (total_confirmados + total_rechazados)
    
    total_personas = sum([
        1 + inv.respuesta.cantidad_acompanantes
        for inv in invitaciones
        if hasattr(inv, 'respuesta') and inv.respuesta.estado == 'CONFIRMADO'
    ])
    
    # Construir lista para la tabla
    lista_invitaciones = []
    for inv in invitaciones:
        tiene_respuesta = hasattr(inv, 'respuesta')
        respuesta = inv.respuesta if tiene_respuesta else None
        
        if respuesta:
            estado_texto = respuesta.get_estado_display()
            estado_clase = respuesta.estado.lower()
        else:
            estado_texto = 'Pendiente'
            estado_clase = 'pendiente'
        
        # HTML de acompañantes
        if respuesta and respuesta.estado == 'CONFIRMADO' and respuesta.lleva_acompanantes:
            acomp_html = f'<span class="acomp-tag"><i class="fa-solid fa-user-plus"></i> {respuesta.cantidad_acompanantes}</span>'
        else:
            acomp_html = '<span class="text-muted">-</span>'
        
        # HTML de mensaje
        if respuesta and respuesta.mensaje:
            msg = respuesta.mensaje[:40]
            msg_html = f'<i class="fa-regular fa-comment"></i> {msg}{"..." if len(respuesta.mensaje) > 40 else ""}'
        else:
            msg_html = '<span class="text-muted">-</span>'
        
        lista_invitaciones.append({
            'nombre': inv.nombre_invitado,
            'email': inv.email or 'Sin email',
            'estado_texto': estado_texto,
            'estado_clase': estado_clase,
            'acomp_html': acomp_html,
            'msg_html': msg_html,
            'token': str(inv.token),
        })
    
    return JsonResponse({
        'total_invitaciones': total_invitaciones,
        'total_confirmados': total_confirmados,
        'total_rechazados': total_rechazados,
        'total_pendientes': total_pendientes,
        'total_personas': total_personas,
        'lista_invitaciones': lista_invitaciones,
    })