"""Agente conversacional: genera el mensaje hacia el cliente a partir de la
decisión del agente NBA, e interpreta mensajes entrantes del cliente
(modo reactivo) para decidir el siguiente turno.

Importante: este agente NO decide qué ofrecer (eso es exclusivo de
`reglas_negocio` + `nba`). Su única responsabilidad es la interacción en
lenguaje natural: explicar, responder objeciones dentro de lo autorizado, y
detectar cuándo debe pedir una nueva decisión al NBA o escalar.

En este prototipo, sin acceso a un LLM real, la interpretación de intención
se hace con reglas léxicas (`_detectar_intencion`) y la generación de texto
con plantillas. El punto de extensión para producción es
`GeneradorLLM` (interfaz) — hoy implementada por `GeneradorPlantillas`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from guardrails import evaluar_mensaje, validar_respuesta_agente
from models import ClienteObligacion
from nba import DecisionNBA, TipoAccion


class IntencionCliente(str, Enum):
    ACEPTA = "acepta"
    RECHAZA = "rechaza"
    PIDE_OTRA_ALTERNATIVA = "pide_otra_alternativa"
    CONSULTA_SALDO = "consulta_saldo"
    DIFICULTAD_FINANCIERA = "dificultad_financiera"
    INCUMPLIMIENTO_PREVIO_ADMITIDO = "incumplimiento_previo_admitido"
    AMBIGUO = "ambiguo"
    ESCALAMIENTO_GUARDRAIL = "escalamiento_guardrail"



# El orden importa: se evalúan de la más específica a la más genérica, para
# que un mensaje como "esa no, ¿tienes algo con menos cuota?" se clasifique
# como PIDE_OTRA_ALTERNATIVA y no como un RECHAZA genérico por contener "no".
_PATRONES_INTENCION = [
    (IntencionCliente.ACEPTA, [r"\b(s[ií]|acepto|de acuerdo|listo|dale|me sirve)\b"]),
    (IntencionCliente.PIDE_OTRA_ALTERNATIVA, [r"otra (opci[oó]n|alternativa)|algo diferente|m[aá]s barato|menos cuota|cu[aá]l me conviene|cu[aá]l es mejor"]),
    (IntencionCliente.CONSULTA_SALDO, [r"cu[aá]nto debo|saldo|estado de (mi )?cuenta|cu[aá]nto es la deuda"]),
    (IntencionCliente.DIFICULTAD_FINANCIERA, [r"perd[ií] el trabajo|no tengo (c[oó]mo|plata|dinero)|dificultad(es)? econ[oó]mic"]),
    (IntencionCliente.INCUMPLIMIENTO_PREVIO_ADMITIDO, [r"no pud(e|imos) cumplir|no alcanc[eé] a pagar el acuerdo"]),
    (IntencionCliente.RECHAZA, [r"\b(no|no puedo|no me sirve|no quiero)\b"]),
]


def _detectar_intencion(texto: str) -> IntencionCliente:
    texto_low = texto.lower()
    for intencion, patrones in _PATRONES_INTENCION:
        if any(re.search(p, texto_low) for p in patrones):
            return intencion
    return IntencionCliente.AMBIGUO


@dataclass
class TurnoConversacion:
    hablante: str  # 'agente' | 'cliente'
    texto: str
    metadata: dict | None = None


class GeneradorPlantillas:
    """Genera el texto del agente a partir de la decisión del NBA.
    Punto de extensión: reemplazar por una llamada a un LLM con un prompt
    que reciba la MISMA decisión estructurada (nunca al revés: el LLM no
    decide, solo redacta)."""

    TEXTOS_ALTERNATIVA = {
        "ampliacion_plazo": "una ampliación del plazo de tu deuda, para bajar el valor de la cuota mensual",
        "reduccion_cuota": "una reducción en el valor de tu cuota mensual",
        "renegociacion_tasa": "una renegociación de la tasa de interés de tu obligación",
        "reestructuracion": "una reestructuración completa de tu crédito",
    }

    def mensaje_apertura(self, ctx: ClienteObligacion, decision: DecisionNBA) -> str:
        saludo = f"Hola {ctx.nombre_cliente_demo}, te contactamos de Bancolombia por tu obligación de {ctx.producto}."
        if decision.accion == TipoAccion.OFRECER_ACUERDO_PAGO:
            return (
                f"{saludo} Podemos ofrecerte un acuerdo de pago: comprométete a pagar en los "
                f"próximos 5 días y evitamos que tu mora siga aumentando. ¿Te interesa?"
            )
        if decision.accion == TipoAccion.OFRECER_OPCION_PAGO:
            alt = decision.alternativa_elegida
            texto_alt = self.TEXTOS_ALTERNATIVA.get(alt.tipo.value, alt.descripcion)
            return f"{saludo} Tienes preaprobada {texto_alt}. ¿Quieres que te cuente los detalles?"
        if decision.accion == TipoAccion.DIFERIR_AUTO_CURA:
            return None  # no se contacta proactivamente
        if decision.accion == TipoAccion.MONITOREO_SIN_OFERTA:
            return None
        return None

    def mensaje_otra_alternativa(self, elegibles_restantes) -> str:
        if not elegibles_restantes:
            return (
                "Entiendo. En este momento no tengo otra opción preaprobada distinta para "
                "ofrecerte; te comunico con un asesor para revisar tu caso con más detalle."
            )
        alt = elegibles_restantes[0]
        texto_alt = self.TEXTOS_ALTERNATIVA.get(alt.tipo.value, alt.descripcion)
        return f"Claro, también tienes disponible {texto_alt}. ¿Esa te sirve más?"

    def mensaje_saldo(self, ctx: ClienteObligacion) -> str:
        return (
            f"Tu saldo de capital actual es de ${ctx.saldo_capital:,.0f} y llevas "
            f"{ctx.dias_mora} días en mora. La cuota mensual es de ${ctx.valor_cuota_mes:,.0f}."
        )

    def mensaje_dificultad_financiera(self) -> str:
        return (
            "Lamento escuchar eso. Cuéntame un poco más de tu situación para ver qué opción "
            "se ajusta mejor; si ninguna de las alternativas preaprobadas te alcanza, te "
            "conecto con un gestor humano que pueda revisar condiciones especiales."
        )

    def mensaje_escalamiento(self, motivo: str) -> str:
        return (
            "Voy a transferir tu caso a uno de nuestros asesores humanos para darte la mejor "
            "atención en este tema. En un momento te contactan."
        )

    def mensaje_cierre_aceptacion(self, alt_o_acuerdo: str) -> str:
        return f"Perfecto, quedó registrado tu {alt_o_acuerdo}. Te llegará la confirmación por los canales oficiales."


class AgenteConversacional:
    def __init__(self, generador: GeneradorPlantillas | None = None):
        self.generador = generador or GeneradorPlantillas()

    def abrir_conversacion(self, ctx: ClienteObligacion, decision: DecisionNBA) -> TurnoConversacion | None:
        texto = self.generador.mensaje_apertura(ctx, decision)
        if texto is None:
            return None
        alternativas_autorizadas = {
            a.tipo.value for a in (decision.elegibilidad.opciones_pago_elegibles if decision.elegibilidad else [])
        }
        assert validar_respuesta_agente(texto, alternativas_autorizadas), "Respuesta menciona alternativa no autorizada"
        return TurnoConversacion("agente", texto)

    def procesar_mensaje_cliente(
        self, texto_cliente: str, ctx: ClienteObligacion, decision: DecisionNBA
    ) -> tuple[TurnoConversacion, IntencionCliente, bool]:
        """Devuelve (turno_respuesta_agente, intencion_detectada, requiere_escalamiento)."""
        guard = evaluar_mensaje(texto_cliente)
        if guard.requiere_escalamiento:
            texto = self.generador.mensaje_escalamiento(guard.motivo)
            return TurnoConversacion("agente", texto, {"guardrail": guard.motivo}), IntencionCliente.ESCALAMIENTO_GUARDRAIL, True

        intencion = _detectar_intencion(texto_cliente)

        if intencion == IntencionCliente.ACEPTA:
            etiqueta = (
                decision.alternativa_elegida.descripcion
                if decision.alternativa_elegida else "acuerdo de pago a 5 días"
            )
            return TurnoConversacion("agente", self.generador.mensaje_cierre_aceptacion(etiqueta)), intencion, False

        if intencion == IntencionCliente.PIDE_OTRA_ALTERNATIVA:
            restantes = [
                a for a in (decision.elegibilidad.opciones_pago_elegibles if decision.elegibilidad else [])
                if a != decision.alternativa_elegida
            ]
            texto = self.generador.mensaje_otra_alternativa(restantes)
            if restantes:
                # La nueva alternativa ofrecida pasa a ser "la oferta sobre la
                # mesa": si el cliente acepta en el siguiente turno, debe
                # quedar registrada ESTA, no la que se priorizó originalmente.
                decision.alternativa_elegida = restantes[0]
            return TurnoConversacion("agente", texto), intencion, False

        if intencion == IntencionCliente.CONSULTA_SALDO:
            return TurnoConversacion("agente", self.generador.mensaje_saldo(ctx)), intencion, False

        if intencion == IntencionCliente.DIFICULTAD_FINANCIERA:
            return TurnoConversacion("agente", self.generador.mensaje_dificultad_financiera()), intencion, False

        if intencion == IntencionCliente.RECHAZA:
            return TurnoConversacion(
                "agente",
                "Entiendo, gracias por contarme. Quedas con la oferta disponible por si cambias de opinión; "
                "cualquier cosa aquí estoy.",
            ), intencion, False

        if intencion == IntencionCliente.INCUMPLIMIENTO_PREVIO_ADMITIDO:
            return TurnoConversacion(
                "agente",
                "Entiendo que se complicó cumplir el acuerdo anterior. Voy a escalar tu caso a un gestor humano "
                "para revisar una alternativa ajustada a tu situación actual.",
            ), intencion, True

        return TurnoConversacion(
            "agente",
            "Perdón, no logré entender bien tu mensaje. ¿Puedes contarme un poco más para ayudarte mejor?",
        ), intencion, False
