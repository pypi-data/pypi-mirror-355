import xfox
import discord
import Amisynth.utils as utils
import asyncio
from typing import Any

@xfox.addfunc(xfox.funcs, "addBotReaction")
async def addBotReaction(*args, **kwargs) -> str:
    """
    Adds reactions to a message for each item in args (expected to be emojis).
    
    Args:
        *args: Emojis (Unicode or custom Discord emojis).
        **kwargs: Must include 'message': the Discord message to react to.
        
    Returns:
        str: Empty string or error message.
    """

    # Validación inicial
    if 'message' not in kwargs:
        print("[DEBUG ADDCMDREACTION] ❌ Falta el parámetro 'message' en kwargs.")
        return ""

    message = kwargs['message']

    if not hasattr(message, 'add_reaction') or not callable(getattr(message, 'add_reaction', None)):
        print(f"[DEBUG ADDCMDREACTION] ❌ El objeto 'message' no es válido o no tiene el método 'add_reaction'. Tipo: {type(message)}")
        return ""

    if not args:
        raise ValueError("❌ La función `$addBotReaction` devolvió un error: Se esperaba al menos un emoji como argumento.")

    # Proceso de reacción
    try:
        for index, emoji in enumerate(args):
            if not emoji or not isinstance(emoji, str) or emoji.strip() == "":
                print(f"[DEBUG ADDCMDREACTION] ⚠️ Emoji inválido en posición {index}: {repr(emoji)} (ignorado)")
                continue

            print(f"[DEBUG ADDCMDREACTION] ✅ Agregando reacción {emoji} al mensaje...")
            await message.add_reaction(emoji)

        print("[DEBUG ADDCMDREACTION] ✅ Todas las reacciones fueron añadidas correctamente.")
    
    except discord.HTTPException as e:
        print(f"[DEBUG ADDCMDREACTION] ❌ HTTPException al agregar reacciones: {e}")
        raise ValueError(f"❌ Error al agregar reacciones: {str(e)}")
    
    except AttributeError as e:
        print(f"[DEBUG ADDCMDREACTION] ❌ AttributeError al acceder a 'add_reaction': {e}")
    
    except Exception as e:
        print(f"[DEBUG ADDCMDREACTION] ❌ Error inesperado: {type(e).__name__} - {e}")
        raise ValueError(f"❌ Error inesperado al agregar reacciones: {str(e)}")

    return ""
