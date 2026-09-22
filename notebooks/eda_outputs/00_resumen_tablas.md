# Resumen de tablas crudas (data/raw/)


## trtest.csv
- Filas: 568,251 | Columnas: 49
- Variables: nit_enmascarado, num_oblig_orig_enmascarado, num_oblig_enmascarado, fecha_var_rpta_alt, var_rpta_alt, tipo_var_rpta_alt, banca, segmento, producto, producto_cons, aplicativo, min_mora, max_mora, dias_mora_fin, rango_mora, vlr_obligacion, vlr_vencido, saldo_capital, endeudamiento, desc_alternativa1, desc_alternativa2, desc_alternativa3, cant_alter_posibles, alter_posible1_2, alter_posible2_2, alter_posible3_2, cant_gestiones, cant_gestiones_binario, rpc, promesas_cumplidas, cant_promesas_cumplidas_binario, cant_acuerdo, cant_acuerdo_binario, descripcion_ranking_mejor_ult, descripcion_ranking_post_ult, marca_alt_rank, marca_alt_apli, valor_cuota_mes, pago_cuota, porc_pago_cuota, pago_mes, porc_pago_mes, pagos_tanque, marca_debito_mora, alternativa_aplicada_agr, marca_agrupada_rgo, marca_pago, marca_alternativa, marca_alternativa_orig


## master_customer_data.csv
- Filas: 430,000 | Columnas: 37
- Variables: nit_enmascarado, cod_tipo_doc, tipo_cli, ctrl_terc, genero_cli, ano_nac_cli, edad_cli, estado_civil, tipo_vivienda, num_hijos, personas_dependientes, nivel_academico, ocup, act_econom, sector, subsector, declarante, total_ing, tot_activos, tot_pasivos, origen_fondos, f_vinc, f_ult_mantenimiento, canal_actualizacion, cli_actualizado, segm, subsegm, nicho, region_of, nombre_dpto_dirp, egresos_mes, tot_patrimonio, ciiu, smmlv, year, month, ingestion_day


## probabilidad_oblig_hist.csv
- Filas: 4,804,836 | Columnas: 7
- Variables: nit_enmascarado, num_oblig_enmascarado, fecha_corte, lote, prob_propension, prob_alrt_temprana, prob_auto_cura


## maestra_cuotas_pagos_mes_hist.csv
- Filas: 4,855,035 | Columnas: 13
- Variables: nit_enmascarado, num_oblig_enmascarado, fecha_corte, producto, aplicativo, segmento, valor_cuota_mes, pago_total, fecha_pago_minima, fecha_pago_maxima, porc_pago, marca_pago, ajustes_banco


## oot.csv
- Filas: 112,549 | Columnas: 4
- Variables: nit_enmascarado, num_oblig_orig_enmascarado, num_oblig_enmascarado, fecha_var_rpta_alt


## sample_submission.csv
- Filas: 112,549 | Columnas: 2
- Variables: ID, var_rpta_alt
