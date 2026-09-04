import API


# ContextMenu opens the menu itself, and cannot tell an entry that is missing from one that never
# arrived - both come back False
def context_menu(serial, texts, timeout):
    for text in texts:
        if API.ContextMenu(serial, text, timeout):
            return True

    return False
