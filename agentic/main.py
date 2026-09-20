"""Ejecuta todos los escenarios simulados a través del orquestador y guarda
las transcripciones + decisiones en results/ para revisión (documento
técnico, sustentación, y como insumo de las pruebas funcionales)."""
from __future__ import annotations

import json
import os

from mock_data import escenarios
from orquestador import Orquestador

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    orq = Orquestador()
    salida = []

    for nombre, esc in escenarios().items():
        resultado = orq.ejecutar(
            esc["ctx"], modo=esc.get("modo", "proactivo"),
            mensajes_cliente=esc.get("mensajes_cliente", []),
        )
        registro = {
            "escenario": nombre,
            "descripcion": esc["descripcion"],
            "session_id": resultado.session_id,
            "accion_nba": resultado.decision_nba.accion.value,
            "explicacion_nba": resultado.decision_nba.explicacion,
            "escalado": resultado.escalado,
            "motivo_escalamiento": resultado.motivo_escalamiento,
            "transcript": [
                {"hablante": t.hablante, "texto": t.texto} for t in resultado.transcript
            ],
        }
        salida.append(registro)

        print(f"\n{'='*90}\nESCENARIO: {nombre}\n{esc['descripcion']}\n{'-'*90}")
        print(f"Acción NBA: {resultado.decision_nba.accion.value}")
        print(f"Explicación: {resultado.decision_nba.explicacion}")
        for t in resultado.transcript:
            print(f"  [{t.hablante}] {t.texto}")
        if resultado.escalado:
            print(f"  >>> ESCALADO A HUMANO. Motivo: {resultado.motivo_escalamiento}")

    with open(os.path.join(RESULTS_DIR, "transcripciones_agentico.json"), "w", encoding="utf-8") as f:
        json.dump(salida, f, indent=2, ensure_ascii=False)
    print(f"\n\nGuardado: {os.path.join(RESULTS_DIR, 'transcripciones_agentico.json')}")


if __name__ == "__main__":
    main()
