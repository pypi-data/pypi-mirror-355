import xfox
from Amisynth.utils import options_slash


@xfox.addfunc(xfox.funcs)
async def addSlashChoiceOption(nombre_opcion: str, name_choice: str, value_choice: str, *args, **kwargs):
    """
    Agrega un choice a una opción existente.

    Uso:
        $add_choice[mensaje;josue;Josuehee]
    """
    if nombre_opcion is None:
        raise ValueError("❌ La función `$addSlashChoiceOption` devolvió un error: El argumento en la posición 1 está vacío o es inválido.")
    
    elif name_choice is None:
        raise ValueError("❌ La función `$addSlashChoiceOption` devolvió un error:  El argumento en la posición 2 está vacío o es inválido.")
    
    elif value_choice is None:
        raise ValueError("❌ La función `$addSlashChoiceOption` devolvió un error:  El argumento en la posición 3 está vacío o es inválido")
    


    for opcion in options_slash:
        if opcion["name_option"] == nombre_opcion:
            opcion.setdefault("choices", []).append({
                "name_choice": name_choice,
                "value_choice": value_choice
            })
            print("[DEBUG ADDCHOICEOPTION] Choice Agregado correctamente.")
            return ""
    print("[SLASH] No se encontró una opción con nombre '{nombre_opcion}' para agregar choice.")
    raise ValueError(f"❌ La función `$addSlashChoiceOption` devolvió un error: No se encontró una opción con nombre '{nombre_opcion}' para agregar choice.")