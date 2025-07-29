import xfox
import discord
import Amisynth.utils as utils


@xfox.addfunc(xfox.funcs)
async def ban(user_id: int, reason="Sin razón específica", *args, **kwargs):
    contexto = utils.ContextAmisynth()

    try:
        # Validación del ID
        if not isinstance(user_id, int):
            raise ValueError("❌ La función `$ban` devolvió un error: El ID debe ser un número entero válido.")

        # Buscar al miembro
        member = await contexto.obj_guild.fetch_member(user_id)

        if member is None:
            raise discord.NotFound("❌ La función $ban devolvió un error: No se encontró al usuario en el servidor.")

        # Banear al miembro
        await member.ban(reason=reason)

        return ""

    except ValueError as ve:
        raise ValueError(f"❌ La función $ban devolvió un error: Error de valor '{ve}'")

    except discord.NotFound:
        raise ValueError(f"❌ La función $ban devolvió un error:  No se encontró al usuario en este servidor.")

    except discord.Forbidden:
        raise ValueError(f"❌ La función $ban devolvió un error:  No tengo permisos suficientes para banear al usuario.")

    except discord.HTTPException as e:
        raise ValueError(f"❌ La función $ban devolvió un error:  Error de red al banear: {e}")

    except Exception as e:
        raise ValueError(f"❌ La función $ban devolvió un error:  Ocurrió un error inesperado: {e}")
