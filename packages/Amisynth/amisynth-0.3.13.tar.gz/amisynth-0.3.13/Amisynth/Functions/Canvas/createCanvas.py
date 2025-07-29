from PIL import Image
import Amisynth.utils as utils
from Amisynth.utils import canvas_storage
import xfox
import re

@xfox.addfunc(xfox.funcs)
async def createCanvas(canvas_id: str, width: int, height: int, color: str = "#000000", *args, **kwargs):
    """
    Crea un canvas con un ID, ancho y alto específicos y un color de fondo dado (HEX o RGB).
    Si no se proporciona color, el fondo será negro.
    """

    if args:
        raise ValueError(f"❌ La función `$createCanvas` devolvió un error: demasiados argumentos, se esperaban hasta 4, se obtuvieron {len(args) + 4}")

    if not canvas_id:
        raise ValueError("❌ La función `$createCanvas` devolvió un error: el parámetro 'canvas_id' es obligatorio.")

    if not str(width).isdigit():
        raise ValueError(f"❌ La función `$createCanvas` devolvió un error: se esperaba un entero positivo en la posición 2, se obtuvo '{width}'")

    if not str(height).isdigit():
        raise ValueError(f"❌ La función `$createCanvas` devolvió un error: se esperaba un entero positivo en la posición 3, se obtuvo '{height}'")

    width = int(width)
    height = int(height)

    if width <= 0 or height <= 0:
        raise ValueError("❌ La función `$createCanvas` devolvió un error: el ancho y alto deben ser enteros positivos.")

    if not isinstance(color, str):
        raise ValueError("❌ La función `$createCanvas` devolvió un error: el parámetro 'color' debe ser una cadena de texto.")

    # Función para convertir HEX a RGB
    def hex_to_rgb(hex_color: str):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    # Validar y convertir color
    if re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', color):
        try:
            color = hex_to_rgb(color)
        except Exception:
            raise ValueError("❌ La función `$createCanvas` devolvió un error: color HEX inválido.")
    elif color.startswith('rgb(') and color.endswith(')'):
        try:
            color = tuple(map(int, color[4:-1].split(',')))
            if len(color) != 3 or not all(0 <= c <= 255 for c in color):
                raise ValueError()
        except Exception:
            raise ValueError("❌ La función `$createCanvas` devolvió un error: color RGB inválido. Usa el formato 'rgb(255,255,255)'.")
    else:
        raise ValueError("❌ La función `$createCanvas` devolvió un error: color inválido. Usa formato HEX ('#FFFFFF') o RGB ('rgb(255,255,255)').")

    # Crear el canvas
    try:
        canvas_storage[canvas_id] = Image.new("RGBA", (width, height), color)
    except Exception as e:
        raise ValueError(f"❌ La función `$createCanvas` devolvió un error al crear el canvas: {e}")

    print(f"[DEBUG CREATECANVAS] Canvas creado con color: {color}")
    return ""
