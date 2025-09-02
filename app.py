# app.py
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi import Request
import subprocess
import uuid
import os
import sys
import shutil

app = FastAPI()

# Carpeta global para outputs
os.makedirs("outputs", exist_ok=True)
app.mount("/static", StaticFiles(directory="outputs"), name="static")

# Carpeta fija para el "último" modelo generado
FIXED_OUTPUT_DIR = os.path.join("outputs", "current")
os.makedirs(FIXED_OUTPUT_DIR, exist_ok=True)

@app.post("/reconstruct")
async def reconstruct(
    request: Request,
    file: UploadFile = File(...),
    model_format: str = "obj",
    bake_texture: bool = True
):
    try:
        # Guardar imagen temporal
        temp_filename = f"temp_{uuid.uuid4()}.png"
        with open(temp_filename, "wb") as f:
            f.write(await file.read())

        # Limpiar carpeta de salida antes de generar el nuevo modelo
        if os.path.exists(FIXED_OUTPUT_DIR):
            shutil.rmtree(FIXED_OUTPUT_DIR)
        os.makedirs(FIXED_OUTPUT_DIR, exist_ok=True)

        # Construir comando para run.py
        cmd = [
            sys.executable, "run.py", temp_filename,
            "--output-dir", FIXED_OUTPUT_DIR,
            "--model-save-format", model_format
        ]
        if bake_texture:
            cmd.append("--bake-texture")

        # Ejecutar run.py
        subprocess.run(cmd, check=True)

        # Buscar modelo 3D (mesh.obj)
        model_path = None
        for root, _, files in os.walk(FIXED_OUTPUT_DIR):
            for f in files:
                if f.endswith(f".{model_format}"):
                    model_path = os.path.join(root, f)
                    break

        if not model_path:
            return JSONResponse({"error": "No se generó ningún modelo"}, status_code=500)

        # Buscar textura (texture.png) en la carpeta del job
        texture_path = None
        if bake_texture:
            for root, _, files in os.walk(FIXED_OUTPUT_DIR):
                for f in files:
                    if f == "texture.png":  # aseguramos que sea la textura, no la imagen de entrada
                        texture_path = os.path.join(root, f)
                        break

        # Construir URLs accesibles
        base_url = str(request.base_url)  # cambia a tu IP o dominio al desplegar
        model_rel_path = os.path.relpath(model_path, "outputs")
        model_url = f"{base_url}static/{model_rel_path.replace(os.sep, '/')}"

        texture_url = None
        if texture_path:
            texture_rel_path = os.path.relpath(texture_path, "outputs")
            texture_url = f"{base_url}static/{texture_rel_path.replace(os.sep, '/')}"

        # Borrar la imagen temporal de entrada
        os.remove(temp_filename)

        return JSONResponse({
            "model_url": model_url,
            "texture_url": texture_url if texture_url else None
        })

    except subprocess.CalledProcessError as e:
        return JSONResponse({"error": f"Fallo en run.py: {str(e)}"}, status_code=500)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
