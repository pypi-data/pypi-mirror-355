import xfox
from Amisynth.utils import embeds, valid_url  # Asegúrate de que 'embeds' sea la lista global que estás usando

@xfox.addfunc(xfox.funcs)
async def footerIcon(url: str, indice: int = 1, *args, **kwargs):
    """
    Guarda un footer con ícono en la lista de embeds, con una URL de ícono y un índice opcional.
    Si se especifica el índice, se inserta o actualiza en esa posición. Si no, se agrega en la posición 1.

    :param url: La URL del ícono que se quiere mostrar en el footer.
    :param indice: El índice opcional del embed (posición en la lista).
    """
    if args:
        raise ValueError(f"❌ La función `$footerIcon` devolvió un error: demasiados argumentos, se esperaban hasta 2, se obtuvieron {len(args) + 2}")

    if url is None or url.strip() == "":
        print("[DEBUG FOOTERICON] La función $footerIcon está vacía.")
        raise ValueError("❌ La función `$footerIcon` devolvió un error: se esperaba un valor válido en la posición 1, se obtuvo un valor vacío")

    if not valid_url(url):
        raise ValueError(f"❌ La función `$footerIcon` devolvió un error: se esperaba una URL en la posición 1, se obtuvo '{url}'")

    # Asegurar que el índice sea un entero
    if not isinstance(indice, int):
        try:
            indice = int(indice)
        except (ValueError, TypeError):
            raise ValueError(f"❌ La función `$footerIcon` devolvió un error: se esperaba un entero en la posición 2, se obtuvo '{indice}'")

    embed = {
        "footer_icon": url,
        "index": indice
    }

    # Buscar si ya existe un embed con ese índice y actualizar solo el footer_icon
    for i, item in enumerate(embeds):
        if item.get("index") == indice:
            embeds[i]["footer_icon"] = url
            break
    else:
        embeds.append(embed)

    return ""
