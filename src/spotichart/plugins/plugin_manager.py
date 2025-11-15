from .plugin_interface import IPlugin

class PluginManager:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if PluginManager._instance is not None:
            raise Exception("This class is a singleton!")
        self._plugins = {}

    def register_plugin(self, plugin: IPlugin) -> bool:
        name = plugin.metadata.name
        if name in self._plugins:
            return False
        self._plugins[name] = plugin
        return True

    def get_plugin(self, name: str) -> IPlugin:
        return self._plugins.get(name)

    def initialize_all(self):
        for plugin in self._plugins.values():
            plugin.initialize()

    def shutdown_all(self):
        for plugin in self._plugins.values():
            plugin.shutdown()

    def list_plugins(self):
        return list(self._plugins.keys())
