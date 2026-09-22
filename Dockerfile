# Imagen de scoring para el modelo de propensión a aceptación de
# opciones de pago (Parte 1) -- ver docs/mlops_parte1.md, sección
# "Productización".
#
# No empaqueta datos ni modelo ya entrenado: eso viola buenas prácticas de
# tamaño/seguridad de imagen. Se montan como volúmenes en tiempo de
# ejecución (aquí, para reproducir localmente); en producción real, los
# datos vendrían del feature store y el modelo del MLflow Model Registry
# al arrancar el contenedor, no de un volumen local.
#
# Construir:
#   docker build -t prueba-bancolombia-scoring .
#
# Correr (monta tus datos de entrada y las carpetas de salida; ver
# config.py si tus archivos tienen otra ruta/nombre):
#   docker run --rm \
#     -v "$(pwd)/data/raw:/app/data/raw:ro" \
#     -v "$(pwd)/data/processed:/app/data/processed" \
#     -v "$(pwd)/results:/app/results" \
#     prueba-bancolombia-scoring

FROM python:3.11-slim

WORKDIR /app

# Solo las dependencias mínimas de scoring (ver docker/requirements.txt) --
# no las de EDA/notebooks/pruebas, que no tienen por qué viajar en la
# imagen de producción.
COPY docker/requirements.txt ./docker/requirements.txt
RUN pip install --no-cache-dir -r docker/requirements.txt

COPY config.py .
COPY src/ ./src/

# data/ y results/ se montan como volúmenes en tiempo de ejecución (ver
# comentario arriba); se crean vacías aquí solo para que el pipeline no
# falle por carpetas inexistentes si se corre sin montar nada.
RUN mkdir -p data/raw data/processed results

CMD ["sh", "-c", "python3 src/data_prep.py && python3 src/train.py"]
