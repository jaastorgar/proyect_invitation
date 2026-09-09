/**
 * ========================================
 * VARIABLES GLOBALES
 * ========================================
 */
let asiste = null;
let llevaAcompanantes = false;
let refreshInterval = null;
const REFRESH_INTERVAL = 10000; // 10 segundos

/**
 * ========================================
 * FORMULARIO RSVP - INVITACIÓN
 * ========================================
 */

function seleccionarAsistencia(valor) {
    asiste = valor;

    const btnSi = document.getElementById('btn-si');
    const btnNo = document.getElementById('btn-no');
    const acompanantesSection = document.getElementById('acompanantes-section');
    const mensajeSection = document.getElementById('mensaje-section');
    const btnSubmit = document.getElementById('btn-submit');

    if (!btnSi) return; // No estamos en la página de invitación

    btnSi.classList.remove('active');
    btnNo.classList.remove('active');

    if (valor) {
        btnSi.classList.add('active');
        acompanantesSection.style.display = 'block';
        mensajeSection.style.display = 'block';
        btnSubmit.style.display = 'flex';
    } else {
        btnNo.classList.add('active');
        acompanantesSection.style.display = 'none';
        mensajeSection.style.display = 'none';
        btnSubmit.style.display = 'flex';
    }
}

function seleccionarAcompanantes(valor) {
    llevaAcompanantes = valor;

    const btnAcompSi = document.getElementById('btn-acomp-si');
    const btnAcompNo = document.getElementById('btn-acomp-no');
    const cantidadSection = document.getElementById('cantidad-section');

    if (!btnAcompSi) return;

    btnAcompSi.classList.remove('active');
    btnAcompNo.classList.remove('active');

    if (valor) {
        btnAcompSi.classList.add('active');
        cantidadSection.style.display = 'block';
    } else {
        btnAcompNo.classList.add('active');
        cantidadSection.style.display = 'none';
    }
}

function mostrarMensaje(texto, tipo) {
    const statusMsg = document.getElementById('status-msg');
    if (!statusMsg) return;

    statusMsg.innerText = texto;
    statusMsg.className = `show ${tipo}`;

    setTimeout(() => {
        statusMsg.classList.remove('show');
    }, 4000);
}

