"""Orquestador: coordina Contexto -> Reglas/NBA -> Conversacional ->
Guardrails -> Escalamiento para una interacción completa (proactiva o
reactiva), dejando traza de cada paso.

Patrón: "supervisor" simple (no un grafo complejo) porque el flujo de
negocio es lineal y auditable: primero se decide QUÉ se puede ofrecer
(determinístico), luego se conversa dentro de esos límites. Esto se
documenta en la arquitectura como decisión deliberada: para un dominio
regulado como cobranza, la previsibilidad y la auditabilidad pesan más que
la flexibilidad de un grafo de agentes totalmente dinámico.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from conversacional import AgenteConversacional, TurnoConversacion
from models import ClienteObligacion
from nba import DecisionNBA, TipoAccion, decidir_siguiente_accion
from trazabilidad import Trazador


@dataclass
class ResultadoSesion:
    session_id: str
    ctx: ClienteObligacion
    decision_nba: DecisionNBA
    transcript: list[TurnoConversacion] = field(default_factory=list)
    escalado: bool = False
    motivo_escalamiento: str | None = None


class Orquestador:
    def __init__(self):
        self.conversacional = AgenteConversacional()

    def ejecutar(
        self,
        ctx: ClienteObligacion,
        modo: str = "proactivo",
        mensajes_cliente: list[str] | None = None,
    ) -> ResultadoSesion:
        traza = Trazador()
        traza.registrar("orquestador", "inicio_sesion", {
            "modo": modo, "obligacion": ctx.num_oblig_enmascarado, "nit": ctx.nit_enmascarado,
        })

        decision = decidir_siguiente_accion(ctx)
        traza.registrar("nba", "decision", {
            "accion": decision.accion.value,
            "alternativa": decision.alternativa_elegida.tipo.value if decision.alternativa_elegida else None,
            "explicacion": decision.explicacion,
            "motivos_bloqueo": decision.elegibilidad.motivos_bloqueo if decision.elegibilidad else [],
        })

        resultado = ResultadoSesion(session_id=traza.session_id, ctx=ctx, decision_nba=decision)

        if decision.accion == TipoAccion.ESCALAR_HUMANO:
            resultado.escalado = True
            resultado.motivo_escalamiento = decision.explicacion
            traza.registrar("orquestador", "escalamiento", {"motivo": decision.explicacion})
            return resultado

        if modo == "proactivo":
            apertura = self.conversacional.abrir_conversacion(ctx, decision)
            if apertura is None:
                traza.registrar("orquestador", "sin_contacto_proactivo", {"accion": decision.accion.value})
                return resultado
            resultado.transcript.append(apertura)
            traza.registrar("conversacional", "mensaje_agente", {"texto": apertura.texto})

        for msg in (mensajes_cliente or []):
            resultado.transcript.append(TurnoConversacion("cliente", msg))
            traza.registrar("cliente", "mensaje", {"texto": msg})

            respuesta, intencion, escalar = self.conversacional.procesar_mensaje_cliente(msg, ctx, decision)
            resultado.transcript.append(respuesta)
            traza.registrar("conversacional", "mensaje_agente", {
                "texto": respuesta.texto, "intencion_detectada": intencion.value,
            })

            if escalar:
                resultado.escalado = True
                resultado.motivo_escalamiento = respuesta.metadata.get("guardrail") if respuesta.metadata else intencion.value
                traza.registrar("orquestador", "escalamiento", {"motivo": resultado.motivo_escalamiento})
                break

        traza.registrar("orquestador", "fin_sesion", {"escalado": resultado.escalado})
        return resultado
