import xfox
import discord
from Amisynth.utils import buttons
import Amisynth.utils as utils

# Contador de fila global
row_counter = 0  

@xfox.addfunc(xfox.funcs)
async def addButton(new_row: str, button_id: str, label: str, style: str, disabled="false", emoji=None, message_id=None, *args, **kwargs):
    """Crea múltiples botones interactivos y devuelve una lista de objetos de botones creados."""
    context = utils.ContextAmisynth()
    
    global row_counter  # Para modificar el contador de fila

    # Estilos disponibles
    if args:
        raise ValueError(f"❌ La función `$addButton` devolvió un error: demasiados argumentos, se esperaban hasta 7, se obtuvieron {len(args)+7}")
    
    elif not new_row.lower() in ["true", "false", "yes", "no", "si"]:
        raise ValueError(f"❌ La función `$addButton` devolvió un error: se esperaba un valor booleano en la posición 1, se obtuvo '{new_row}'")
    
    elif not style.lower() in ["primary", "secondary", "success", "danger", "link"]:
        raise ValueError(f"❌ La función `$addButton` devolvió un error: se esperaba un valor de stilo válido en el argumento 4, se obtuvo '{style}'")
    
    elif not disabled.lower() in ["true", "false", "yes", "no", "si"]:
        raise ValueError(f"❌ La función `$addButton` devolvió un error: se esperaba un valor booleano en la posición 5, se obtuvo '{new_row}'")
    
    elif not message_id is None:
        if not message_id.isdigit():
            raise ValueError(f"❌ La función `$addButton` devolvió un error: se esperaba un entero en la posición 7, se obtuvo '{message_id}'")

    estilos = {
        "primary": discord.ButtonStyle.primary,
        "secondary": discord.ButtonStyle.secondary,
        "success": discord.ButtonStyle.success,
        "danger": discord.ButtonStyle.danger,
        "link": discord.ButtonStyle.link
    }
    
    button_style = estilos.get(style, discord.ButtonStyle.primary)

    # Validar el parámetro 'disabled'
    if disabled.lower() in ["true", "false", "yes", "no", "si"]:
        if disabled == "true" or disabled == "yes" or disabled == "si":
            disabled = True
        else:
            disabled = False



    # Validar si es un botón de tipo enlace
    custom_id = button_id if button_style != discord.ButtonStyle.link else None
    url = button_id if button_style == discord.ButtonStyle.link else None

    # Manejo de la fila (row)
    if new_row.lower() == "true" or new_row.lower() == "yes" or new_row.lower() == "si":
        row_counter += 1
    elif new_row.lower() == "re":
        row_counter = 0  

    button = discord.ui.Button(
        label=label,
        custom_id=custom_id,
        style=button_style,
        emoji=emoji,
        disabled=disabled,
        url=url,
        row=row_counter
    )

    if message_id is None:
        buttons.append(button)  # Si no hay mensaje, guardar el botón en la lista
    else:

        message = await context.get_message_from_id(int(message_id))


        # Recuperar o crear una vista nueva
        view = discord.ui.View() if not message.components else discord.ui.View.from_message(message)
        view.add_item(button)  # Agregar el botón a la vista

        await message.edit(view=view)  # Editar el mensaje con la nueva vista

    return ""
