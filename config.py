"""
Configuración de rutas de datos — este es el ÚNICO archivo que hay que
editar para correr el proyecto con otra ubicación de los datos.

Para reproducir los resultados: coloca las 6 rutas de abajo apuntando a
tus copias de los archivos (por defecto, se asume que están dentro de
data/raw/ con estos mismos nombres — ver README.md), y luego ejecuta los
scripts en el orden que indica el README. Ningún otro archivo del
repositorio necesita cambios: src/data_prep.py, src/train.py y los 3
scripts de notebooks/ importan sus rutas desde aquí.

Si tus archivos viven en otro lugar o con otro nombre, basta con
sobrescribir la(s) línea(s) correspondiente(s) más abajo — por ejemplo:
    RUTA_TRTEST = "/ruta/en/tu/computador/trtest_2024.csv"
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Carpetas por defecto (no necesitan existir de antemano; data/processed/
# y results/ se crean automáticamente al correr los scripts).
DATA_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
DATA_PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
RESULTS_DIR = os.path.join(BASE_DIR, "results")

# --- Rutas de las 6 tablas de entrada ---------------------------------
# (los 3 primeros son los nombres que trae la prueba; edítalos aquí si tu
# copia tiene otro nombre o está en otra carpeta)
RUTA_TRTEST = os.path.join(DATA_RAW_DIR, "trtest.csv")
RUTA_MASTER_CUSTOMER_DATA = os.path.join(DATA_RAW_DIR, "master_customer_data.csv")
RUTA_PROBABILIDAD_OBLIG_HIST = os.path.join(DATA_RAW_DIR, "probabilidad_oblig_hist.csv")
RUTA_MAESTRA_CUOTAS_PAGOS = os.path.join(DATA_RAW_DIR, "maestra_cuotas_pagos_mes_hist.csv")
RUTA_OOT = os.path.join(DATA_RAW_DIR, "oot.csv")
RUTA_SAMPLE_SUBMISSION = os.path.join(DATA_RAW_DIR, "sample_submission.csv")

os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
