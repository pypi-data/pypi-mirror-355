import xfox
import discord
import Amisynth.utils as utils


@xfox.addfunc(xfox.funcs)
async def kick(user_id: int=None, reason="Ninguna", *args, **kwargs):
    contexto = utils.ContextAmisynth()

    try:
        # Validación de tipo de ID
        if not isinstance(user_id, int):
            raise ValueError("❌ La función $ban devolvió un error: El ID debe ser un número entero válido.")

        # Buscar al miembro
        member = await contexto.obj_guild.fetch_member(user_id)

        # Intentar expulsar al miembro
        await member.kick(reason=reason)

        return ""

    except ValueError as ve:
        # Imprimir el error de valor
        return f"❌ La función $kick devolvió un error: Error de valor: {ve}"

    except discord.NotFound:
        # Si no se encuentra al miembro en el servidor
        raise ValueError(f"❌ La función $kick devolvió un error: No se encontró al usuario en este servidor en `$kick`")

    except discord.Forbidden:
        # Si no se tienen permisos suficientes
         raise ValueError(f"❌ La función $kick devolvió un error: No tengo permisos suficientes para expulsar al usuario en `$kick`.")

    except discord.HTTPException as e:
        # Si ocurre un error HTTP al intentar la acción
        raise ValueError(f"❌ La función $kick devolvió un error: Error de red al expulsar: {e}")

    except Exception as e:
        # Para cualquier otro error inesperado
        raise ValueError(e)
