import xfox
from Amisynth.utils import embeds
from Amisynth.utils import valid_url

@xfox.addfunc(xfox.funcs)
async def thumbnail(url: str, indice: int = 1, *args, **kwargs):
    """
    Guarda un thumbnail en la lista de embeds, con una URL de imagen específica y un índice opcional.
    Si se especifica el índice, se inserta o actualiza en esa posición. Si no, se agrega en la posición 1.
    
    :param url: La URL de la imagen que se desea mostrar como thumbnail.
    :param indice: El índice opcional del embed (posición en la lista).
    """
    if args:
        raise ValueError(f"❌ La función `$thumbnail` devolvió un error: demasiados argumentos, se esperaban hasta 2, se obtuvieron {len(args) + 2}")

    if url is None or url.strip() == "":
        print("[DEBUG THUMBNAIL] La función $thumbnail está vacía")
        raise ValueError("❌ La función `$thumbnail` devolvió un error: se esperaba un valor válido en la posición 1, se obtuvo un valor vacío")

    if not valid_url(url):
        raise ValueError(f"❌ La función `$thumbnail` devolvió un error: se esperaba una URL válida en la posición 1, se obtuvo '{url}'")

    # Asegurar que el índice sea un entero
    if not isinstance(indice, int):
        try:
            indice = int(indice)
        except (ValueError, TypeError):
            raise ValueError(f"❌ La función `$thumbnail` devolvió un error: se esperaba un entero en la posición 2, se obtuvo '{indice}'")

    embed = {
        "thumbnail_icon": url,
        "index": indice
    }

    # Buscar si ya existe un embed con ese índice y actualizar el thumbnail
    for i, item in enumerate(embeds):
        if item.get("index") == indice:
            embeds[i]["thumbnail_icon"] = url
            break
    else:
        embeds.append(embed)

    return ""
