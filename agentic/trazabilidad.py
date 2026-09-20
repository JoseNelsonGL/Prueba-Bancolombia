"""Servicio de trazabilidad/auditoría. Cada decisión de cada agente se
registra como un evento estructurado (JSON Lines) con un `session_id`
común, para poder reconstruir end-to-end por qué el sistema tomó una
decisión (requisito explícito de la prueba: trazabilidad + explicabilidad).
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone

LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "results", "trazas_agentico.jsonl")


class Trazador:
    def __init__(self, session_id: str | None = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.eventos: list[dict] = []

    def registrar(self, agente: str, evento: str, detalle: dict):
        entry = {
            "session_id": self.session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agente": agente,
            "evento": evento,
            "detalle": detalle,
        }
        self.eventos.append(entry)
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
        return entry

    def resumen(self) -> list[dict]:
        return self.eventos
