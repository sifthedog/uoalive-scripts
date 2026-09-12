import API

# TazUO's working directory is its own folder, and the scripts live in this subfolder of it
SCRIPTS_FOLDER = "LegionScripts"


# A bare name lands in TazUO's working directory; beside the script is where anyone looks for it.
# A name with a folder in it, relative or absolute, is left as written.
def beside_script(name):
    if not name or "/" in name or "\\" in name:
        return name

    script = getattr(API, "ScriptPath", None) or ""
    cut = max(script.rfind("/"), script.rfind("\\"))

    # A client that does not say where the script is still runs it out of the standard folder
    if cut < 0:
        return SCRIPTS_FOLDER + "/" + name

    return script[:cut + 1] + name
