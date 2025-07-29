import xfox
from Amisynth.utils import embeds  # Asumo que embeds es una lista global que estás usando

@xfox.addfunc(xfox.funcs)
async def author(texto: str = None, indice:str = 1, *args, **kwargs):
    """
    Guarda un autor en la lista de embeds, con el texto del autor y un índice opcional.
    Si se especifica el índice, se inserta o actualiza en esa posición. Si no, se agrega en la posición 1.
    """

    if args:
        raise ValueError(f"❌ La función `$author` devolvió un error: demasiados argumentos, se esperaban hasta 2, se obtuvieron {len(args) + 2}")

    if texto is None:
        raise ValueError("❌ La función `$author` devolvió un error: se esperaba un valor en la posición 1 (texto del autor), se obtuvo un valor vacío")

    if indice is not None and not str(indice).isdigit():
        raise ValueError(f"❌ La función `$author` devolvió un error: se esperaba un número entero en la posición 2 (índice), se obtuvo '{indice}'")
    
    indice = int(indice)  # Asegurarse de que sea entero

    # Crear o actualizar el embed con el texto del autor
    for i, item in enumerate(embeds):
        if item.get("index") == indice:
            embeds[i]["author"] = texto  # Solo actualizar el campo "author"
            break
    else:
        embeds.append({
            "author": texto,
            "index": indice
        })

    return ""
