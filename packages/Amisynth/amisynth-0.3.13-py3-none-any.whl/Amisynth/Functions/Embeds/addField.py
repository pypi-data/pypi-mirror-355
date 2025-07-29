import xfox
from Amisynth.utils import embeds  # Asumo que embeds es una lista global

@xfox.addfunc(xfox.funcs)
async def addField(nombre=None, valor=None, inline=False, indice=1, *args, **kwargs):
    if args:
        raise ValueError(f"❌ La función `$addField` devolvió un error: demasiados argumentos, se esperaban hasta 4, se obtuvieron {len(args)+4}")
    
    if nombre is None:
        raise ValueError("❌ La función `$addField` devolvió un error: se esperaba un valor válido en la posición 1, se obtuvo un valor vacío")
    
    if valor is None:
        raise ValueError(f"❌ La función `$addField` devolvió un error: se esperaba un valor en la posición 2, se obtuvo '{indice}'")

    # Validar inline
    if inline is not None:
        if str(inline).lower() not in ["yes", "no", "si", "false", "true"]:
            raise ValueError(f"❌ La función `$addField` devolvió un error: se esperaba un valor booleano en la posición 3, se obtuvo '{inline}'")
        inline = str(inline).lower() in ["yes", "si", "true"]  # Convertir a booleano real

    # Validar índice
    if indice is not None:
        if not str(indice).isdigit():
            raise ValueError(f"❌ La función `$addField` devolvió un error: se esperaba un entero en la posición 4, se obtuvo '{indice}'")
        indice = int(indice)

    # Agregar campo al embed correspondiente
    for i, item in enumerate(embeds):
        if item["index"] == indice:
            if "fields" not in embeds[i]:
                embeds[i]["fields"] = []
            embeds[i]["fields"].append({
                "name": nombre,
                "value": valor,
                "inline": inline
            })
            break
    else:
        # Crear nuevo embed si no existe
        embed = {
            "index": indice,
            "fields": [{
                "name": nombre,
                "value": valor,
                "inline": inline
            }]
        }
        embeds.append(embed)

    return ""
