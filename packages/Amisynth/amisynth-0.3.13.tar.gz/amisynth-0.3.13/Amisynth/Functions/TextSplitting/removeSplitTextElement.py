import xfox
from Amisynth.Functions.storage import split_storage  # Importamos el almacenamiento global
from datetime import datetime

ahora = datetime.now()

# Formatear la fecha y hora
formato = ahora.strftime("%H:%M:%S %d/%m/%Y")



@xfox.addfunc(xfox.funcs)
async def removeSplitTextElement(index: str, *args, **kwargs):
    global split_storage
    if "last_split" not in split_storage:
        print(f"{formato}     [DEBUG MENSAJE $removeSplitTextElement] Aún no se ha dividido ningún texto.")

        return ""
    
    try:
        index = int(index) - 1  # Ajustar para que empiece desde 1
        if 0 <= index < len(split_storage["last_split"]):
            del split_storage["last_split"][index]
        else:
            print(f"{formato}     [DEBUG MENSAJE $removeSplitTextElement] Indice Fuera de rango")
            raise ValueError(f"❌ La función `$removeSplitTextElement` devolvió un error: Indice Fuera de rango, obtuvo '{index}'")
        

    except ValueError:
        raise ValueError("❌ La función `$removeSplitTextElement` devolvió un error: Invalid index: must be an integer")
    
    return ""
