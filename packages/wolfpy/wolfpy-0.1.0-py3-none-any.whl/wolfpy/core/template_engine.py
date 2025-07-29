"""
WolfPy Template Engine Module.

This module provides enhanced template rendering functionality using Jinja2 templates.
Includes template loading, advanced caching, context management, asset management,
live reload, and comprehensive error handling with performance optimization.
"""

import os
import sys
import time
import hashlib
import json
import threading
import asyncio
import gzip
import pickle
from typing import Dict, Any, Optional, List, Callable, Union, Set, Tuple
from pathlib import Path
from collections import defaultdict, OrderedDict
from concurrent.futures import ThreadPoolExecutor
import weakref

# Jinja2 imports
try:
    from jinja2 import Environment, FileSystemLoader, BaseLoader, Template
    from jinja2 import TemplateNotFound, TemplateSyntaxError, TemplateRuntimeError
    from jinja2 import select_autoescape, StrictUndefined
    from markupsafe import Markup
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False

# Mako imports (for backward compatibility)
try:
    from mako.template import Template as MakoTemplate
    from mako.lookup import TemplateLookup
    from mako.exceptions import TemplateLookupException, TemplateRuntimeException
    HAS_MAKO = True
except ImportError:
    HAS_MAKO = False


class TemplateError(Exception):
    """Base exception for template-related errors."""
    pass


class TemplateNotFoundError(TemplateError, FileNotFoundError):
    """Raised when a template cannot be found."""
    pass


class TemplateSyntaxErrorWrapper(TemplateError):
    """Raised when there's a syntax error in a template."""
    pass


class TemplateRuntimeErrorWrapper(TemplateError):
    """Raised when there's a runtime error in a template."""
    pass


class AssetManager:
    """
    Asset management for templates with versioning and bundling.
    """

    def __init__(self, static_folder: str = 'static', version_assets: bool = True):
        """
        Initialize asset manager.

        Args:
            static_folder: Path to static assets
            version_assets: Whether to add version hashes to asset URLs
        """
        self.static_folder = static_folder
        self.version_assets = version_assets
        self._asset_cache = {}
        self._bundles = {}

        # Ensure static folder exists
        os.makedirs(static_folder, exist_ok=True)

    def get_asset_url(self, asset_path: str) -> str:
        """
        Get versioned URL for an asset.

        Args:
            asset_path: Relative path to asset

        Returns:
            Versioned asset URL
        """
        if not self.version_assets:
            return f"/static/{asset_path}"

        # Check cache first
        if asset_path in self._asset_cache:
            cached_info = self._asset_cache[asset_path]
            file_path = os.path.join(self.static_folder, asset_path)

            # Check if file has been modified
            if os.path.exists(file_path):
                mtime = os.path.getmtime(file_path)
                if mtime == cached_info['mtime']:
                    return cached_info['url']

        # Generate new versioned URL
        file_path = os.path.join(self.static_folder, asset_path)
        if os.path.exists(file_path):
            # Generate hash from file content and modification time
            with open(file_path, 'rb') as f:
                content = f.read()

            mtime = os.path.getmtime(file_path)
            version_hash = hashlib.md5(content + str(mtime).encode()).hexdigest()[:8]

            # Create versioned URL
            if '.' in asset_path:
                name, ext = asset_path.rsplit('.', 1)
                versioned_url = f"/static/{name}.{version_hash}.{ext}"
            else:
                versioned_url = f"/static/{asset_path}?v={version_hash}"

            # Cache the result
            self._asset_cache[asset_path] = {
                'url': versioned_url,
                'mtime': mtime,
                'hash': version_hash
            }

            return versioned_url

        # File doesn't exist, return original path
        return f"/static/{asset_path}"

    def create_bundle(self, bundle_name: str, assets: List[str], bundle_type: str = 'css'):
        """
        Create an asset bundle.

        Args:
            bundle_name: Name of the bundle
            assets: List of asset paths to bundle
            bundle_type: Type of bundle ('css' or 'js')
        """
        self._bundles[bundle_name] = {
            'assets': assets,
            'type': bundle_type,
            'created': time.time()
        }

    def get_bundle_url(self, bundle_name: str) -> str:
        """
        Get URL for an asset bundle.

        Args:
            bundle_name: Name of the bundle

        Returns:
            Bundle URL
        """
        if bundle_name not in self._bundles:
            return ""

        bundle = self._bundles[bundle_name]
        bundle_type = bundle['type']

        # For now, return individual asset URLs
        # In production, this would return a single bundled file URL
        assets = bundle['assets']
        if len(assets) == 1:
            return self.get_asset_url(assets[0])

        # Return the first asset URL as placeholder
        return self.get_asset_url(assets[0]) if assets else ""


