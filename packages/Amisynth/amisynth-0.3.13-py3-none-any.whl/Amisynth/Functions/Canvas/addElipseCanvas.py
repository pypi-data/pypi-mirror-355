import xfox
from PIL import ImageDraw
from Amisynth.utils import canvas_storage

@xfox.addfunc(xfox.funcs)
async def addElipseCanvas(canvas_id: str, x: int, y: int, ancho: int, alto: int, color: str = "#FFFFFF", grosor: int = 1, *args, **kwargs):
    """
    Dibuja una elipse de solo borde (contorno) en el canvas especificado.

    Parámetros:
        canvas_id (str): ID del canvas donde se dibujará.
        x (int): Coordenada X inicial (esquina superior izquierda del marco).
        y (int): Coordenada Y inicial (esquina superior izquierda del marco).
        ancho (int): Ancho de la elipse.
        alto (int): Alto de la elipse.
        color (str): Color del borde de la elipse.
        grosor (int): Grosor del contorno de la elipse (por defecto 1).
    """

    if args:
        raise ValueError(f"❌ La función `$addElipseCanvas` devolvió un error: demasiados argumentos, se esperaban hasta 7, se obtuvieron {len(args)+7}")
    
    if not str(x).isdigit():
        raise ValueError(f"❌ La función `$addElipseCanvas` devolvió un error: se esperaba un entero en la posición 2, se obtuvo '{x}'")

    if not str(y).isdigit():
        raise ValueError(f"❌ La función `$addElipseCanvas` devolvió un error: se esperaba un entero en la posición 3, se obtuvo '{y}'")
    
    if not str(ancho).isdigit():
        raise ValueError(f"❌ La función `$addElipseCanvas` devolvió un error: se esperaba un entero en la posición 4, se obtuvo '{ancho}'")
    
    if not str(alto).isdigit():
        raise ValueError(f"❌ La función `$addElipseCanvas` devolvió un error: se esperaba un entero en la posición 5, se obtuvo '{alto}'")
    
    if not str(grosor).isdigit():
        raise ValueError(f"❌ La función `$addElipseCanvas` devolvió un error: se esperaba un entero en la posición 7, se obtuvo '{grosor}'")

    try:
        # Obtener el canvas
        canvas = canvas_storage.get(canvas_id)
        if canvas is None:
            raise ValueError(f"❌ La función `$addElipseCanvas` devolvió un error: No se encontró un canvas con nombre '{canvas_id}'.")

        # Crear objeto de dibujo
        draw = ImageDraw.Draw(canvas)

        # Coordenadas del marco de la elipse
        bbox = [(x, y), (x + ancho, y + alto)]

        # Dibujar contorno de elipse
        for i in range(grosor):  # Dibuja múltiples elipses concéntricas para simular grosor
            draw.ellipse(
                [(x + i, y + i), (x + ancho - i, y + alto - i)],
                outline=color
            )

        # Guardar el canvas actualizado
        canvas_storage[canvas_id] = canvas

        print(f"[DEBUG ELIPSECANVAS] Elipse de borde agregada al canvas: {canvas_id}")
        return ""

    except Exception as e:
        raise ValueError(f"❌ La función `$addElipseCanvas` devolvió un error: Error al dibujar elipse: {str(e)}")
