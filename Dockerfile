# Imagen base liviana con Python
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYOPENGL_PLATFORM=egl

# Dependencias de compilación
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    cmake \
    libgl1 \
    libglib2.0-0 \
    libosmesa6-dev \
    libglu1-mesa \
    libgl1-mesa-dri \
    libegl1 \
    libgles2 \
    mesa-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Actualizar pip y herramientas
RUN pip install --upgrade pip setuptools wheel

# Instalar torch y numpy primero (para que torchmcubes compile bien)
RUN pip install --no-cache-dir numpy \
    && pip install typing-extensions==4.12.2 \
    && pip install torch==2.8.0 torchvision==0.23.0 --index-url https://download.pytorch.org/whl/cpu

# Instalar el resto de dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Descargar modelo de rembg al construir la imagen
RUN python -c "import rembg; rembg.new_session()"

COPY . .

EXPOSE 8080

CMD ["python", "app.py"]
