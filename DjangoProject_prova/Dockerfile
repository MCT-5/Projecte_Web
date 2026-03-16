# Usamos una imagen oficial y ligera de Python
FROM python:3.12-slim

# Variables de entorno recomendadas por 12-factor (sin logs cacheados y sin archivos .pyc)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalamos uv
RUN pip install uv

# Copiamos el archivo de dependencias (necesitarás crear un requirements.txt usando uv)
COPY requirements.txt /app/

# Instalamos las dependencias del proyecto usando uv para mayor velocidad
RUN uv pip install --system -r requirements.txt

# Copiamos el resto del código del proyecto al contenedor
COPY . /app/

# Exponemos el puerto en el que correrá Django
EXPOSE 8000

# Comando por defecto para arrancar el servidor en desarrollo
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]