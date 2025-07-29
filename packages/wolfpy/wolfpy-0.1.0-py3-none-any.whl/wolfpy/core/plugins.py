"""
WolfPy Plugin System

Provides plugin discovery, loading, and management using entry_points.
Supports plugin lifecycle management, dependency resolution, and auto-discovery.
"""

import importlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field

try:
    import pkg_resources
    PKG_RESOURCES_AVAILABLE = True
except ImportError:
    PKG_RESOURCES_AVAILABLE = False

try:
    from importlib.metadata import entry_points
    IMPORTLIB_METADATA_AVAILABLE = True
except ImportError:
    IMPORTLIB_METADATA_AVAILABLE = False


logger = logging.getLogger(__name__)


@dataclass
class PluginInfo:
    """Information about a plugin."""
    name: str
    module_name: str
    entry_point: str
    version: str = "unknown"
    description: str = ""
    author: str = ""
    dependencies: List[str] = field(default_factory=list)
    loaded: bool = False
    instance: Optional[Any] = None
    setup_func: Optional[Callable] = None
    teardown_func: Optional[Callable] = None


class PluginManager:
    """
    Plugin manager for WolfPy applications.
    
    Features:
    - Auto-discovery using entry_points
    - Plugin lifecycle management (setup/teardown)
    - Dependency resolution
    - Plugin isolation and error handling
    - Hot reloading support
    """
    
    def __init__(self, app=None, entry_point_group: str = "wolfpy.plugins"):
        """
        Initialize plugin manager.
        
        Args:
            app: WolfPy application instance
            entry_point_group: Entry point group name for plugin discovery
        """
        self.app = app
        self.entry_point_group = entry_point_group
        self.plugins: Dict[str, PluginInfo] = {}
        self.load_order: List[str] = []
        self.hooks: Dict[str, List[Callable]] = {}
        
        # Plugin directories for local plugins
        self.plugin_dirs = [
            Path("plugins"),
            Path("src/plugins"),
            Path.cwd() / "plugins"
        ]
    
    def discover_plugins(self) -> List[PluginInfo]:
        """
        Discover available plugins using entry_points.
        
        Returns:
            List of discovered plugin information
        """
        discovered = []
        
        # Method 1: Use importlib.metadata (Python 3.8+)
        if IMPORTLIB_METADATA_AVAILABLE:
            try:
                eps = entry_points()
                if hasattr(eps, 'select'):
                    # Python 3.10+ style
                    plugin_eps = eps.select(group=self.entry_point_group)
                else:
                    # Python 3.8-3.9 style
                    plugin_eps = eps.get(self.entry_point_group, [])
                
                for ep in plugin_eps:
                    plugin_info = PluginInfo(
                        name=ep.name,
                        module_name=ep.value.split(':')[0],
                        entry_point=ep.value,
                        version=getattr(ep.dist, 'version', 'unknown') if hasattr(ep, 'dist') else 'unknown'
                    )
                    discovered.append(plugin_info)
                    logger.info(f"Discovered plugin: {plugin_info.name}")
                    
            except Exception as e:
                logger.warning(f"Error discovering plugins with importlib.metadata: {e}")
        
        # Method 2: Fallback to pkg_resources
        elif PKG_RESOURCES_AVAILABLE:
            try:
                for ep in pkg_resources.iter_entry_points(self.entry_point_group):
                    plugin_info = PluginInfo(
                        name=ep.name,
                        module_name=ep.module_name,
                        entry_point=f"{ep.module_name}:{ep.attrs[0]}" if ep.attrs else ep.module_name,
                        version=ep.dist.version if ep.dist else 'unknown'
                    )
                    discovered.append(plugin_info)
                    logger.info(f"Discovered plugin: {plugin_info.name}")
                    
            except Exception as e:
                logger.warning(f"Error discovering plugins with pkg_resources: {e}")
        
        # Method 3: Local plugin discovery
        discovered.extend(self.discover_local_plugins())
        
        return discovered
    
    def discover_local_plugins(self) -> List[PluginInfo]:
        """Discover local plugins in plugin directories."""
        discovered = []
        
        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                continue
                
            for item in plugin_dir.iterdir():
                if item.is_dir() and (item / "__init__.py").exists():
                    try:
                        plugin_info = PluginInfo(
                            name=item.name,
                            module_name=f"plugins.{item.name}",
                            entry_point=f"plugins.{item.name}:setup",
                            version="local"
                        )
                        
                        # Try to read plugin metadata
                        self._read_plugin_metadata(plugin_info, item)
                        
                        discovered.append(plugin_info)
                        logger.info(f"Discovered local plugin: {plugin_info.name}")
                        
                    except Exception as e:
                        logger.warning(f"Error discovering local plugin {item.name}: {e}")
        
        return discovered
    
    def _read_plugin_metadata(self, plugin_info: PluginInfo, plugin_dir: Path):
        """Read plugin metadata from plugin directory."""
        # Try to read from __init__.py
        init_file = plugin_dir / "__init__.py"
        if init_file.exists():
            try:
                with open(init_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract docstring as description
                import ast
                tree = ast.parse(content)
                if (tree.body and isinstance(tree.body[0], ast.Expr) 
                    and isinstance(tree.body[0].value, ast.Str)):
                    plugin_info.description = tree.body[0].value.s.strip()
                
            except Exception:
                pass
        
        # Try to read from plugin.toml or setup.cfg
        for config_file in [plugin_dir / "plugin.toml", plugin_dir / "setup.cfg"]:
            if config_file.exists():
                try:
                    # Simple parsing - could be enhanced with proper TOML/INI parsing
                    with open(config_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extract basic metadata (simplified)
                    for line in content.split('\n'):
                        if 'version' in line.lower() and '=' in line:
                            plugin_info.version = line.split('=')[1].strip().strip('"\'')
                        elif 'description' in line.lower() and '=' in line:
                            plugin_info.description = line.split('=')[1].strip().strip('"\'')
                        elif 'author' in line.lower() and '=' in line:
                            plugin_info.author = line.split('=')[1].strip().strip('"\'')
                            
                except Exception:
                    pass
    
    def load_plugin(self, plugin_name: str) -> bool:
        """
        Load a specific plugin.
        
        Args:
            plugin_name: Name of the plugin to load
            
        Returns:
            True if plugin loaded successfully, False otherwise
        """
        if plugin_name in self.plugins and self.plugins[plugin_name].loaded:
            logger.info(f"Plugin {plugin_name} already loaded")
            return True
        
        # Discover plugins if not already done
        if plugin_name not in self.plugins:
            discovered = self.discover_plugins()
            for plugin_info in discovered:
                self.plugins[plugin_info.name] = plugin_info
        
        if plugin_name not in self.plugins:
            logger.error(f"Plugin {plugin_name} not found")
            return False
        
        plugin_info = self.plugins[plugin_name]
        
        try:
            # Import the plugin module
            if ':' in plugin_info.entry_point:
                module_name, attr_name = plugin_info.entry_point.split(':', 1)
            else:
                module_name, attr_name = plugin_info.entry_point, 'setup'
            
            module = importlib.import_module(module_name)
            
            # Get setup function
            if hasattr(module, attr_name):
                plugin_info.setup_func = getattr(module, attr_name)
            elif hasattr(module, 'setup'):
                plugin_info.setup_func = getattr(module, 'setup')
            else:
                logger.error(f"Plugin {plugin_name} has no setup function")
                return False
            
            # Get teardown function (optional)
            if hasattr(module, 'teardown'):
                plugin_info.teardown_func = getattr(module, 'teardown')
            
            # Call setup function
            if self.app and plugin_info.setup_func:
                result = plugin_info.setup_func(self.app)
                plugin_info.instance = result
            
            plugin_info.loaded = True
            self.load_order.append(plugin_name)
            
            logger.info(f"Successfully loaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {e}")
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a specific plugin.
        
        Args:
            plugin_name: Name of the plugin to unload
            
        Returns:
            True if plugin unloaded successfully, False otherwise
        """
        if plugin_name not in self.plugins or not self.plugins[plugin_name].loaded:
            logger.warning(f"Plugin {plugin_name} not loaded")
            return False
        
        plugin_info = self.plugins[plugin_name]
        
        try:
            # Call teardown function if available
            if plugin_info.teardown_func and self.app:
                plugin_info.teardown_func(self.app)
            
            plugin_info.loaded = False
            plugin_info.instance = None
            
            if plugin_name in self.load_order:
                self.load_order.remove(plugin_name)
            
            logger.info(f"Successfully unloaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error unloading plugin {plugin_name}: {e}")
            return False
    
    def load_all_plugins(self) -> Dict[str, bool]:
        """
        Load all discovered plugins.
        
        Returns:
            Dictionary mapping plugin names to load success status
        """
        discovered = self.discover_plugins()
        results = {}
        
        for plugin_info in discovered:
            self.plugins[plugin_info.name] = plugin_info
            results[plugin_info.name] = self.load_plugin(plugin_info.name)
        
        return results
    
    def get_loaded_plugins(self) -> List[PluginInfo]:
        """Get list of loaded plugins."""
        return [plugin for plugin in self.plugins.values() if plugin.loaded]
    
    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """Get information about a specific plugin."""
        return self.plugins.get(plugin_name)
    
    def register_hook(self, hook_name: str, callback: Callable):
        """Register a hook callback."""
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        self.hooks[hook_name].append(callback)
    
    def call_hook(self, hook_name: str, *args, **kwargs):
        """Call all callbacks registered for a hook."""
        if hook_name in self.hooks:
            for callback in self.hooks[hook_name]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error calling hook {hook_name}: {e}")
    
    def reload_plugin(self, plugin_name: str) -> bool:
        """Reload a plugin (unload then load)."""
        if plugin_name in self.plugins and self.plugins[plugin_name].loaded:
            self.unload_plugin(plugin_name)
        return self.load_plugin(plugin_name)
