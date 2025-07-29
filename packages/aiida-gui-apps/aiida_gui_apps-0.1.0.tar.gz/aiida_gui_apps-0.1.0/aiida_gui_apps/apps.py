from __future__ import annotations
import sys
import traceback
import pathlib
from fastapi import APIRouter


def get_plugins():
    import importlib.metadata

    plugins = {}

    try:
        eps = importlib.metadata.entry_points()
        if sys.version_info >= (3, 10):
            eps = eps.select(group="aiida_gui_apps.plugins")
        else:
            eps = eps.get("aiida_gui_apps.plugins", [])
    except Exception:
        print("Failed to get entry points")
        return plugins

    for entry in eps:
        plugin_name = entry.name
        try:
            plugin_module = entry.load()
            plugins[plugin_name] = plugin_module
        except Exception as e:
            print(traceback.format_exc())
            print(f"Failed to load plugin {plugin_name}: {e}")
            continue

    return plugins


plugins = get_plugins()

# static_dir points to plugin1/static
THIS_DIR = pathlib.Path(__file__).parent
static_dir = str(THIS_DIR / "static")

router = APIRouter()


@router.get("/apps")
async def get_apps():
    """Return the daemon status."""
    data = []
    for key, pluin in plugins.items():
        data.append(
            {
                "name": key,
                "title": plugin.get("title", key),
                "version": plugin.get("version", "unknown"),
                "description": plugin.get("description", "No description provided"),
                "logo": plugin.get("logo", None),
            }
        )
    return data


routers = {"apps": router}  # Default router for the main app
sub_apps = {}
for key, plugin in plugins.items():
    if plugin.get("app", False):
        sub_apps[key] = plugin.get("app")

for key, plugin in plugins.items():
    routers.update(plugin.get("routers", {}))

static_dirs = {"apps": static_dir}  # Default static directory for the main app
for key, plugin in plugins.items():
    static_dirs.update(plugin.get("static_dirs", static_dirs))
