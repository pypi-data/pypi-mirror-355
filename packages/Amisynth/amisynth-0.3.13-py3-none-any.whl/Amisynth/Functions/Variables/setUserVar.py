import xfox
import discord
import Amisynth.utils as utils
@xfox.addfunc(xfox.funcs)
async def setUserVar(nombre=None, valor=None, user_id=None, guild_id=None,  *args, **kwargs):
    context = utils.ContextAmisynth()
    if nombre is None:
        raise ValueError("❌ La función `$setUserVar` devolvió un error: El argumento en la posición 1 está vacío o es inválido.")
    
    if value is None:
        raise ValueError("❌ La función `$setUserVar` devolvió un error: El argumento en la posición 2 está vacío o es inválido.")

    if user_id is None:
        user_id = context.author_id

    if guild_id is None:
        guild_id = context.guild_id

    var = utils.VariableManager()

    value = var.set_value("user", key=nombre, value=valor, user_id=user_id, guild_id=guild_id)
    return ""