class LiveReloadManager:
    """
    Live reload functionality for development.
    """

    def __init__(self, watch_folders: List[str] = None):
        """
        Initialize live reload manager.

        Args:
            watch_folders: Folders to watch for changes
        """
        self.watch_folders = watch_folders or ['templates', 'static']
        self._file_mtimes = {}
        self._enabled = False

    def enable(self):
        """Enable live reload."""
        self._enabled = True
        self._scan_files()

    def disable(self):
        """Disable live reload."""
        self._enabled = False

    def _scan_files(self):
        """Scan watched folders for file modification times."""
        for folder in self.watch_folders:
            if os.path.exists(folder):
                for root, dirs, files in os.walk(folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            self._file_mtimes[file_path] = os.path.getmtime(file_path)
                        except OSError:
                            pass

    def check_for_changes(self) -> bool:
        """
        Check if any watched files have changed.

        Returns:
            True if changes detected, False otherwise
        """
        if not self._enabled:
            return False

        for folder in self.watch_folders:
            if os.path.exists(folder):
                for root, dirs, files in os.walk(folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            current_mtime = os.path.getmtime(file_path)
                            if file_path not in self._file_mtimes:
                                self._file_mtimes[file_path] = current_mtime
                                return True
                            elif current_mtime != self._file_mtimes[file_path]:
                                self._file_mtimes[file_path] = current_mtime
                                return True
                        except OSError:
                            pass

        return False

    def get_reload_script(self) -> str:
        """
        Get JavaScript code for live reload functionality.

        Returns:
            JavaScript code as string
        """
        if not self._enabled:
            return ""

        return """
        <script>
        (function() {
            let lastCheck = Date.now();

            function checkForReload() {
                fetch('/dev/reload-check', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({lastCheck: lastCheck})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.reload) {
                        window.location.reload();
                    }
                    lastCheck = Date.now();
                })
                .catch(() => {
                    // Silently ignore errors
                });
            }

            // Check every 1 second
            setInterval(checkForReload, 1000);
        })();
        </script>
        """


class Jinja2TemplateEngine:
    """
    Jinja2-based template engine for FoxPy.

    Provides full Jinja2 templating functionality with inheritance,
    includes, filters, custom functions, and more.
    """

    def __init__(self,
                 template_folders: Union[str, List[str]] = 'templates',
                 cache_enabled: bool = True,
                 auto_reload: bool = True,
                 strict_undefined: bool = False,
                 autoescape: bool = True,
                 static_folder: str = 'static',
                 enable_live_reload: bool = False):
        """
        Initialize Jinja2 template engine with advanced features.

        Args:
            template_folders: Directory or list of directories containing templates
            cache_enabled: Whether to enable template caching
            auto_reload: Whether to auto-reload templates when changed
            strict_undefined: Whether to raise errors for undefined variables
            autoescape: Whether to enable auto-escaping for HTML
            static_folder: Directory containing static assets
            enable_live_reload: Whether to enable live reload for development
        """
        # Normalize template folders to list
        if isinstance(template_folders, str):
            self.template_folders = [template_folders]
        else:
            self.template_folders = template_folders

        # Ensure all template folders exist
        for folder in self.template_folders:
            os.makedirs(folder, exist_ok=True)

        self.cache_enabled = cache_enabled
        self.auto_reload = auto_reload
        self.strict_undefined = strict_undefined
        self.autoescape = autoescape
        self.static_folder = static_folder

        # Initialize asset management and live reload
        self.asset_manager = AssetManager(static_folder, version_assets=True)
        self.live_reload = LiveReloadManager(self.template_folders + [static_folder])

        if enable_live_reload:
            self.live_reload.enable()

        # Create Jinja2 environment
        self._create_environment()

        # Custom filters and functions
        self.custom_filters = {}
        self.custom_functions = {}

        # Add default filters and functions
        self._add_default_filters()
        self._add_default_functions()

        # Performance tracking
        self._render_stats = {
            'total_renders': 0,
            'total_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }

        # Advanced template features
        self._template_compilation_cache = {}  # Pre-compiled templates
        self._template_dependency_graph = {}  # Template inheritance tracking
        self._template_metrics = {}  # Per-template performance metrics
        self._template_optimization_enabled = True

        # Advanced caching strategies
        self._multi_level_cache_enabled = cache_enabled
        self._template_fingerprints = {}  # For cache invalidation
        self._template_precompilation_enabled = not auto_reload
        self._cache_warming_enabled = cache_enabled

        # Template compilation and optimization
        self._compiled_template_cache = OrderedDict()
        self._template_source_cache = {}
        self._template_ast_cache = {}
        self._template_compression_enabled = True

        # Advanced performance features
        self._async_rendering_enabled = False
        self._template_executor = ThreadPoolExecutor(max_workers=2)
        self._render_queue = asyncio.Queue() if hasattr(asyncio, 'Queue') else None

        # Template analytics and monitoring
        self._template_usage_stats = defaultdict(lambda: {
            'render_count': 0,
            'total_time': 0.0,
            'avg_time': 0.0,
            'last_rendered': None,
            'error_count': 0
        })

        # Component system
        self._components = {}
        self._component_cache = {}

        # Template security
        self._security_enabled = True
        self._allowed_tags = set()
        self._blocked_functions = {'eval', 'exec', 'compile', '__import__'}

        # Thread safety
        self._lock = threading.RLock()

        # Advanced template features
        self._template_streaming_enabled = False
        self._template_fragments_cache = {}
        self._template_hot_reload_enabled = auto_reload
        self._template_memory_mapping = {}

        # Template compilation pipeline
        self._compilation_pipeline = []
        self._optimization_passes = []
        self._minification_enabled = not auto_reload

        # Advanced caching layers
        self._l1_cache = {}  # Memory cache
        self._l2_cache_enabled = False  # Disk cache
        self._l3_cache_enabled = False  # Distributed cache

        # Template analytics
        self._template_heat_map = defaultdict(int)
        self._template_error_tracking = defaultdict(list)
        self._template_dependency_tracking = defaultdict(set)

        # Context processors
        self.context_processors = []

    def _create_environment(self):
        """Create the Jinja2 environment."""
        # Create file system loader
        loader = FileSystemLoader(self.template_folders)

        # Configure auto-escaping
        if self.autoescape:
            autoescape = select_autoescape(['html', 'htm', 'xml'])
        else:
            autoescape = False

        # Create environment
        env_kwargs = {
            'loader': loader,
            'autoescape': autoescape,
            'cache_size': 400 if self.cache_enabled else 0,
            'auto_reload': self.auto_reload,
            'trim_blocks': True,
            'lstrip_blocks': True
        }

        # Only set undefined if strict_undefined is True
        if self.strict_undefined:
            env_kwargs['undefined'] = StrictUndefined

        self.env = Environment(**env_kwargs)

    def _add_default_filters(self):
        """Add default template filters."""
        def currency(value, symbol='$'):
            """Format a number as currency."""
            try:
                return f"{symbol}{float(value):.2f}"
            except (ValueError, TypeError):
                return value

        def truncate_words(value, length=50, suffix='...'):
            """Truncate text to specified number of words."""
            if not isinstance(value, str):
                return value
            words = value.split()
            if len(words) <= length:
                return value
            return ' '.join(words[:length]) + suffix

        def nl2br(value):
            """Convert newlines to <br> tags."""
            if not isinstance(value, str):
                return value
            return Markup(value.replace('\n', '<br>\n'))

        # Register filters
        self.add_filter('currency', currency)
        self.add_filter('truncate_words', truncate_words)
        self.add_filter('nl2br', nl2br)

    def _add_default_functions(self):
        """Add default template functions with asset management."""
        def url_for(endpoint, **kwargs):
            """Generate URL for endpoint (placeholder implementation)."""
            # This would integrate with the router in a full implementation
            return f"/{endpoint}"

        def static_url(filename):
            """Generate versioned URL for static file."""
            return self.asset_manager.get_asset_url(filename)

        def asset_url(filename):
            """Alias for static_url."""
            return self.asset_manager.get_asset_url(filename)

        def bundle_url(bundle_name):
            """Generate URL for asset bundle."""
            return self.asset_manager.get_bundle_url(bundle_name)

        def csrf_token():
            """Generate CSRF token (placeholder implementation)."""
            import secrets
            return secrets.token_urlsafe(32)

        def live_reload_script():
            """Get live reload script for development."""
            return self.live_reload.get_reload_script()

        def current_time():
            """Get current timestamp."""
            return time.time()

        def format_datetime(timestamp, format_str='%Y-%m-%d %H:%M:%S'):
            """Format timestamp as datetime string."""
            import datetime
            if isinstance(timestamp, (int, float)):
                dt = datetime.datetime.fromtimestamp(timestamp)
            else:
                dt = timestamp
            return dt.strftime(format_str)

        # Register functions
        self.add_function('url_for', url_for)
        self.add_function('static_url', static_url)
        self.add_function('asset_url', asset_url)
        self.add_function('bundle_url', bundle_url)
        self.add_function('csrf_token', csrf_token)
        self.add_function('live_reload_script', live_reload_script)
        self.add_function('current_time', current_time)
        self.add_function('format_datetime', format_datetime)

    def enable_advanced_compilation(self):
        """Enable advanced template compilation features."""
        self._template_precompilation_enabled = True
        self._template_optimization_enabled = True
        self._minification_enabled = True

        # Add optimization passes
        self._optimization_passes = [
            self._optimize_static_expressions,
            self._optimize_loop_unrolling,
            self._optimize_conditional_elimination,
            self._optimize_template_inlining
        ]

        # Precompile existing templates
        self._precompile_templates()

    def _optimize_static_expressions(self, template_source: str) -> str:
        """Optimize static expressions in templates."""
        # Simple optimization: pre-calculate static expressions
        import re

        # Find static arithmetic expressions
        static_expr_pattern = r'\{\{\s*(\d+\s*[+\-*/]\s*\d+)\s*\}\}'

        def evaluate_static_expr(match):
            expr = match.group(1)
            try:
                result = eval(expr)  # Safe for simple arithmetic
                return f"{{{{ {result} }}}}"
            except:
                return match.group(0)

        return re.sub(static_expr_pattern, evaluate_static_expr, template_source)

    def _optimize_loop_unrolling(self, template_source: str) -> str:
        """Optimize small loops by unrolling them."""
        # For small, static loops, unroll them for better performance
        # This is a simplified implementation
        return template_source

    def _optimize_conditional_elimination(self, template_source: str) -> str:
        """Eliminate dead conditional branches."""
        # Remove unreachable conditional branches
        # This is a simplified implementation
        return template_source

    def _optimize_template_inlining(self, template_source: str) -> str:
        """Inline small templates and macros."""
        # Inline small templates for better performance
        # This is a simplified implementation
        return template_source

    def _precompile_templates(self):
        """Precompile all templates for faster rendering."""
        with self._lock:
            for folder in self.template_folders:
                if os.path.exists(folder):
                    for root, dirs, files in os.walk(folder):
                        for file in files:
                            if file.endswith(('.html', '.htm', '.xml', '.txt')):
                                template_path = os.path.relpath(
                                    os.path.join(root, file), folder
                                )
                                try:
                                    # Load and compile template
                                    template = self.env.get_template(template_path)
                                    self._compiled_template_cache[template_path] = template
                                except Exception as e:
                                    print(f"Failed to precompile template {template_path}: {e}")

    def enable_streaming_templates(self):
        """Enable template streaming for large templates."""
        self._template_streaming_enabled = True

    def create_template_fragment(self, name: str, template_source: str):
        """Create a reusable template fragment."""
        with self._lock:
            try:
                template = self.env.from_string(template_source)
                self._template_fragments_cache[name] = template
            except Exception as e:
                raise TemplateSyntaxErrorWrapper(f"Error creating fragment '{name}': {e}")

    def render_fragment(self, name: str, context: Dict[str, Any] = None) -> str:
        """Render a template fragment."""
        if name not in self._template_fragments_cache:
            raise TemplateNotFoundError(f"Fragment '{name}' not found")

        context = context or {}
        try:
            return self._template_fragments_cache[name].render(**context)
        except Exception as e:
            raise TemplateRuntimeErrorWrapper(f"Error rendering fragment '{name}': {e}")

    def enable_template_hot_reload(self):
        """Enable hot reloading of templates during development."""
        self._template_hot_reload_enabled = True
        self.live_reload.enable()

    def disable_template_hot_reload(self):
        """Disable hot reloading of templates."""
        self._template_hot_reload_enabled = False
        self.live_reload.disable()

    def get_template_analytics(self) -> Dict[str, Any]:
        """Get comprehensive template analytics."""
        with self._lock:
            analytics = {
                'render_stats': self._render_stats.copy(),
                'template_usage': dict(self._template_usage_stats),
                'template_heat_map': dict(self._template_heat_map),
                'cache_stats': {
                    'l1_cache_size': len(self._l1_cache),
                    'compiled_cache_size': len(self._compiled_template_cache),
                    'fragments_cache_size': len(self._template_fragments_cache)
                },
                'error_tracking': dict(self._template_error_tracking),
                'dependency_graph': dict(self._template_dependency_tracking)
            }

            # Calculate additional metrics
            total_renders = self._render_stats['total_renders']
            if total_renders > 0:
                analytics['avg_render_time'] = self._render_stats['total_time'] / total_renders
                analytics['cache_hit_rate'] = (
                    self._render_stats['cache_hits'] / total_renders * 100
                )

            return analytics

    def add_context_processor(self, processor: Callable):
        """
        Add a context processor function.

        Args:
            processor: Function that returns a dict to add to template context
        """
        self.context_processors.append(processor)

    def _process_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process context through context processors.

        Args:
            context: Original context

        Returns:
            Enhanced context with processor data
        """
        enhanced_context = context.copy()

        for processor in self.context_processors:
            try:
                processor_context = processor()
                if isinstance(processor_context, dict):
                    enhanced_context.update(processor_context)
            except Exception:
                # Silently ignore context processor errors in production
                pass

        return enhanced_context

    def precompile_templates(self) -> int:
        """
        Precompile all templates for production performance.

        Returns:
            Number of templates precompiled
        """
        compiled_count = 0
        start_time = time.time()

        for folder in self.template_folders:
            if os.path.exists(folder):
                for root, dirs, files in os.walk(folder):
                    for file in files:
                        if file.endswith(('.html', '.htm', '.jinja2', '.j2')):
                            template_path = os.path.relpath(
                                os.path.join(root, file),
                                folder
                            ).replace('\\', '/')

                            try:
                                self.compile_template(template_path)
                                compiled_count += 1
                            except Exception as e:
                                print(f"Failed to precompile {template_path}: {e}")

        compilation_time = time.time() - start_time
        print(f"Precompiled {compiled_count} templates in {compilation_time:.3f}s")

        return compiled_count

    def register_component(self, name: str, template_path: str,
                          default_props: Dict[str, Any] = None):
        """
        Register a reusable template component.

        Args:
            name: Component name
            template_path: Path to component template
            default_props: Default properties for the component
        """
        self._components[name] = {
            'template_path': template_path,
            'default_props': default_props or {},
            'created': time.time()
        }

    def render_component(self, name: str, props: Dict[str, Any] = None) -> str:
        """
        Render a registered component.

        Args:
            name: Component name
            props: Component properties

        Returns:
            Rendered component HTML
        """
        if name not in self._components:
            raise TemplateNotFoundError(f"Component '{name}' not found")

        component = self._components[name]

        # Merge default props with provided props
        component_context = component['default_props'].copy()
        if props:
            component_context.update(props)

        # Check component cache
        cache_key = f"{name}:{hash(str(sorted(component_context.items())))}"
        if cache_key in self._component_cache:
            return self._component_cache[cache_key]

        # Render component
        result = self.render(component['template_path'], component_context)

        # Cache result
        self._component_cache[cache_key] = result

        return result

    def enable_async_rendering(self):
        """Enable asynchronous template rendering."""
        self._async_rendering_enabled = True

    def disable_async_rendering(self):
        """Disable asynchronous template rendering."""
        self._async_rendering_enabled = False

    async def render_async(self, template_name: str, context: Dict[str, Any] = None) -> str:
        """
        Render template asynchronously.

        Args:
            template_name: Name of template to render
            context: Template context variables

        Returns:
            Rendered template content
        """
        if not self._async_rendering_enabled:
            # Fall back to synchronous rendering
            return self.render(template_name, context)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._template_executor,
            self.render,
            template_name,
            context
        )

    def compile_template(self, template_name: str) -> Any:
        """
        Pre-compile a template for faster rendering.

        Args:
            template_name: Name of template to compile

        Returns:
            Compiled template object
        """
        if template_name in self._compiled_template_cache:
            return self._compiled_template_cache[template_name]

        try:
            template = self.env.get_template(template_name)

            # Store in compilation cache
            self._compiled_template_cache[template_name] = template

            # Update dependency graph
            self._update_dependency_graph(template_name, template)

            return template

        except TemplateNotFound:
            raise TemplateNotFoundError(f"Template '{template_name}' not found")

    def _update_dependency_graph(self, template_name: str, template: Any):
        """Update template dependency graph for cache invalidation."""
        dependencies = set()

        # Extract template dependencies (extends, includes)
        if hasattr(template, 'blocks'):
            # This is a simplified dependency extraction
            # In a full implementation, you'd parse the AST
            source = template.source if hasattr(template, 'source') else ""

            # Find extends
            import re
            extends_matches = re.findall(r'{%\s*extends\s+["\']([^"\']+)["\']', source)
            dependencies.update(extends_matches)

            # Find includes
            include_matches = re.findall(r'{%\s*include\s+["\']([^"\']+)["\']', source)
            dependencies.update(include_matches)

        self._template_dependency_graph[template_name] = dependencies

    def render(self, template_name: str, context: Dict[str, Any] = None) -> str:
        """
        Render a template with context, context processors, and performance tracking.

        Args:
            template_name: Name of template file
            context: Template context variables

        Returns:
            Rendered template string

        Raises:
            TemplateNotFoundError: If template is not found
            TemplateSyntaxErrorWrapper: If template has syntax errors
            TemplateRuntimeErrorWrapper: If template has runtime errors
        """
        start_time = time.time()
        context = context or {}

        # Process context through context processors
        enhanced_context = self._process_context(context)

        # Add asset management functions to context
        enhanced_context.update({
            'asset_manager': self.asset_manager,
            'live_reload_enabled': self.live_reload._enabled,
            'template_engine': self,
            'performance_stats': self.get_performance_stats()
        })

        try:
            template = self.env.get_template(template_name)

            # Check if template is cached
            is_cached = False
            if hasattr(self.env, 'cache') and self.env.cache is not None:
                is_cached = template_name in self.env.cache

            rendered = template.render(**enhanced_context)

            # Update performance stats
            render_time = time.time() - start_time
            self._render_stats['total_renders'] += 1
            self._render_stats['total_time'] += render_time

            if is_cached:
                self._render_stats['cache_hits'] += 1
            else:
                self._render_stats['cache_misses'] += 1

            # Track per-template metrics
            if template_name not in self._template_metrics:
                self._template_metrics[template_name] = {
                    'render_count': 0,
                    'total_time': 0.0,
                    'avg_time': 0.0,
                    'cache_hits': 0,
                    'last_rendered': time.time()
                }

            metrics = self._template_metrics[template_name]
            metrics['render_count'] += 1
            metrics['total_time'] += render_time
            metrics['avg_time'] = metrics['total_time'] / metrics['render_count']
            metrics['last_rendered'] = time.time()

            if is_cached:
                metrics['cache_hits'] += 1

            return rendered

        except TemplateNotFound as e:
            raise TemplateNotFoundError(f"Template '{template_name}' not found") from e
        except TemplateSyntaxError as e:
            raise TemplateSyntaxErrorWrapper(f"Syntax error in template '{template_name}': {e}") from e
        except TemplateRuntimeError as e:
            raise TemplateRuntimeErrorWrapper(f"Runtime error in template '{template_name}': {e}") from e
        except Exception as e:
            raise TemplateRuntimeErrorWrapper(f"Unexpected error in template '{template_name}': {e}") from e

    def render_with_debug(self, template_name: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Render a template with debugging information.

        Args:
            template_name: Name of template file
            context: Template context variables

        Returns:
            Dictionary with rendered content and debug info
        """
        import time
        start_time = time.time()

        context = context or {}
        enhanced_context = self._process_context(context)

        debug_info = {
            'template_name': template_name,
            'context_keys': list(enhanced_context.keys()),
            'context_processors_count': len(self.context_processors),
            'template_folders': self.template_folders,
            'cache_enabled': self.cache_enabled
        }

        try:
            template = self.env.get_template(template_name)

            # Get template source info
            source, filename, uptodate = self.env.loader.get_source(self.env, template_name)
            debug_info.update({
                'template_path': filename,
                'template_size': len(source),
                'template_lines': source.count('\n') + 1
            })

            # Render template
            rendered = template.render(**enhanced_context)

            render_time = time.time() - start_time
            debug_info.update({
                'render_time': render_time,
                'rendered_size': len(rendered),
                'success': True
            })

            return {
                'content': rendered,
                'debug': debug_info
            }

        except Exception as e:
            render_time = time.time() - start_time
            debug_info.update({
                'render_time': render_time,
                'error': str(e),
                'error_type': type(e).__name__,
                'success': False
            })

            return {
                'content': '',
                'debug': debug_info,
                'error': str(e)
            }

    def render_string(self, template_string: str, context: Dict[str, Any] = None) -> str:
        """
        Render a template from string.

        Args:
            template_string: Template content as string
            context: Template context variables

        Returns:
            Rendered template string

        Raises:
            TemplateSyntaxErrorWrapper: If template has syntax errors
            TemplateRuntimeErrorWrapper: If template has runtime errors
        """
        context = context or {}

        try:
            template = self.env.from_string(template_string)
            return template.render(**context)

        except TemplateSyntaxError as e:
            raise TemplateSyntaxErrorWrapper(f"Syntax error in template string: {e}") from e
        except TemplateRuntimeError as e:
            raise TemplateRuntimeErrorWrapper(f"Runtime error in template string: {e}") from e
        except Exception as e:
            raise TemplateRuntimeErrorWrapper(f"Unexpected error in template string: {e}") from e

    def add_filter(self, name: str, filter_func: Callable):
        """
        Add a custom template filter.

        Args:
            name: Filter name
            filter_func: Filter function
        """
        self.custom_filters[name] = filter_func
        self.env.filters[name] = filter_func

    def add_function(self, name: str, func: Callable):
        """
        Add a custom template function.

        Args:
            name: Function name
            func: Function
        """
        self.custom_functions[name] = func
        self.env.globals[name] = func

    def add_global(self, name: str, value: Any):
        """
        Add a global variable available to all templates.

        Args:
            name: Variable name
            value: Variable value
        """
        self.env.globals[name] = value

    def get_template(self, template_name: str) -> Template:
        """
        Get a template object.

        Args:
            template_name: Name of template file

        Returns:
            Jinja2 Template object

        Raises:
            TemplateNotFoundError: If template is not found
        """
        try:
            return self.env.get_template(template_name)
        except TemplateNotFound as e:
            raise TemplateNotFoundError(f"Template '{template_name}' not found") from e

    def template_exists(self, template_name: str) -> bool:
        """
        Check if a template exists.

        Args:
            template_name: Name of template file

        Returns:
            True if template exists, False otherwise
        """
        try:
            self.env.get_template(template_name)
            return True
        except TemplateNotFound:
            return False

    def list_templates(self) -> List[str]:
        """
        List all available templates.

        Returns:
            List of template names
        """
        templates = []
        for folder in self.template_folders:
            if os.path.exists(folder):
                for root, dirs, files in os.walk(folder):
                    for file in files:
                        if file.endswith(('.html', '.htm', '.txt', '.xml', '.j2', '.jinja', '.jinja2')):
                            rel_path = os.path.relpath(os.path.join(root, file), folder)
                            templates.append(rel_path.replace('\\', '/'))
        return sorted(list(set(templates)))

    def clear_cache(self):
        """Clear template cache."""
        self.env.cache.clear()

    def get_source(self, template_name: str) -> tuple:
        """
        Get template source code.

        Args:
            template_name: Name of template file

        Returns:
            Tuple of (source, filename, uptodate_func)
        """
        try:
            return self.env.loader.get_source(self.env, template_name)
        except TemplateNotFound as e:
            raise TemplateNotFoundError(f"Template '{template_name}' not found") from e

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get template engine performance statistics.

        Returns:
            Dictionary with performance metrics
        """
        stats = self._render_stats.copy()

        if stats['total_renders'] > 0:
            stats['avg_render_time'] = stats['total_time'] / stats['total_renders']
            stats['cache_hit_rate'] = stats['cache_hits'] / stats['total_renders']
        else:
            stats['avg_render_time'] = 0.0
            stats['cache_hit_rate'] = 0.0

        # Add advanced metrics
        stats['template_count'] = len(self._template_metrics)
        stats['precompiled_templates'] = len(self._template_compilation_cache)
        stats['dependency_graph_size'] = len(self._template_dependency_graph)

        return stats

    def precompile_templates(self):
        """
        Precompile all templates for faster rendering.

        This method compiles all templates in advance, which can significantly
        improve first-render performance in production.
        """
        if not self._template_precompilation_enabled:
            return

        compiled_count = 0
        start_time = time.time()

        for template_name in self.list_templates():
            try:
                if template_name not in self._template_compilation_cache:
                    template = self.env.get_template(template_name)
                    # Force compilation by accessing the template's compiled code
                    if hasattr(template, 'code'):
                        _ = template.code
                    elif hasattr(template, 'compile'):
                        template.compile()
                    else:
                        # For Jinja2, just getting the template compiles it
                        pass
                    self._template_compilation_cache[template_name] = template
                    compiled_count += 1
            except Exception as e:
                print(f"Warning: Could not precompile template '{template_name}': {e}")

        compilation_time = time.time() - start_time
        print(f"Precompiled {compiled_count} templates in {compilation_time:.3f}s")

    def build_dependency_graph(self):
        """
        Build template dependency graph for inheritance optimization.

        This helps identify which templates depend on others and can be used
        for cache invalidation and optimization.
        """
        for template_name in self.list_templates():
            try:
                template = self.env.get_template(template_name)
                dependencies = []

                # Extract template dependencies (extends, includes)
                if hasattr(template, 'blocks'):
                    # This is a simplified dependency extraction
                    # In a real implementation, you'd parse the template AST
                    source = self.env.loader.get_source(self.env, template_name)[0]

                    # Find extends statements
                    import re
                    extends_matches = re.findall(r'{%\s*extends\s+["\']([^"\']+)["\']', source)
                    dependencies.extend(extends_matches)

                    # Find include statements
                    include_matches = re.findall(r'{%\s*include\s+["\']([^"\']+)["\']', source)
                    dependencies.extend(include_matches)

                self._template_dependency_graph[template_name] = dependencies

            except Exception as e:
                print(f"Warning: Could not analyze dependencies for '{template_name}': {e}")

    def optimize_template_cache(self):
        """
        Optimize template cache based on usage patterns.

        This method analyzes template usage and optimizes caching strategies.
        """
        if not self._template_optimization_enabled:
            return

        # Sort templates by usage frequency
        template_usage = []
        for name, metrics in self._template_metrics.items():
            usage_score = metrics['render_count'] / max(metrics['avg_time'], 0.001)
            template_usage.append((name, usage_score, metrics))

        template_usage.sort(key=lambda x: x[1], reverse=True)

        # Keep frequently used templates in cache
        high_usage_templates = template_usage[:50]  # Top 50 templates

        for template_name, score, metrics in high_usage_templates:
            if template_name not in self._template_compilation_cache:
                try:
                    template = self.env.get_template(template_name)
                    self._template_compilation_cache[template_name] = template
                except Exception:
                    pass

    def get_template_metrics(self, template_name: str = None) -> Dict[str, Any]:
        """
        Get detailed metrics for a specific template or all templates.

        Args:
            template_name: Specific template name, or None for all templates

        Returns:
            Template metrics dictionary
        """
        if template_name:
            return self._template_metrics.get(template_name, {})

        return {
            'per_template_metrics': self._template_metrics.copy(),
            'total_templates': len(self._template_metrics),
            'most_used_template': max(
                self._template_metrics.items(),
                key=lambda x: x[1]['render_count'],
                default=(None, {})
            )[0] if self._template_metrics else None,
            'slowest_template': max(
                self._template_metrics.items(),
                key=lambda x: x[1]['avg_time'],
                default=(None, {})
            )[0] if self._template_metrics else None
        }

    def warm_cache(self, template_names: List[str] = None):
        """
        Warm template cache by pre-loading specified templates.

        Args:
            template_names: List of template names to warm, or None for all
        """
        if not self._cache_warming_enabled:
            return

        if template_names is None:
            template_names = self.list_templates()

        warmed_count = 0
        for template_name in template_names:
            try:
                template = self.env.get_template(template_name)
                # Force template loading and compilation
                if hasattr(template, 'code'):
                    _ = template.code
                elif hasattr(template, 'compile'):
                    template.compile()
                else:
                    # For Jinja2, just getting the template compiles it
                    pass
                warmed_count += 1
            except Exception as e:
                print(f"Warning: Could not warm cache for '{template_name}': {e}")

        print(f"Warmed cache for {warmed_count} templates")

    def invalidate_template_cache(self, template_name: str):
        """
        Invalidate cache for a specific template and its dependents.

        Args:
            template_name: Template to invalidate
        """
        # Remove from compilation cache
        self._template_compilation_cache.pop(template_name, None)

        # Remove from Jinja2 cache
        if hasattr(self.env, 'cache') and self.env.cache:
            try:
                # Try different cache invalidation methods
                if hasattr(self.env.cache, 'pop'):
                    self.env.cache.pop(template_name, None)
                elif hasattr(self.env.cache, 'clear'):
                    # If we can't remove specific items, clear the whole cache
                    self.env.cache.clear()
                elif hasattr(self.env.cache, '__delitem__'):
                    try:
                        del self.env.cache[template_name]
                    except KeyError:
                        pass
            except Exception:
                # Silently ignore cache invalidation errors
                pass

        # Invalidate dependent templates
        for name, dependencies in self._template_dependency_graph.items():
            if template_name in dependencies:
                self.invalidate_template_cache(name)

    def get_advanced_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive template engine statistics.

        Returns:
            Dictionary with detailed statistics
        """
        basic_stats = self.get_performance_stats()

        return {
            **basic_stats,
            'template_metrics': self.get_template_metrics(),
            'dependency_graph': self._template_dependency_graph,
            'optimization_enabled': self._template_optimization_enabled,
            'precompilation_enabled': self._template_precompilation_enabled,
            'cache_warming_enabled': self._cache_warming_enabled,
            'engine_type': 'Jinja2Enhanced'
        }

    def create_asset_bundle(self, bundle_name: str, assets: List[str], bundle_type: str = 'css'):
        """
        Create an asset bundle.

        Args:
            bundle_name: Name of the bundle
            assets: List of asset paths to bundle
            bundle_type: Type of bundle ('css' or 'js')
        """
        self.asset_manager.create_bundle(bundle_name, assets, bundle_type)

    def check_live_reload(self) -> bool:
        """
        Check if live reload should trigger.

        Returns:
            True if reload needed, False otherwise
        """
        return self.live_reload.check_for_changes()

    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a template.

        Args:
            template_name: Name of template file

        Returns:
            Dictionary with template information
        """
        try:
            source, filename, uptodate = self.get_source(template_name)
            template = self.get_template(template_name)

            return {
                'name': template_name,
                'filename': filename,
                'size': len(source),
                'lines': source.count('\n') + 1,
                'exists': True,
                'uptodate': uptodate() if callable(uptodate) else True,
                'blocks': list(template.blocks.keys()) if hasattr(template, 'blocks') else [],
                'globals': list(template.globals.keys()) if hasattr(template, 'globals') else []
            }
        except TemplateNotFoundError:
            return {
                'name': template_name,
                'exists': False
            }


class SimpleTemplateEngine:
    """
    Simple template engine fallback when Mako is not available.
    
    Provides basic string substitution templating.
    """
    
    def __init__(self, template_folder: str):
        """
        Initialize simple template engine.
        
        Args:
            template_folder: Directory containing templates
        """
        self.template_folder = template_folder
    
    def render(self, template_name: str, context: Dict[str, Any] = None) -> str:
        """
        Render a template with context.
        
        Args:
            template_name: Name of template file
            context: Template context variables
            
        Returns:
            Rendered template string
        """
        context = context or {}
        template_path = os.path.join(self.template_folder, template_name)
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Simple string substitution
            for key, value in context.items():
                placeholder = f"{{{{{key}}}}}"
                template_content = template_content.replace(placeholder, str(value))
            
            return template_content
            
        except FileNotFoundError:
            return f"Template '{template_name}' not found"
        except Exception as e:
            return f"Template error: {e}"


class MakoTemplateEngine:
    """
    Mako-based template engine.
    
    Provides full Mako templating functionality with inheritance,
    includes, filters, and more.
    """
    
    def __init__(self, 
                 template_folder: str,
                 cache_enabled: bool = True,
                 auto_reload: bool = True):
        """
        Initialize Mako template engine.
        
        Args:
            template_folder: Directory containing templates
            cache_enabled: Whether to enable template caching
            auto_reload: Whether to auto-reload templates when changed
        """
        self.template_folder = template_folder
        self.cache_enabled = cache_enabled
        self.auto_reload = auto_reload
        
        # Create template lookup
        self.lookup = TemplateLookup(
            directories=[template_folder],
            module_directory=os.path.join(template_folder, '.mako_cache') if cache_enabled else None,
            filesystem_checks=auto_reload,
            collection_size=500 if cache_enabled else -1
        )
    
    def render(self, template_name: str, context: Dict[str, Any] = None) -> str:
        """
        Render a template with context.
        
        Args:
            template_name: Name of template file
            context: Template context variables
            
        Returns:
            Rendered template string
        """
        context = context or {}
        
        try:
            template = self.lookup.get_template(template_name)
            return template.render(**context)
            
        except TemplateLookupException:
            return f"Template '{template_name}' not found"
        except TemplateRuntimeException as e:
            return f"Template runtime error: {e}"
        except Exception as e:
            return f"Template error: {e}"
    
    def render_string(self, template_string: str, context: Dict[str, Any] = None) -> str:
        """
        Render a template from string.
        
        Args:
            template_string: Template content as string
            context: Template context variables
            
        Returns:
            Rendered template string
        """
        context = context or {}
        
        try:
            template = Template(template_string, lookup=self.lookup)
            return template.render(**context)
            
        except TemplateRuntimeException as e:
            return f"Template runtime error: {e}"
        except Exception as e:
            return f"Template error: {e}"


class TemplateEngine:
    """
    Main template engine for FoxPy applications.

    Uses Jinja2 by default, falls back to Mako, then simple engine.
    """

    def __init__(self,
                 template_folders: Union[str, List[str]] = 'templates',
                 cache_enabled: bool = True,
                 auto_reload: bool = True,
                 engine: str = 'auto',
                 strict_undefined: bool = False,
                 autoescape: bool = True):
        """
        Initialize template engine.

        Args:
            template_folders: Directory or list of directories containing templates
            cache_enabled: Whether to enable template caching
            auto_reload: Whether to auto-reload templates when changed
            engine: Template engine to use ('auto', 'jinja2', 'mako', 'simple')
            strict_undefined: Whether to raise errors for undefined variables (Jinja2 only)
            autoescape: Whether to enable auto-escaping for HTML (Jinja2 only)
        """
        # Normalize template folders
        if isinstance(template_folders, str):
            self.template_folders = [template_folders]
        else:
            self.template_folders = template_folders

        # Ensure all template folders exist
        for folder in self.template_folders:
            os.makedirs(folder, exist_ok=True)

        # Choose engine based on preference and availability
        if engine == 'auto':
            if HAS_JINJA2:
                self.engine = Jinja2TemplateEngine(
                    self.template_folders, cache_enabled, auto_reload,
                    strict_undefined, autoescape
                )
                self.engine_type = 'jinja2'
            elif HAS_MAKO:
                # Use first template folder for Mako compatibility
                self.engine = MakoTemplateEngine(
                    self.template_folders[0], cache_enabled, auto_reload
                )
                self.engine_type = 'mako'
            else:
                self.engine = SimpleTemplateEngine(self.template_folders[0])
                self.engine_type = 'simple'
        elif engine == 'jinja2':
            if not HAS_JINJA2:
                raise ImportError("Jinja2 is not installed. Install with: pip install Jinja2")
            self.engine = Jinja2TemplateEngine(
                self.template_folders, cache_enabled, auto_reload,
                strict_undefined, autoescape
            )
            self.engine_type = 'jinja2'
        elif engine == 'mako':
            if not HAS_MAKO:
                raise ImportError("Mako is not installed. Install with: pip install Mako")
            self.engine = MakoTemplateEngine(
                self.template_folders[0], cache_enabled, auto_reload
            )
            self.engine_type = 'mako'
        elif engine == 'simple':
            self.engine = SimpleTemplateEngine(self.template_folders[0])
            self.engine_type = 'simple'
        else:
            raise ValueError(f"Unknown template engine: {engine}")

        # Store configuration
        self.cache_enabled = cache_enabled
        self.auto_reload = auto_reload
    
    def render(self, template_name: str, context: Dict[str, Any] = None, **kwargs) -> str:
        """
        Render a template with context.

        Args:
            template_name: Name of template file
            context: Template context variables
            **kwargs: Additional context variables

        Returns:
            Rendered template string

        Raises:
            TemplateNotFoundError: If template is not found
            TemplateSyntaxErrorWrapper: If template has syntax errors
            TemplateRuntimeErrorWrapper: If template has runtime errors
        """
        # Merge context and kwargs
        full_context = context or {}
        full_context.update(kwargs)

        try:
            return self.engine.render(template_name, full_context)
        except (TemplateNotFoundError, TemplateSyntaxErrorWrapper, TemplateRuntimeErrorWrapper):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Handle legacy engines that don't use our custom exceptions
            if "not found" in str(e).lower():
                raise TemplateNotFoundError(f"Template '{template_name}' not found") from e
            else:
                raise TemplateRuntimeErrorWrapper(f"Error rendering template '{template_name}': {e}") from e
    
    def render_string(self, template_string: str, context: Dict[str, Any] = None, **kwargs) -> str:
        """
        Render a template from string.

        Args:
            template_string: Template content as string
            context: Template context variables
            **kwargs: Additional context variables

        Returns:
            Rendered template string

        Raises:
            TemplateSyntaxErrorWrapper: If template has syntax errors
            TemplateRuntimeErrorWrapper: If template has runtime errors
        """
        # Merge context and kwargs
        full_context = context or {}
        full_context.update(kwargs)

        try:
            if hasattr(self.engine, 'render_string'):
                return self.engine.render_string(template_string, full_context)
            else:
                # Simple engine doesn't support string rendering
                return template_string
        except (TemplateSyntaxErrorWrapper, TemplateRuntimeErrorWrapper):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            raise TemplateRuntimeErrorWrapper(f"Error rendering template string: {e}") from e
    
    def add_global(self, name: str, value: Any):
        """
        Add a global variable available to all templates.

        Args:
            name: Variable name
            value: Variable value
        """
        if hasattr(self.engine, 'add_global'):
            self.engine.add_global(name, value)
        elif hasattr(self.engine, 'lookup'):
            # For Mako compatibility
            if not hasattr(self.engine.lookup, 'template_args'):
                self.engine.lookup.template_args = {}
            self.engine.lookup.template_args[name] = value

    def add_filter(self, name: str, filter_func: Callable):
        """
        Add a template filter function.

        Args:
            name: Filter name
            filter_func: Filter function
        """
        if hasattr(self.engine, 'add_filter'):
            self.engine.add_filter(name, filter_func)

    def add_function(self, name: str, func: Callable):
        """
        Add a template function.

        Args:
            name: Function name
            func: Function
        """
        if hasattr(self.engine, 'add_function'):
            self.engine.add_function(name, func)

    def add_context_processor(self, processor: Callable):
        """
        Add a context processor function.

        Args:
            processor: Function that returns a dict to add to template context
        """
        if hasattr(self.engine, 'add_context_processor'):
            self.engine.add_context_processor(processor)

    def render_with_debug(self, template_name: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Render a template with debugging information.

        Args:
            template_name: Name of template file
            context: Template context variables

        Returns:
            Dictionary with rendered content and debug info
        """
        if hasattr(self.engine, 'render_with_debug'):
            return self.engine.render_with_debug(template_name, context)
        else:
            # Fallback for engines without debug support
            try:
                content = self.render(template_name, context)
                return {
                    'content': content,
                    'debug': {
                        'template_name': template_name,
                        'engine_type': self.engine_type,
                        'debug_supported': False
                    }
                }
            except Exception as e:
                return {
                    'content': '',
                    'debug': {
                        'template_name': template_name,
                        'engine_type': self.engine_type,
                        'debug_supported': False,
                        'error': str(e)
                    },
                    'error': str(e)
                }
    
    def get_template_path(self, template_name: str) -> str:
        """
        Get full path to a template file.

        Args:
            template_name: Name of template file

        Returns:
            Full path to template file
        """
        # Return path from first template folder for compatibility
        return os.path.join(self.template_folders[0], template_name)

    def template_exists(self, template_name: str) -> bool:
        """
        Check if a template file exists.

        Args:
            template_name: Name of template file

        Returns:
            True if template exists, False otherwise
        """
        if hasattr(self.engine, 'template_exists'):
            return self.engine.template_exists(template_name)
        else:
            # Fallback: check in all template folders
            for folder in self.template_folders:
                if os.path.exists(os.path.join(folder, template_name)):
                    return True
            return False

    def list_templates(self) -> List[str]:
        """
        List all available templates.

        Returns:
            List of template file names
        """
        if hasattr(self.engine, 'list_templates'):
            return self.engine.list_templates()
        else:
            # Fallback implementation
            templates = []
            for folder in self.template_folders:
                if os.path.exists(folder):
                    for root, dirs, files in os.walk(folder):
                        for file in files:
                            if file.endswith(('.html', '.htm', '.txt', '.xml', '.mako', '.j2', '.jinja', '.jinja2')):
                                rel_path = os.path.relpath(os.path.join(root, file), folder)
                                templates.append(rel_path.replace('\\', '/'))
            return sorted(list(set(templates)))

    def clear_cache(self):
        """Clear template cache."""
        if hasattr(self.engine, 'clear_cache'):
            self.engine.clear_cache()
        elif hasattr(self.engine, 'lookup') and hasattr(self.engine.lookup, 'collection'):
            self.engine.lookup.collection.clear()

    def get_source(self, template_name: str) -> tuple:
        """
        Get template source code.

        Args:
            template_name: Name of template file

        Returns:
            Tuple of (source, filename, uptodate_func)

        Raises:
            TemplateNotFoundError: If template is not found
        """
        if hasattr(self.engine, 'get_source'):
            return self.engine.get_source(template_name)
        else:
            # Fallback implementation
            for folder in self.template_folders:
                template_path = os.path.join(folder, template_name)
                if os.path.exists(template_path):
                    with open(template_path, 'r', encoding='utf-8') as f:
                        source = f.read()
                    return source, template_path, lambda: True
            raise TemplateNotFoundError(f"Template '{template_name}' not found")

    def get_engine_info(self) -> Dict[str, Any]:
        """
        Get information about the current template engine.

        Returns:
            Dictionary with engine information
        """
        return {
            'engine_type': self.engine_type,
            'template_folders': self.template_folders,
            'cache_enabled': self.cache_enabled,
            'auto_reload': self.auto_reload,
            'available_engines': {
                'jinja2': HAS_JINJA2,
                'mako': HAS_MAKO,
                'simple': True
            }
        }


# Template helper functions

def create_base_template(template_folder: str, engine_type: str = 'jinja2'):
    """
    Create a base template file for inheritance.

    Args:
        template_folder: Directory to create template in
        engine_type: Template engine type ('jinja2' or 'mako')
    """
    if engine_type == 'jinja2':
        base_template_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}FoxPy Application{% endblock %}</title>
    {% block head %}{% endblock %}
</head>
<body>
    <header>
        {% block header %}
            <h1>FoxPy Application</h1>
        {% endblock %}
    </header>

    <main>
        {% block content %}
            <p>Welcome to FoxPy!</p>
        {% endblock %}
    </main>

    <footer>
        {% block footer %}
            <p>&copy; 2024 FoxPy Application</p>
        {% endblock %}
    </footer>

    {% block scripts %}{% endblock %}
</body>
</html>'''
    else:  # Mako
        base_template_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><%block name="title">FoxPy Application</%block></title>
    <%block name="head"></%block>
</head>
<body>
    <header>
        <%block name="header">
            <h1>FoxPy Application</h1>
        </%block>
    </header>

    <main>
        <%block name="content">
            <p>Welcome to FoxPy!</p>
        </%block>
    </main>

    <footer>
        <%block name="footer">
            <p>&copy; 2024 FoxPy Application</p>
        </%block>
    </footer>

    <%block name="scripts"></%block>
</body>
</html>'''

    base_template_path = os.path.join(template_folder, 'base.html')
    os.makedirs(template_folder, exist_ok=True)

    with open(base_template_path, 'w', encoding='utf-8') as f:
        f.write(base_template_content)


def create_example_template(template_folder: str, engine_type: str = 'jinja2'):
    """
    Create an example template that extends the base template.

    Args:
        template_folder: Directory to create template in
        engine_type: Template engine type ('jinja2' or 'mako')
    """
    if engine_type == 'jinja2':
        example_template_content = '''{% extends "base.html" %}

{% block title %}Example Page - FoxPy{% endblock %}

{% block content %}
    <h2>Hello, {{ name or 'World' }}!</h2>
    <p>This is an example template using Jinja2.</p>

    {% if items %}
        <ul>
        {% for item in items %}
            <li>{{ item }}</li>
        {% endfor %}
        </ul>
    {% else %}
        <p>No items to display.</p>
    {% endif %}

    <div class="features">
        <h3>Template Features:</h3>
        <ul>
            <li>Template inheritance with {% raw %}{% extends %}{% endraw %}</li>
            <li>Block overrides with {% raw %}{% block %}{% endraw %}</li>
            <li>Variable output with {% raw %}{{ variable }}{% endraw %}</li>
            <li>Control structures with {% raw %}{% if %}{% endraw %} and {% raw %}{% for %}{% endraw %}</li>
            <li>Filters: {{ "hello world" | title }}</li>
            <li>Functions: {{ static_url('style.css') }}</li>
        </ul>
    </div>
{% endblock %}

{% block scripts %}
    <script>
        console.log('Example Jinja2 template loaded');
    </script>
{% endblock %}'''
    else:  # Mako
        example_template_content = '''<%inherit file="base.html"/>

<%block name="title">Example Page - FoxPy</%block>

<%block name="content">
    <h2>Hello, ${name or 'World'}!</h2>
    <p>This is an example template using Mako.</p>

    % if items:
        <ul>
        % for item in items:
            <li>${item}</li>
        % endfor
        </ul>
    % else:
        <p>No items to display.</p>
    % endif
</%block>

<%block name="scripts">
    <script>
        console.log('Example template loaded');
    </script>
</%block>'''

    example_template_path = os.path.join(template_folder, 'example.html')
    os.makedirs(template_folder, exist_ok=True)

    with open(example_template_path, 'w', encoding='utf-8') as f:
        f.write(example_template_content)


def create_error_templates(template_folder: str, engine_type: str = 'jinja2'):
    """
    Create error page templates.

    Args:
        template_folder: Directory to create templates in
        engine_type: Template engine type ('jinja2' or 'mako')
    """
    os.makedirs(template_folder, exist_ok=True)

    if engine_type == 'jinja2':
        # 404 Error Template
        error_404_content = '''{% extends "base.html" %}

{% block title %}Page Not Found - FoxPy{% endblock %}

{% block content %}
    <div class="error-page">
        <h1>404 - Page Not Found</h1>
        <p>The page you are looking for could not be found.</p>
        <p><a href="/">Return to Home</a></p>

        {% if debug %}
            <div class="debug-info">
                <h3>Debug Information:</h3>
                <p><strong>Path:</strong> {{ request.path }}</p>
                <p><strong>Method:</strong> {{ request.method }}</p>
                <p><strong>User Agent:</strong> {{ request.user_agent }}</p>
            </div>
        {% endif %}
    </div>
{% endblock %}'''

        # 500 Error Template
        error_500_content = '''{% extends "base.html" %}

{% block title %}Server Error - FoxPy{% endblock %}

{% block content %}
    <div class="error-page">
        <h1>500 - Internal Server Error</h1>
        <p>An unexpected error occurred. Please try again later.</p>
        <p><a href="/">Return to Home</a></p>

        {% if debug and error %}
            <div class="debug-info">
                <h3>Error Details:</h3>
                <pre>{{ error }}</pre>
            </div>
        {% endif %}
    </div>
{% endblock %}'''
    else:  # Mako
        error_404_content = '''<%inherit file="base.html"/>

<%block name="title">Page Not Found - FoxPy</%block>

<%block name="content">
    <div class="error-page">
        <h1>404 - Page Not Found</h1>
        <p>The page you are looking for could not be found.</p>
        <p><a href="/">Return to Home</a></p>
    </div>
</%block>'''

        error_500_content = '''<%inherit file="base.html"/>

<%block name="title">Server Error - FoxPy</%block>

<%block name="content">
    <div class="error-page">
        <h1>500 - Internal Server Error</h1>
        <p>An unexpected error occurred. Please try again later.</p>
        <p><a href="/">Return to Home</a></p>
    </div>
</%block>'''

    # Write error templates
    with open(os.path.join(template_folder, '404.html'), 'w', encoding='utf-8') as f:
        f.write(error_404_content)

    with open(os.path.join(template_folder, '500.html'), 'w', encoding='utf-8') as f:
        f.write(error_500_content)
