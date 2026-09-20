"""Modelos de datos del sistema agéntico de gestión de cartera en mora.

Estas clases representan el "contexto" que el Agente de Contexto ensambla
para cada obligación antes de que cualquier otro agente razone sobre ella.
Se usan dataclasses simples (no ORM) porque el prototipo no depende de una
base de datos real; en producción estos mismos campos vendrían de los
sistemas fuente (core bancario, motor de preaprobación, CRM de cobranza,
el modelo de propensión de la Parte 1).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum


class TipoAlternativa(str, Enum):
    AMPLIACION_PLAZO = "ampliacion_plazo"
    REDUCCION_CUOTA = "reduccion_cuota"
    RENEGOCIACION_TASA = "renegociacion_tasa"
    REESTRUCTURACION = "reestructuracion"


# Meses de "enfriamiento" (cooldown) por tipo de alternativa antes de poder
# ofrecer otra opción de pago sobre la misma obligación. Varía según el
# enunciado ("3 a 4 meses, depende de la opción aplicada"); estos valores
# son un supuesto explícito y quedan documentados como parámetro editable.
COOLDOWN_MESES_POR_ALTERNATIVA = {
    TipoAlternativa.AMPLIACION_PLAZO: 3,
    TipoAlternativa.REDUCCION_CUOTA: 3,
    TipoAlternativa.RENEGOCIACION_TASA: 4,
    TipoAlternativa.REESTRUCTURACION: 4,
}

MAX_OPCIONES_PREAPROBADAS_MES = 3


@dataclass
class AlternativaPreaprobada:
    tipo: TipoAlternativa
    codigo: str
    descripcion: str


@dataclass
class EventoAplicacion:
    """Una alternativa que ya fue aplicada a la obligación en el pasado."""
    tipo: TipoAlternativa
    fecha_aplicacion: date


@dataclass
class HistorialGestion:
    fecha: date
    canal: str  # 'agente_ia', 'gestor_humano', 'call_center', etc.
    resultado: str  # 'acuerdo_generado', 'rechazo', 'incumplimiento', 'sin_contacto', ...
    detalle: str = ""


@dataclass
class ClienteObligacion:
    """Contexto completo de una obligación de un cliente, ensamblado por el
    Agente de Contexto a partir de las fuentes de datos disponibles."""

    nit_enmascarado: str
    num_oblig_enmascarado: str
    nombre_cliente_demo: str  # nombre FICTICIO para la simulación, nunca dato real

    dias_mora: int
    saldo_capital: float
    valor_cuota_mes: float
    producto: str

    alternativas_preaprobadas: list[AlternativaPreaprobada] = field(default_factory=list)
    historial_aplicaciones: list[EventoAplicacion] = field(default_factory=list)
    historial_gestiones: list[HistorialGestion] = field(default_factory=list)

    acepto_opcion_pago_vigente: bool = False  # ya aceptó una opción de pago activa
    restriccion_ofrecimiento: str | None = None  # ej. 'juridico', 'fraude', 'cliente_fallecido'
    ingreso_mensual_estimado: float | None = None

    # Salidas del modelo analítico (Parte 1) y de los scores actuales del banco
    prob_aceptacion_opcion_pago: float | None = None  # salida del modelo Parte 1
    prob_propension_pago: float | None = None
    prob_alerta_temprana: float | None = None
    prob_auto_cura: float | None = None

    fecha_referencia: date = field(default_factory=date.today)

    def alternativas_en_cooldown(self) -> set[TipoAlternativa]:
        bloqueadas = set()
        for ev in self.historial_aplicaciones:
            meses_cooldown = COOLDOWN_MESES_POR_ALTERNATIVA[ev.tipo]
            limite = ev.fecha_aplicacion + timedelta(days=30 * meses_cooldown)
            if self.fecha_referencia < limite:
                bloqueadas.add(ev.tipo)
        return bloqueadas
