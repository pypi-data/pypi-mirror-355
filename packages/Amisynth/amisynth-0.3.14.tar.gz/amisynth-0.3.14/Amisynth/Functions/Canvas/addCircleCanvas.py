import xfox
from PIL import ImageDraw
from Amisynth.utils import canvas_storage
from Amisynth.utils import valid_hex

@xfox.addfunc(xfox.funcs)
async def addCircleCanvas(canvas_id: str=None, x=None, y=None, radio=None, color="#FFFFFF", *args, **kwargs):
    """
    Dibuja un círculo en el canvas con el color y radio especificado.

    Parámetros:
        canvas_id (str): ID del canvas destino.
        x (int): Coordenada X del centro del círculo.
        y (int): Coordenada Y del centro del círculo.
        radio (int): Radio del círculo.
        color (str): Color del círculo en formato hexadecimal (por defecto blanco).
    """

    if args:
        raise ValueError(f"❌ La función `$addCircleCanvas` devolvió un error: demasiados argumentos, se esperaban hasta 5, se obtuvieron {len(args)+5}")
    
    if not x.isdigit():
       raise ValueError(f"❌ La función `$addCircleCanvas` devolvió un error: se esperaba un entero en la posición 2, se obtuvo '{x}'")
    else:
        int(x)
    
    if not y.isdigit():
       raise ValueError(f"❌ La función `$addCircleCanvas` devolvió un error: se esperaba un entero en la posición 3, se obtuvo '{y}'")
    else:
        int(y)
    
    if not radio.isdigit():
       raise ValueError(f"❌ La función `$addCircleCanvas` devolvió un error: se esperaba un entero en la posición 4, se obtuvo '{radio}'")
    else:
        int(radio)
    
    if not valid_hex(color):
        raise ValueError(f"❌ La función `$addCircleCanvas` devolvió un error: se esperaba un color hexadecimal en la posición 5, se obtuvo '{color}'")
    


    try:
        # Obtener canvas
        canvas = canvas_storage.get(canvas_id)
        if canvas is None:
            raise ValueError(f"❌ La función `$addCircleCanvas` devolvió un error: No se encontró un canvas con nombre '{canvas_id}'.")

        # Crear objeto de dibujo
        draw = ImageDraw.Draw(canvas)

        # Coordenadas del círculo
        left_up = (x - radio, y - radio)
        right_down = (x + radio, y + radio)

        # Dibujar círculo relleno
        draw.ellipse([left_up, right_down], fill=color)

        # Guardar canvas actualizado
        canvas_storage[canvas_id] = canvas

        print(f"[DEBUG CIRCLECANVAS] Círculo agregado al canvas: {canvas_id}")
        return ""

    except Exception as e:
        raise ValueError(f"❌ La función `$addCircleCanvas` devolvió un error: Error al dibujar círculo: {str(e)}")
