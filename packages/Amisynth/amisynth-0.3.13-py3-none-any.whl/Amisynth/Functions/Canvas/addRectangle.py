import xfox
from PIL import ImageDraw
from Amisynth.utils import canvas_storage

@xfox.addfunc(xfox.funcs)
async def addRectangleCanvas(
    canvas_id: str,
    x: int,
    y: int,
    ancho: int,
    alto: int,
    color: str = "#FFFFFF",
    *args, **kwargs
):
    """
    Dibuja un rectángulo relleno en el canvas especificado.

    Parámetros:
        canvas_id (str): ID del canvas donde se dibujará.
        x (int): Coordenada X inicial (esquina superior izquierda).
        y (int): Coordenada Y inicial (esquina superior izquierda).
        ancho (int): Ancho del rectángulo.
        alto (int): Alto del rectángulo.
        color (str): Color del rectángulo en formato hexadecimal (por defecto blanco).
    """

    if args:
        raise ValueError(f"❌ La función `$addRectangleCanvas` devolvió un error: demasiados argumentos, se esperaban hasta 6, se obtuvieron {len(args) + 6}")

    if not str(x).isdigit():
        raise ValueError(f"❌ La función `$addRectangleCanvas` devolvió un error: se esperaba un entero en la posición 2, se obtuvo '{x}'")

    if not str(y).isdigit():
        raise ValueError(f"❌ La función `$addRectangleCanvas` devolvió un error: se esperaba un entero en la posición 3, se obtuvo '{y}'")

    if not str(ancho).isdigit():
        raise ValueError(f"❌ La función `$addRectangleCanvas` devolvió un error: se esperaba un entero en la posición 4, se obtuvo '{ancho}'")

    if not str(alto).isdigit():
        raise ValueError(f"❌ La función `$addRectangleCanvas` devolvió un error: se esperaba un entero en la posición 5, se obtuvo '{alto}'")

    try:
        # Obtener el canvas
        canvas = canvas_storage.get(canvas_id)
        if canvas is None:
            raise ValueError(f"❌ La función `$addRectangleCanvas` devolvió un error: No se encontró un canvas con nombre '{canvas_id}'.")

        # Crear objeto de dibujo
        draw = ImageDraw.Draw(canvas)

        # Coordenadas del rectángulo
        rect_coords = [(x, y), (x + ancho, y + alto)]

        # Dibujar rectángulo relleno
        draw.rectangle(rect_coords, fill=color)

        # Guardar canvas actualizado
        canvas_storage[canvas_id] = canvas

        print(f"[DEBUG RECTCANVAS] Rectángulo agregado al canvas: {canvas_id}")
        return ""

    except Exception as e:
        raise ValueError(f"❌ La función `$addRectangleCanvas` devolvió un error: Error al dibujar rectángulo: {str(e)}")
