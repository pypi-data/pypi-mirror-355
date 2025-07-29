from PIL import Image
import xfox
import discord
import io
from Amisynth.utils import canvas_storage

@xfox.addfunc(xfox.funcs)
async def getCanvas(canvas_id: str = None, *args, **kwargs):
    """
    Devuelve la URL adjunta del canvas si existe, en formato `attachment://archivo.png`.

    Parámetros:
        canvas_id (str): ID del canvas a recuperar.

    Retorna:
        str: URL en formato `attachment://{canvas_id}.png` si el canvas existe.

    Lanza:
        ValueError: Si el ID es nulo, si hay argumentos de más o si no se encuentra el canvas.
    """
    if args:
        raise ValueError(f"❌ La función `$getCanvas` devolvió un error: demasiados argumentos, se esperaban hasta 1, se obtuvieron {len(args) + 1}")

    if not canvas_id:
        raise ValueError("❌ La función `$getCanvas` devolvió un error: argumento vacío o no proporcionado.")


    if canvas_id not in canvas_storage:
        raise ValueError(f"❌ La función `$getCanvas` devolvió un error: no se encontró ningún canvas con ID '{canvas_id}'.")

    return f"attachment://{canvas_id}.png"
