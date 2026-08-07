async def safe_delete(msg):
    try:
        await msg.delete()
    except Exception:
        pass


async def safe_edit(msg, text):
    try:
        await msg.edit_text(text)
    except Exception:
        pass