async function enviarRSVP() {
    const csrfToken = document.getElementById('csrf-token');
    const token = document.getElementById('token');
    const btnSubmit = document.getElementById('btn-submit');

    if (!csrfToken || !token) return;

    if (asiste === null) {
        mostrarMensaje('Debes seleccionar si asistirás o no.', 'error');
        return;
    }

    const cantidad = asiste && llevaAcompanantes
        ? parseInt(document.getElementById('cantidad').value) || 0
        : 0;
    const mensaje = asiste ? document.getElementById('mensaje').value.trim() : '';

    if (asiste && llevaAcompanantes && cantidad > 5) {
        mostrarMensaje('Máximo 5 acompañantes permitidos.', 'error');
        return;
    }

    btnSubmit.disabled = true;
    btnSubmit.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Procesando...';

    try {
        const res = await fetch(`/api/responder/${token.value}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken.value
            },
            body: JSON.stringify({
                asiste: asiste,
                lleva_acompanantes: llevaAcompanantes,
                cantidad_acompanantes: cantidad,
                mensaje: mensaje
            })
        });

        const data = await res.json();

        if (res.ok) {
            window.location.reload();
        } else {
            mostrarMensaje(`Error: ${data.error}`, 'error');
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Confirmar Respuesta';
        }
    } catch (error) {
        mostrarMensaje('Error de conexión. Intenta de nuevo.', 'error');
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Confirmar Respuesta';
        console.error('Error:', error);
    }
}

/**
 * ========================================
 * DASHBOARD - UTILIDADES
 * ========================================
 */

function copiarLink(token) {
    const url = `${window.location.origin}/invitacion/${token}/`;
    navigator.clipboard.writeText(url).then(() => {
        mostrarToast('Link copiado al portapapeles');
    }).catch(err => {
        console.error('Error al copiar:', err);
        mostrarToast('Error al copiar el link');
    });
}

function compartirWhatsapp(nombre, token) {
    const url = `${window.location.origin}/invitacion/${token}/`;
    const mensaje = `Hola ${nombre}, estás invitado a mi titulación en Ingeniería en Informática. \n\nPor favor, confirma tu asistencia aquí: ${url}`;
    const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(mensaje)}`;
    window.open(whatsappUrl, '_blank');
}

function mostrarToast(mensaje) {
    const toast = document.getElementById('toast');
    if (!toast) return;

    toast.querySelector('span').innerText = mensaje;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

/**
 * ========================================
 * DASHBOARD - AUTO-REFRESH Y TABLA
 * ========================================
 */

async function actualizarDashboard() {
    try {
        const response = await fetch('/api/dashboard/');

        if (!response.ok) {
            console.error('Error al actualizar dashboard:', response.status);
            return;
        }

        const data = await response.json();

        // Actualizar métricas con animación
        actualizarMetrica('metric-invitaciones', data.total_invitaciones);
        actualizarMetrica('metric-confirmados', data.total_confirmados);
        actualizarMetrica('metric-personas', data.total_personas);
        actualizarMetrica('metric-rechazados', data.total_rechazados);
        actualizarMetrica('metric-pendientes', data.total_pendientes);

        // Actualizar tabla de invitaciones
        if (data.lista_invitaciones) {
            actualizarTablaInvitaciones(data.lista_invitaciones);
            const badge = document.getElementById('badge-count');
            if (badge) badge.innerText = `${data.lista_invitaciones.length} registros`;
        }

        // Actualizar timestamp
        const now = new Date();
        const timeString = now.toLocaleTimeString('es-CL', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        const lastUpdate = document.getElementById('last-update');
        if (lastUpdate) lastUpdate.innerText = `Última actualización: ${timeString}`;

    } catch (error) {
        console.error('Error en auto-refresh:', error);
    }
}

function actualizarMetrica(elementId, nuevoValor) {
    const element = document.getElementById(elementId);
    if (!element) return;

    const valorActual = parseInt(element.innerText);

    if (valorActual !== nuevoValor) {
        element.parentElement.classList.add('updating');
        element.innerText = nuevoValor;

        setTimeout(() => {
            element.parentElement.classList.remove('updating');
        }, 500);
    }
}

function actualizarTablaInvitaciones(lista) {
    const tbody = document.getElementById('tabla-invitaciones');
    if (!tbody) return;

    if (lista.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="empty-state">
                    <i class="fa-solid fa-inbox"></i>
                    <p>Aún no hay invitaciones creadas.</p>
                </td>
            </tr>`;
        return;
    }

    let html = '';
    lista.forEach(inv => {
        html += `
            <tr>
                <td class="name-cell">
                    <i class="fa-regular fa-user"></i>
                    <div>
                        <strong>${inv.nombre}</strong>
                        <small>${inv.email}</small>
                    </div>
                </td>
                <td>
                    <span class="status-badge ${inv.estado_clase}">${inv.estado_texto}</span>
                </td>
                <td class="text-center">${inv.acomp_html}</td>
                <td class="message-cell">${inv.msg_html}</td>
                <td>
                    <a href="/invitacion/${inv.token}/" target="_blank" class="action-btn" title="Ver Invitación">
                        <i class="fa-solid fa-eye"></i>
                    </a>
                    <button onclick="copiarLink('${inv.token}')" class="action-btn" title="Copiar Link">
                        <i class="fa-solid fa-copy"></i>
                    </button>
                    <button onclick="compartirWhatsapp('${inv.nombre}', '${inv.token}')" class="action-btn whatsapp-btn" title="Compartir por WhatsApp">
                        <i class="fa-brands fa-whatsapp"></i>
                    </button>
                </td>
            </tr>`;
    });

    tbody.innerHTML = html;
}

function iniciarAutoRefresh() {
    actualizarDashboard();
    refreshInterval = setInterval(actualizarDashboard, REFRESH_INTERVAL);
}

function detenerAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}

// Iniciar auto-refresh cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciarAutoRefresh);
} else {
    iniciarAutoRefresh();
}

// Pausar auto-refresh cuando la pestaña no está visible
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        detenerAutoRefresh();
    } else {
        iniciarAutoRefresh();
    }
});