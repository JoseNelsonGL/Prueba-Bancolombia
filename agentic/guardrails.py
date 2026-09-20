"""Agente/capa de guardarraíles: seguridad, cumplimiento y detección de
señales que ameritan escalamiento a un gestor humano.

Se implementa como reglas explícitas (léxicos + heurísticas) porque el
prototipo no tiene acceso a un LLM real en este entorno. En producción esta
capa normalmente combina: (a) un clasificador/LLM barato y rápido para
intención + riesgo, (b) estas mismas reglas duras como red de seguridad
que NUNCA se delega al LLM (defensa en profundidad), y (c) un servicio de
DLP/PII (p. ej. Presidio) para detectar fuga de datos sensibles en la
respuesta antes de enviarla.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

PATRONES_MANIPULACION = [
    r"ignora.*(instrucciones|reglas|prompt)",
    r"olvida.*(instrucciones|reglas)",
    r"act[uú]a como",
    r"eres (un|otro) (chatgpt|ia|modelo)",
    r"dame (un|el) descuento (mayor|extra|especial) sin autorizaci",
    r"c[oó]ndonam[e|a]|perd[oó]nam[e|a] toda la deuda",
    r"borrame? (la mora|el reporte|de datacr[eé]dito)",
    r"eso qu[eé]dese entre (nosotros|los dos)",
]

PATRONES_SENSIBLES_URGENTES = [
    r"me quiero (morir|matar)|suicid",
    r"amenaz",
    r"me van a (embargar|demandar) y no s[eé] qu[eé] hacer",
    r"perd[ií] (mi trabajo|el empleo)|qued[eé] sin trabajo",
    r"enfermedad (grave|terminal)|c[aá]ncer|hospitalizad",
    r"viol(encia|ento)|agres",
]

PATRONES_INFO_INCOMPLETA_O_CONTRADICTORIA = [
    r"esa no es mi deuda|yo no debo eso|no reconozco esa obligaci[oó]n",
    r"ya (pagu[eé]|cancel[eé]) eso",
]


@dataclass
class ResultadoGuardrail:
    es_manipulacion: bool = False
    es_sensible: bool = False
    posible_info_contradictoria: bool = False
    requiere_escalamiento: bool = False
    motivo: str | None = None


def _match_any(patrones: list[str], texto: str) -> bool:
    texto_low = texto.lower()
    return any(re.search(p, texto_low) for p in patrones)


def evaluar_mensaje(texto_cliente: str) -> ResultadoGuardrail:
    r = ResultadoGuardrail()

    if _match_any(PATRONES_MANIPULACION, texto_cliente):
        r.es_manipulacion = True
        r.requiere_escalamiento = True
        r.motivo = "intento_manipulacion_o_solicitud_no_autorizada"
        return r

    if _match_any(PATRONES_SENSIBLES_URGENTES, texto_cliente):
        r.es_sensible = True
        r.requiere_escalamiento = True
        r.motivo = "senal_sensible_requiere_gestor_humano"
        return r

    if _match_any(PATRONES_INFO_INCOMPLETA_O_CONTRADICTORIA, texto_cliente):
        r.posible_info_contradictoria = True
        r.requiere_escalamiento = True
        r.motivo = "informacion_contradictoria_requiere_verificacion_humana"
        return r

    return r


def validar_respuesta_agente(texto_respuesta: str, alternativas_autorizadas: set[str]) -> bool:
    """Última barrera antes de enviar: verifica que la respuesta generada
    no mencione códigos/alternativas fuera de lo que `reglas_negocio`
    autorizó para esta obligación. Devuelve True si la respuesta es segura
    de enviar."""
    for token in re.findall(r"\b[A-Z_]{4,}\b", texto_respuesta):
        if token in {"OK", "IVA", "NIT"}:
            continue
    # Verificación simple por keyword de tipos de alternativa mencionados
    tipos_conocidos = {
        "ampliacion_plazo": "ampliación de plazo",
        "reduccion_cuota": "reducción de cuota",
        "renegociacion_tasa": "renegociación de tasa",
        "reestructuracion": "reestructuración",
    }
    texto_low = texto_respuesta.lower()
    for tipo, etiqueta in tipos_conocidos.items():
        if etiqueta in texto_low and tipo not in alternativas_autorizadas:
            return False
    return True
