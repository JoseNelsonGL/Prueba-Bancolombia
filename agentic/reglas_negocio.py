"""Motor de reglas de negocio: la ÚNICA fuente de verdad sobre qué se le
puede ofrecer a un cliente. Se aísla deliberadamente de los agentes de
lenguaje/razonamiento: un LLM puede decidir CÓMO comunicar la oferta, pero
JAMÁS decide QUÉ ofrecer por fuera de lo que este módulo autoriza. Esto es
lo que garantiza "ofrecer únicamente acuerdos u opciones de pago para los
que el cliente sea elegible" de forma determinística y auditable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from models import AlternativaPreaprobada, ClienteObligacion, TipoAlternativa

MORA_MAXIMA_ACUERDO_TEMPRANO = 90  # días; acuerdos aplican a gestión "temprana"
DIAS_MAX_COMPROMISO_ACUERDO = 5


@dataclass
class DecisionElegibilidad:
    opciones_pago_elegibles: list[AlternativaPreaprobada] = field(default_factory=list)
    puede_ofrecer_acuerdo_pago: bool = False
    motivos_bloqueo: list[str] = field(default_factory=list)
    requiere_escalamiento_humano: bool = False
    motivo_escalamiento: str | None = None


def evaluar_elegibilidad(ctx: ClienteObligacion) -> DecisionElegibilidad:
    decision = DecisionElegibilidad()

    # 0. Restricciones duras (jurídico, fraude, fallecido, etc.) -> nunca ofrecer nada,
    #    siempre escalar.
    if ctx.restriccion_ofrecimiento:
        decision.motivos_bloqueo.append(
            f"Restricción activa: {ctx.restriccion_ofrecimiento}"
        )
        decision.requiere_escalamiento_humano = True
        decision.motivo_escalamiento = f"restriccion:{ctx.restriccion_ofrecimiento}"
        return decision

    # 1. Opciones de pago: solo si no tiene ya una opción de pago vigente
    #    aceptada, y el tipo no está en cooldown por una aplicación reciente.
    if ctx.acepto_opcion_pago_vigente:
        decision.motivos_bloqueo.append(
            "Ya tiene una opción de pago vigente aceptada; no aplica ofrecer otra."
        )
    else:
        bloqueadas = ctx.alternativas_en_cooldown()
        for alt in ctx.alternativas_preaprobadas:
            if alt.tipo in bloqueadas:
                decision.motivos_bloqueo.append(
                    f"{alt.tipo.value} en cooldown por aplicación reciente."
                )
                continue
            decision.opciones_pago_elegibles.append(alt)

        # Regla explícita del enunciado: máximo 3 opciones preaprobadas por
        # obligación/mes. Si la fuente de preaprobación ya trae más de 3
        # (dato inconsistente), se recorta y se deja trazabilidad.
        if len(decision.opciones_pago_elegibles) > 3:
            decision.motivos_bloqueo.append(
                "Se recibieron más de 3 alternativas preaprobadas; se recorta a 3 "
                "por regla de negocio y se marca para revisión de calidad de datos."
            )
            decision.opciones_pago_elegibles = decision.opciones_pago_elegibles[:3]

    # 2. Acuerdo de pago (compromiso a <=5 días): gestión temprana, y solo si
    #    el cliente NO aceptó ya una opción de pago, y no hay restricción.
    if not ctx.acepto_opcion_pago_vigente and ctx.dias_mora <= MORA_MAXIMA_ACUERDO_TEMPRANO:
        decision.puede_ofrecer_acuerdo_pago = True
    elif ctx.acepto_opcion_pago_vigente:
        decision.motivos_bloqueo.append(
            "No se ofrece acuerdo de pago: ya aceptó una opción de pago."
        )

    return decision


def hubo_incumplimiento_reciente(ctx: ClienteObligacion, dias_ventana: int = 90) -> bool:
    for g in ctx.historial_gestiones:
        if g.resultado == "incumplimiento" and (ctx.fecha_referencia - g.fecha) <= timedelta(days=dias_ventana):
            return True
    return False
