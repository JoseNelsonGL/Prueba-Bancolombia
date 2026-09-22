"""Generador de contextos sintéticos aleatorios para la prueba masiva de
invariantes (property-based testing) del sistema agéntico.

Complementa a `mock_data.py` (14 escenarios DIRIGIDOS, pensados a mano para
casos conocidos) con una fuente de casos ALEATORIOS, reproducible mediante
una semilla fija, que explora el espacio de combinaciones sin limitarse a
lo que a alguien se le ocurrió escribir a mano. Deliberadamente NO usa
datos reales de la Parte 1 (trtest.csv): todo se genera sintéticamente,
para que la suite de pruebas del sistema agéntico siga siendo independiente
de los datos confidenciales de la prueba y corra igual aquí, en CI
(GitHub Actions) y en cualquier computador, sin necesitar esos archivos.

Las probabilidades de cada rama (restricción dura, incumplimiento
reciente, más de 3 alternativas preaprobadas, opción de pago ya aceptada,
etc.) están deliberadamente ponderadas para que, sobre una muestra de
varios cientos de casos, cada rama del motor de reglas se ejercite un
número de veces suficiente para ser una prueba real y no una casualidad.
"""
from __future__ import annotations

import random
from datetime import date, timedelta

from models import (
    AlternativaPreaprobada, ClienteObligacion, EventoAplicacion,
    HistorialGestion, TipoAlternativa,
)

HOY = date(2024, 1, 15)

PRODUCTOS = ["Libre Inversión", "Tarjeta de Crédito", "Crédito de Vehículo", "Libranza"]

# ~27% de probabilidad de alguna restricción dura -- lo bastante frecuente
# para que la prueba masiva ejercite esa rama con regularidad.
RESTRICCIONES = [None] * 8 + ["juridico", "fraude", "cliente_fallecido"]

RESULTADOS_GESTION = ["acuerdo_generado", "rechazo", "incumplimiento", "sin_contacto"]

ETIQUETAS_ALTERNATIVA = {
    TipoAlternativa.AMPLIACION_PLAZO: "Ampliación de plazo",
    TipoAlternativa.REDUCCION_CUOTA: "Reducción de cuota",
    TipoAlternativa.RENEGOCIACION_TASA: "Renegociación de tasa",
    TipoAlternativa.REESTRUCTURACION: "Reestructuración",
}


def _alt(tipo: TipoAlternativa, codigo: str) -> AlternativaPreaprobada:
    return AlternativaPreaprobada(tipo=tipo, codigo=codigo, descripcion=ETIQUETAS_ALTERNATIVA[tipo])


def generar_contexto_aleatorio(rng: random.Random, i: int) -> ClienteObligacion:
    """Genera UNA obligación sintética con campos aleatorios pero
    realistas. `rng` debe ser un `random.Random` con semilla fija para que
    la muestra completa sea reproducible."""
    tramo_mora = rng.choice(["temprana", "media", "alta", "muy_alta"])
    dias_mora = {
        "temprana": rng.randint(0, 15),
        "media": rng.randint(16, 60),
        "alta": rng.randint(61, 90),
        "muy_alta": rng.randint(91, 400),
    }[tramo_mora]

    saldo_capital = round(rng.uniform(300_000, 40_000_000), -3)
    valor_cuota_mes = round(saldo_capital * rng.uniform(0.02, 0.15), -3)

    tipos_disponibles = list(TipoAlternativa)
    # 0 a 5 alternativas preaprobadas (a veces más de 3, para ejercitar el
    # recorte por regla de negocio de "máximo 3 por obligación/mes").
    n_alt = rng.choice([0, 1, 1, 2, 2, 3, 3, 4, 5])
    alternativas = [
        _alt(rng.choice(tipos_disponibles), f"RND-{i:04d}-{j}")
        for j in range(n_alt)
    ]

    n_aplic = rng.choice([0, 0, 0, 1, 1, 2])
    historial_aplicaciones = [
        EventoAplicacion(
            tipo=rng.choice(tipos_disponibles),
            fecha_aplicacion=HOY - timedelta(days=rng.randint(0, 200)),
        )
        for _ in range(n_aplic)
    ]

    n_gest = rng.choice([0, 0, 1, 1, 2, 3])
    historial_gestiones = [
        HistorialGestion(
            fecha=HOY - timedelta(days=rng.randint(0, 200)),
            canal=rng.choice(["agente_ia", "gestor_humano", "call_center"]),
            resultado=rng.choice(RESULTADOS_GESTION),
        )
        for _ in range(n_gest)
    ]

    return ClienteObligacion(
        nit_enmascarado=f"NIT-RND-{i:04d}",
        num_oblig_enmascarado=f"OBL-RND-{i:04d}",
        nombre_cliente_demo=f"Cliente sintético {i} (ficticio)",
        dias_mora=dias_mora,
        saldo_capital=saldo_capital,
        valor_cuota_mes=valor_cuota_mes,
        producto=rng.choice(PRODUCTOS),
        alternativas_preaprobadas=alternativas,
        historial_aplicaciones=historial_aplicaciones,
        historial_gestiones=historial_gestiones,
        acepto_opcion_pago_vigente=rng.random() < 0.15,
        restriccion_ofrecimiento=rng.choice(RESTRICCIONES),
        ingreso_mensual_estimado=(
            round(rng.uniform(1_000_000, 15_000_000), -3) if rng.random() < 0.8 else None
        ),
        prob_aceptacion_opcion_pago=round(rng.uniform(0, 1), 3),
        prob_propension_pago=round(rng.uniform(0, 1), 3),
        prob_alerta_temprana=round(rng.uniform(0, 1), 3),
        prob_auto_cura=round(rng.uniform(0, 1), 3),
        fecha_referencia=HOY,
    )


def generar_muestra(n: int, semilla: int = 42) -> list[ClienteObligacion]:
    """Genera una muestra de `n` obligaciones sintéticas, reproducible: la
    misma semilla siempre produce exactamente la misma muestra."""
    rng = random.Random(semilla)
    return [generar_contexto_aleatorio(rng, i) for i in range(n)]
