from .apps import routers, static_dirs, sub_apps

__version__ = "0.1.0"


plugin = {
    "sub_apps": sub_apps,
    "routers": routers,
    "name": "Apps",
    "static_dirs": static_dirs,
}
