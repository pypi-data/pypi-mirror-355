import xfox
from Amisynth.Functions.storage import split_storage  # Importamos el almacenamiento global

@xfox.addfunc(xfox.funcs)
async def editSplitText(index: str, value: str = None, *args, **kwargs):
    global split_storage

    # Validación de valor nulo
    if value is None:
        raise ValueError(
            "❌ La función `$editSplitText` devolvió un error: se esperaba un entero en la posición 2, pero se obtuvo vacío."
        )

    # Validación de existencia de texto previamente dividido
    if "last_split" not in split_storage:
        raise ValueError(
            "❌ La función `$editSplitText` devolvió un error: aún no se ha dividido ningún texto."
        )

    try:
        # Convertimos el índice a entero (ajustando para comenzar desde 1)
        index = int(index) - 1

        # Verificamos si el índice está dentro del rango válido
        if 0 <= index < len(split_storage["last_split"]):
            split_storage["last_split"][index] = value
        else:
            print(
                "[DEBUG EDITSPLITTEXT] ❌ La función `$editSplitText` devolvió un error: índice fuera de rango."
            )
            return ""
    except ValueError:
        raise ValueError(
            f"❌ La función `$editSplitText` devolvió un error: se esperaba un entero en la posición 1, se obtuvo '{index + 1}'."
        )

    return ""
