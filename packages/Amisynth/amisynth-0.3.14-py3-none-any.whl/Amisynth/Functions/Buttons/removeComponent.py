import xfox
import discord
import Amisynth.utils as utils

@xfox.addfunc(xfox.funcs)
async def removeComponent(custom_id: str, message_id=None, *args, **kwargs):
    """Elimina un componente (botón o select menu) del mensaje por su custom_id.
       Si el custom_id es '-1', elimina todos los componentes."""
    context = utils.ContextAmisynth()

    if args:
        raise ValueError(f"❌ La función `$removeComponent` devolvió un error: demasiados argumentos, se esperaban hasta 1, se obtuvieron {len(args)+2}")
    
    if message_id is None:
        message_id = context.message_id

    message = await context.get_message_from_id(int(message_id))

    if not message:
        raise ValueError(f"❌ La función `$removeComponent` devolvió un error: Nose pudo obtener el Mensaje '{message}'.")
    
    # Obtener la vista actual
    view = discord.ui.View() if not message.components else discord.ui.View.from_message(message)

    # Si el custom_id es "-1", limpiar todos los componentes
    if custom_id == "-1":
        await message.edit(view=discord.ui.View())  # Vista vacía = sin componentes
        return ""

    # Si no, eliminar solo el componente con el custom_id dado
    new_children = [
        item for item in view.children
        if not (
            hasattr(item, "custom_id") and item.custom_id == custom_id
        )
    ]

    # Crear nueva vista con los componentes restantes
    new_view = discord.ui.View()
    for item in new_children:
        new_view.add_item(item)

    await message.edit(view=new_view)
    return ""
