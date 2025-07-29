import xfox
import discord
import Amisynth.utils as utils

@xfox.addfunc(xfox.funcs)
async def editButton(button_id: str, label: str, style: str, disabled="false", emoji=None, message_id=None, *args, **kwargs):
    """Edita o añade un botón en un mensaje ya enviado."""
    context = utils.ContextAmisynth()

    # Validar argumentos extra
    if args:
        raise ValueError(f"❌ La función `$editButton` devolvió un error: demasiados argumentos, se esperaban hasta 6, se obtuvieron {len(args)+6}")

    # Validar el estilo
    estilos = {
        "primary": discord.ButtonStyle.primary,
        "secondary": discord.ButtonStyle.secondary,
        "success": discord.ButtonStyle.success,
        "danger": discord.ButtonStyle.danger,
        "link": discord.ButtonStyle.link
    }
    if not style.lower() in estilos:
        raise ValueError(f"❌ La función `$editButton` devolvió un error: se esperaba un valor de estilo válido en el argumento 3, se obtuvo '{style}'")

    button_style = estilos.get(style.lower(), discord.ButtonStyle.primary)

    # Validar el parámetro 'disabled'
    if disabled.lower() not in ["true", "false", "yes", "no", "si"]:
        raise ValueError(f"❌ La función `$editButton` devolvió un error: se esperaba un valor booleano en la posición 4, se obtuvo '{disabled}'")
    
    disabled = disabled.lower() in ["true", "yes", "si"]

    # Validar message_id si se proporciona
    if message_id is not None:
        if not str(message_id).isdigit():
            raise ValueError(f"❌ La función `$editButton` devolvió un error: se esperaba un entero en la posición 6, se obtuvo '{message_id}'")
        message_id = int(message_id)
    else:
        message_id = int(context.message_id)

    # Establecer ID o URL del botón
    custom_id = button_id if button_style != discord.ButtonStyle.link else None
    url = button_id if button_style == discord.ButtonStyle.link else None

    # Obtener mensaje
    message = await context.get_message_from_id(message_id)

    # Obtener vista existente o nueva
    view = discord.ui.View() if not message.components else discord.ui.View.from_message(message)

    # Buscar y editar botón existente
    for item in view.children:
        if isinstance(item, discord.ui.Button):
            if (item.custom_id == custom_id and custom_id is not None) or (item.url == url and url is not None):
                item.label = label
                item.style = button_style
                item.disabled = disabled
                item.emoji = emoji
                await message.edit(view=view)
                return ""

    # Si no se encontró, crear y agregar uno nuevo
    new_button = discord.ui.Button(
        label=label,
        custom_id=custom_id,
        style=button_style,
        disabled=disabled,
        emoji=emoji,
        url=url
    )
    view.add_item(new_button)

    await message.edit(view=view)
    return ""
