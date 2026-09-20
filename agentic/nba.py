"""Agente de Siguiente Mejor Acción (Next Best Action).

Combina: (a) lo que las reglas de negocio AUTORIZAN (reglas_negocio.py,
determinístico, no negociable) con (b) las señales analíticas — la
propensión a aceptar del modelo de la Parte 1, y los scores actuales del
banco (propensión de pago, alerta temprana, auto-cura) — para decidir QUÉ
acción tomar y, si hay varias opciones de pago elegibles, CUÁL priorizar.

Este agente NUNCA agrega alternativas que `reglas_negocio` no autorizó; solo
prioriza y decide entre lo ya autorizado, o decide no ofrecer nada / escalar.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from models import AlternativaPreaprobada, ClienteObligacion, TipoAlternativa
from reglas_negocio import DecisionElegibilidad, evaluar_elegibilidad

UMBRAL_PROPENSION_ACCION_PROACTIVA = 0.5
UMBRAL_AUTO_CURA_NO_MOLESTAR = 0.75  # si es muy probable que se ponga al día solo, no se gestiona agresivamente


class TipoAccion(str, Enum):
    ESCALAR_HUMANO = "escalar_humano"
    OFRECER_ACUERDO_PAGO = "ofrecer_acuerdo_pago"
    OFRECER_OPCION_PAGO = "ofrecer_opcion_pago"
    MONITOREO_SIN_OFERTA = "monitoreo_sin_oferta"
    DIFERIR_AUTO_CURA = "diferir_auto_cura"


# Orden de preferencia cuando hay empate de "alivio esperado": alternativas
# más profundas primero para mora alta, más leves primero para mora baja.
# Esto es un supuesto de negocio explícito y parametrizable.
PRIORIDAD_MORA_ALTA = [
    TipoAlternativa.REESTRUCTURACION, TipoAlternativa.RENEGOCIACION_TASA,
    TipoAlternativa.AMPLIACION_PLAZO, TipoAlternativa.REDUCCION_CUOTA,
]
PRIORIDAD_MORA_BAJA = [
    TipoAlternativa.REDUCCION_CUOTA, TipoAlternativa.AMPLIACION_PLAZO,
    TipoAlternativa.RENEGOCIACION_TASA, TipoAlternativa.REESTRUCTURACION,
]


@dataclass
class DecisionNBA:
    accion: TipoAccion
    alternativa_elegida: AlternativaPreaprobada | None = None
    explicacion: str = ""
    elegibilidad: DecisionElegibilidad | None = None
    score_usado: float | None = None


def _elegir_mejor_alternativa(elegibles: list[AlternativaPreaprobada], dias_mora: int) -> AlternativaPreaprobada:
    prioridad = PRIORIDAD_MORA_ALTA if dias_mora > 60 else PRIORIDAD_MORA_BAJA
    orden = {t: i for i, t in enumerate(prioridad)}
    return sorted(elegibles, key=lambda a: orden.get(a.tipo, len(prioridad)))[0]


def decidir_siguiente_accion(ctx: ClienteObligacion) -> DecisionNBA:
    elegibilidad = evaluar_elegibilidad(ctx)

    if elegibilidad.requiere_escalamiento_humano:
        return DecisionNBA(
            accion=TipoAccion.ESCALAR_HUMANO,
            explicacion=f"Escalamiento por reglas de negocio: {elegibilidad.motivo_escalamiento}",
            elegibilidad=elegibilidad,
        )

    propension = ctx.prob_aceptacion_opcion_pago
    auto_cura = ctx.prob_auto_cura or 0.0

    # Auto-cura muy probable y mora muy temprana -> no gastar gestión intensa
    if ctx.dias_mora <= 15 and auto_cura >= UMBRAL_AUTO_CURA_NO_MOLESTAR:
        return DecisionNBA(
            accion=TipoAccion.DIFERIR_AUTO_CURA,
            explicacion=(
                f"Probabilidad de auto-cura alta ({auto_cura:.0%}) con mora muy "
                "temprana; se difiere la gestión intensa para no generar fricción "
                "innecesaria (según lineamiento de auto-cura del banco)."
            ),
            elegibilidad=elegibilidad,
            score_usado=auto_cura,
        )

    if elegibilidad.opciones_pago_elegibles:
        alt = _elegir_mejor_alternativa(elegibilidad.opciones_pago_elegibles, ctx.dias_mora)
        return DecisionNBA(
            accion=TipoAccion.OFRECER_OPCION_PAGO,
            alternativa_elegida=alt,
            explicacion=(
                f"Cliente elegible para {len(elegibilidad.opciones_pago_elegibles)} "
                f"opción(es) de pago; se prioriza '{alt.tipo.value}' según mora "
                f"({ctx.dias_mora} días) y disponibilidad. Propensión estimada del "
                f"modelo: {propension:.0%}." if propension is not None else "sin score de propensión disponible."
            ),
            elegibilidad=elegibilidad,
            score_usado=propension,
        )

    if elegibilidad.puede_ofrecer_acuerdo_pago:
        return DecisionNBA(
            accion=TipoAccion.OFRECER_ACUERDO_PAGO,
            explicacion=(
                "No hay opciones de pago preaprobadas elegibles vigentes, pero la "
                "obligación está en gestión temprana y sin restricciones: se ofrece "
                "un acuerdo de pago a máximo 5 días."
            ),
            elegibilidad=elegibilidad,
            score_usado=propension,
        )

    return DecisionNBA(
        accion=TipoAccion.MONITOREO_SIN_OFERTA,
        explicacion="No hay oferta autorizada para esta obligación en este momento: " + "; ".join(elegibilidad.motivos_bloqueo),
        elegibilidad=elegibilidad,
        score_usado=propension,
    )
