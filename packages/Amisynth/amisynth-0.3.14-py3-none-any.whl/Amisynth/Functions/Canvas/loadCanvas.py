from PIL import Image
import Amisynth.utils as utils
from Amisynth.utils import canvas_storage
import xfox
import os
import requests
from io import BytesIO

@xfox.addfunc(xfox.funcs)
async def loadCanvas(canvas_id: str=None, path: str=None, *args, **kwargs):
    """
    Carga una imagen desde una ruta local o URL y la guarda en el canvas con el ID proporcionado.
    """
    try:
        if canvas_id is None:
            raise ValueError(f"❌ La función `$loadCanvas` devolvió un error: parámetro 'canvas_id' vacío o inválido.")
        if path is None:
            raise ValueError(f"❌ La función `$loadCanvas` devolvió un error: parámetro 'path' vacío o inválido.")

        # Cargar imagen desde URL
        if path.startswith("http://") or path.startswith("https://"):
            response = requests.get(path)
            if response.status_code != 200:
                raise ValueError(f"❌ La función `$loadCanvas` devolvió un error: no se pudo acceder a la URL '{path}' (status {response.status_code}).")
            img = Image.open(BytesIO(response.content)).convert("RGBA")
        else:
            # Ruta local
            if not os.path.exists(path):
                raise ValueError(f"❌ La función `$loadCanvas` devolvió un error: archivo no encontrado en la ruta '{path}'.")
            img = Image.open(path).convert("RGBA")

        # Guardar imagen en el canvas_storage
        canvas_storage[canvas_id] = img
        print(f"[DEBUG LOADCANVAS] Imagen cargada correctamente en canvas '{canvas_id}'.")
        return ""

    except Exception as e:
        return f"❌ La función `$loadCanvas` devolvió un error inesperado: {str(e)}"
