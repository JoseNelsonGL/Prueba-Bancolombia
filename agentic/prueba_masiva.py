"""Corre la prueba masiva (simulación sobre N obligaciones sintéticas
aleatorias) de forma independiente a pytest, y guarda un resumen agregado
en results/ para revisión (documento técnico, sustentación).

Esto es el complemento "Masivas" a `main.py` (que corre los 14 escenarios
DIRIGIDOS): aquí no importa el detalle de cada caso individual, sino la
distribución de resultados sobre una muestra grande y la confirmación de
que ninguna de las garantías de negocio se rompió ni una sola vez.
Ver docs/pruebas_agentico.md, sección "Dirigidas vs. Masivas".
"""
from __future__ import annotations

import json
import os
from collections import Counter

from generador_aleatorio import generar_muestra
from nba import TipoAccion, decidir_siguiente_accion
from reglas_negocio import hubo_incumplimiento_reciente

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
N_MUESTRA_MASIVA = 400
SEMILLA = 42


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    muestra = generar_muestra(N_MUESTRA_MASIVA, semilla=SEMILLA)

    resultados = []
    violaciones = []
    conteo_acciones = Counter()

    for ctx in muestra:
        decision = decidir_siguiente_accion(ctx)
        conteo_acciones[decision.accion.value] += 1

        # Mismas invariantes que en tests/test_agentic.py::TestPruebasMasivas,
        # verificadas también aquí para que este script sirva como reporte
        # independiente, sin depender de correr pytest.
        if ctx.restriccion_ofrecimiento and (
            decision.accion != TipoAccion.ESCALAR_HUMANO or decision.alternativa_elegida is not None
        ):
            violaciones.append((ctx.nit_enmascarado, "restriccion_dura_no_escalo_o_ofrecio_algo"))

        if (
            not ctx.restriccion_ofrecimiento
            and hubo_incumplimiento_reciente(ctx)
            and (decision.accion != TipoAccion.ESCALAR_HUMANO or decision.alternativa_elegida is not None)
        ):
            violaciones.append((ctx.nit_enmascarado, "incumplimiento_reciente_no_escalo_o_ofrecio_algo"))

        if ctx.acepto_opcion_pago_vigente and decision.accion == TipoAccion.OFRECER_OPCION_PAGO:
            violaciones.append((ctx.nit_enmascarado, "ofrecio_opcion_pago_con_una_ya_vigente"))

        if decision.accion == TipoAccion.OFRECER_OPCION_PAGO:
            bloqueadas = ctx.alternativas_en_cooldown()
            if decision.alternativa_elegida.tipo in bloqueadas:
                violaciones.append((ctx.nit_enmascarado, "ofrecio_alternativa_en_cooldown"))

        if decision.elegibilidad is not None and len(decision.elegibilidad.opciones_pago_elegibles) > 3:
            violaciones.append((ctx.nit_enmascarado, "mas_de_3_opciones_elegibles"))

        resultados.append({
            "nit_enmascarado": ctx.nit_enmascarado,
            "dias_mora": ctx.dias_mora,
            "restriccion_ofrecimiento": ctx.restriccion_ofrecimiento,
            "acepto_opcion_pago_vigente": ctx.acepto_opcion_pago_vigente,
            "accion": decision.accion.value,
            "alternativa_elegida": decision.alternativa_elegida.codigo if decision.alternativa_elegida else None,
        })

    resumen = {
        "n_muestra": N_MUESTRA_MASIVA,
        "semilla": SEMILLA,
        "distribucion_acciones": dict(conteo_acciones),
        "n_violaciones": len(violaciones),
        "violaciones": violaciones,
    }

    with open(os.path.join(RESULTS_DIR, "resumen_prueba_masiva.json"), "w", encoding="utf-8") as f:
        json.dump({"resumen": resumen, "detalle": resultados}, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*90}\nPRUEBA MASIVA: {N_MUESTRA_MASIVA} obligaciones sintéticas (semilla={SEMILLA})\n{'-'*90}")
    print("Distribución de acciones:")
    for accion, n in conteo_acciones.most_common():
        print(f"  {accion:<25} {n:>4}  ({n / N_MUESTRA_MASIVA:.1%})")
    print(f"\nViolaciones de invariantes de negocio: {len(violaciones)}")
    if violaciones:
        for nit, motivo in violaciones:
            print(f"  >>> {nit}: {motivo}")
    else:
        print("  Ninguna. Las 5 garantías de negocio se cumplieron en los "
              f"{N_MUESTRA_MASIVA} casos generados.")
    print(f"\nGuardado: {os.path.join(RESULTS_DIR, 'resumen_prueba_masiva.json')}")


if __name__ == "__main__":
    main()
