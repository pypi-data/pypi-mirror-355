import xfox
from Amisynth.utils import embeds  # Asegúrate de que 'embeds' sea la lista global que deseas modificar
from Amisynth.utils import valid_url

@xfox.addfunc(xfox.funcs)
async def image(url_imagen: str = None, indice: int = 1, *args, **kwargs):
    """
    Guarda una imagen en la lista de embeds, con una URL de imagen específica y un índice opcional.
    Si se especifica el índice, se inserta o actualiza en esa posición. Si no, se agrega en la posición 1.
    
    :param url_imagen: La URL de la imagen que se desea mostrar.
    :param indice: El índice opcional del embed (posición en la lista).
    """
    if args:
        raise ValueError(f"❌ La función `$image` devolvió un error: demasiados argumentos, se esperaban hasta 2, se obtuvieron {len(args) + 2}")
    
    if url_imagen is None or url_imagen.strip() == "":
        print("[DEBUG IMAGE] La función $image está vacía.")
        raise ValueError("❌ La función `$image` devolvió un error: se esperaba un valor válido en la posición 1, se obtuvo un valor vacío")

    if not valid_url(url_imagen):
        raise ValueError(f"❌ La función `$image` devolvió un error: se esperaba una URL válida en la posición 1, se obtuvo '{url_imagen}'")
    
    # Asegurar que el índice sea un entero
    if not isinstance(indice, int):
        try:
            indice = int(indice)
        except (ValueError, TypeError):
            raise ValueError(f"❌ La función `$image` devolvió un error: se esperaba un entero en la posición 2, se obtuvo '{indice}'")

    embed = {
        "image": url_imagen,
        "index": indice
    }

    # Buscar si ya existe un embed con ese índice y actualizar solo la imagen
    for i, item in enumerate(embeds):
        if item.get("index") == indice:
            embeds[i]["image"] = url_imagen
            break
    else:
        embeds.append(embed)

    return ""
