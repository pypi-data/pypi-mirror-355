"""
WolfPy Documentation System

Provides markdown-powered live documentation at /docs endpoint.
Supports nested documentation structure, syntax highlighting, and auto-discovery.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import unquote

try:
    import markdown
    from markdown.extensions import codehilite, toc
    from pygments.formatters import HtmlFormatter
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

from .response import Response


class DocumentationSystem:
    """
    Markdown-powered documentation system for WolfPy applications.
    
    Features:
    - Auto-discovery of markdown files
    - Nested documentation structure
    - Syntax highlighting with Pygments
    - Table of contents generation
    - Custom CSS styling
    - Search functionality
    """
    
    def __init__(self, docs_dir: str = "docs", url_prefix: str = "/docs"):
        """
        Initialize documentation system.
        
        Args:
            docs_dir: Directory containing markdown documentation files
            url_prefix: URL prefix for documentation routes
        """
        self.docs_dir = Path(docs_dir)
        self.url_prefix = url_prefix.rstrip('/')
        self.markdown_processor = None
        self.css_cache = None
        
        if MARKDOWN_AVAILABLE:
            self.markdown_processor = markdown.Markdown(
                extensions=[
                    'codehilite',
                    'toc',
                    'fenced_code',
                    'tables',
                    'attr_list'
                ],
                extension_configs={
                    'codehilite': {
                        'css_class': 'highlight',
                        'use_pygments': True
                    },
                    'toc': {
                        'permalink': True,
                        'permalink_title': 'Link to this section'
                    }
                }
            )
    
    def register_routes(self, app):
        """Register documentation routes with the WolfPy app."""
        
        @app.route(f"{self.url_prefix}")
        @app.route(f"{self.url_prefix}/")
        def docs_index(request):
            """Documentation index page."""
            return self.serve_doc(request, "index")
        
        @app.route(f"{self.url_prefix}/<path:doc_path>")
        def docs_page(request, doc_path):
            """Serve documentation page."""
            return self.serve_doc(request, doc_path)
        
        @app.route(f"{self.url_prefix}/assets/docs.css")
        def docs_css(request):
            """Serve documentation CSS."""
            return Response(
                self.get_docs_css(),
                content_type="text/css"
            )
        
        @app.route(f"{self.url_prefix}/api/search")
        def docs_search(request):
            """Search documentation."""
            query = request.args.get('q', '').strip()
            if not query:
                return Response.json({'results': []})
            
            results = self.search_docs(query)
            return Response.json({'results': results})
    
    def serve_doc(self, request, doc_path: str) -> Response:
        """
        Serve a documentation page.
        
        Args:
            request: HTTP request object
            doc_path: Path to the documentation file
            
        Returns:
            Response object with rendered documentation
        """
        if not MARKDOWN_AVAILABLE:
            return Response(
                "<h1>Documentation Unavailable</h1>"
                "<p>Install markdown and pygments to enable documentation: "
                "<code>pip install markdown pygments</code></p>",
                status=503
            )
        
        # Clean and validate path
        doc_path = unquote(doc_path).strip('/')
        if not doc_path or doc_path == 'index':
            doc_path = 'index'
        
        # Security: prevent directory traversal
        if '..' in doc_path or doc_path.startswith('/'):
            return Response("Invalid documentation path", status=400)
        
        # Find markdown file
        md_file = self.find_markdown_file(doc_path)
        if not md_file:
            return self.render_404(doc_path)
        
        try:
            # Read and process markdown
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Process markdown
            html_content = self.markdown_processor.convert(content)
            toc = getattr(self.markdown_processor, 'toc', '')
            
            # Get navigation
            nav_items = self.get_navigation()
            
            # Render full page
            return Response(self.render_doc_page(
                title=self.extract_title(content, doc_path),
                content=html_content,
                toc=toc,
                navigation=nav_items,
                current_path=doc_path
            ))
            
        except Exception as e:
            return Response(f"Error rendering documentation: {str(e)}", status=500)
    
    def find_markdown_file(self, doc_path: str) -> Optional[Path]:
        """Find markdown file for given path."""
        if not self.docs_dir.exists():
            return None
        
        # Try exact match with .md extension
        md_file = self.docs_dir / f"{doc_path}.md"
        if md_file.exists():
            return md_file
        
        # Try as directory with index.md
        index_file = self.docs_dir / doc_path / "index.md"
        if index_file.exists():
            return index_file
        
        # Try without extension (if file exists)
        direct_file = self.docs_dir / doc_path
        if direct_file.exists() and direct_file.suffix == '.md':
            return direct_file
        
        return None
    
    def get_navigation(self) -> List[Dict]:
        """Get navigation structure from docs directory."""
        if not self.docs_dir.exists():
            return []
        
        nav_items = []
        
        # Scan for markdown files
        for md_file in self.docs_dir.rglob("*.md"):
            rel_path = md_file.relative_to(self.docs_dir)
            
            # Skip hidden files
            if any(part.startswith('.') for part in rel_path.parts):
                continue
            
            # Create navigation item
            url_path = str(rel_path.with_suffix(''))
            if url_path == 'index':
                url_path = ''
            
            title = self.extract_title_from_file(md_file)
            
            nav_items.append({
                'title': title,
                'path': url_path,
                'url': f"{self.url_prefix}/{url_path}" if url_path else self.url_prefix,
                'level': len(rel_path.parts) - 1
            })
        
        # Sort navigation items
        nav_items.sort(key=lambda x: (x['level'], x['path']))
        
        return nav_items
    
    def extract_title(self, content: str, fallback: str) -> str:
        """Extract title from markdown content."""
        # Look for first H1 heading
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        
        # Fallback to path-based title
        return fallback.replace('_', ' ').replace('-', ' ').title()
    
    def extract_title_from_file(self, file_path: Path) -> str:
        """Extract title from markdown file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_lines = f.read(500)  # Read first 500 chars
            return self.extract_title(first_lines, file_path.stem)
        except:
            return file_path.stem.replace('_', ' ').replace('-', ' ').title()
    
    def search_docs(self, query: str) -> List[Dict]:
        """Search documentation files for query."""
        if not self.docs_dir.exists():
            return []
        
        results = []
        query_lower = query.lower()
        
        for md_file in self.docs_dir.rglob("*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Simple text search
                if query_lower in content.lower():
                    rel_path = md_file.relative_to(self.docs_dir)
                    url_path = str(rel_path.with_suffix(''))
                    if url_path == 'index':
                        url_path = ''
                    
                    # Extract context around match
                    lines = content.split('\n')
                    context_lines = []
                    for i, line in enumerate(lines):
                        if query_lower in line.lower():
                            start = max(0, i - 1)
                            end = min(len(lines), i + 2)
                            context_lines.extend(lines[start:end])
                            break
                    
                    results.append({
                        'title': self.extract_title(content, md_file.stem),
                        'path': url_path,
                        'url': f"{self.url_prefix}/{url_path}" if url_path else self.url_prefix,
                        'context': ' '.join(context_lines)[:200] + '...'
                    })
            except:
                continue
        
        return results[:10]  # Limit results

    def render_doc_page(self, title: str, content: str, toc: str,
                       navigation: List[Dict], current_path: str) -> str:
        """Render complete documentation page."""
        nav_html = self.render_navigation(navigation, current_path)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - WolfPy Documentation</title>
    <link rel="stylesheet" href="{self.url_prefix}/assets/docs.css">
    <link rel="icon" type="image/x-icon" href="/static/favicon.ico">
</head>
<body>
    <div class="docs-container">
        <nav class="docs-sidebar">
            <div class="docs-header">
                <h2>📚 Documentation</h2>
                <div class="search-box">
                    <input type="text" id="search-input" placeholder="Search docs...">
                    <div id="search-results"></div>
                </div>
            </div>
            {nav_html}
        </nav>

        <main class="docs-content">
            <div class="docs-page">
                {toc if toc else ''}
                <div class="docs-body">
                    {content}
                </div>
            </div>
        </main>
    </div>

    <script>
        // Simple search functionality
        const searchInput = document.getElementById('search-input');
        const searchResults = document.getElementById('search-results');

        let searchTimeout;
        searchInput.addEventListener('input', function() {{
            clearTimeout(searchTimeout);
            const query = this.value.trim();

            if (query.length < 2) {{
                searchResults.innerHTML = '';
                searchResults.style.display = 'none';
                return;
            }}

            searchTimeout = setTimeout(() => {{
                fetch(`{self.url_prefix}/api/search?q=${{encodeURIComponent(query)}}`)
                    .then(response => response.json())
                    .then(data => {{
                        if (data.results.length > 0) {{
                            const html = data.results.map(result =>
                                `<div class="search-result">
                                    <a href="${{result.url}}">${{result.title}}</a>
                                    <p>${{result.context}}</p>
                                </div>`
                            ).join('');
                            searchResults.innerHTML = html;
                            searchResults.style.display = 'block';
                        }} else {{
                            searchResults.innerHTML = '<div class="no-results">No results found</div>';
                            searchResults.style.display = 'block';
                        }}
                    }})
                    .catch(() => {{
                        searchResults.innerHTML = '<div class="search-error">Search error</div>';
                        searchResults.style.display = 'block';
                    }});
            }}, 300);
        }});

        // Hide search results when clicking outside
        document.addEventListener('click', function(e) {{
            if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {{
                searchResults.style.display = 'none';
            }}
        }});
    </script>
</body>
</html>"""

    def render_navigation(self, navigation: List[Dict], current_path: str) -> str:
        """Render navigation HTML."""
        if not navigation:
            return '<p class="no-docs">No documentation found</p>'

        html = '<ul class="docs-nav">'

        for item in navigation:
            active_class = ' class="active"' if item['path'] == current_path else ''
            indent_style = f' style="margin-left: {item["level"] * 20}px;"' if item['level'] > 0 else ''

            html += f'''
                <li{indent_style}>
                    <a href="{item['url']}"{active_class}>{item['title']}</a>
                </li>
            '''

        html += '</ul>'
        return html

    def render_404(self, doc_path: str) -> Response:
        """Render 404 page for missing documentation."""
        nav_items = self.get_navigation()
        nav_html = self.render_navigation(nav_items, '')

        content = f"""
        <h1>📄 Documentation Not Found</h1>
        <p>The documentation page <code>{doc_path}</code> could not be found.</p>
        <h2>Available Documentation:</h2>
        {nav_html if nav_items else '<p>No documentation available.</p>'}
        """

        html = self.render_doc_page(
            title="Page Not Found",
            content=content,
            toc="",
            navigation=nav_items,
            current_path=""
        )

        return Response(html, status=404)

    def get_docs_css(self) -> str:
        """Get documentation CSS styles."""
        if self.css_cache:
            return self.css_cache

        # Generate Pygments CSS
        pygments_css = ""
        if MARKDOWN_AVAILABLE:
            try:
                formatter = HtmlFormatter(style='default', cssclass='highlight')
                pygments_css = formatter.get_style_defs()
            except:
                pass

        css = f"""
/* WolfPy Documentation Styles */
* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: #333;
    background: #f8f9fa;
}}

.docs-container {{
    display: flex;
    min-height: 100vh;
}}

.docs-sidebar {{
    width: 280px;
    background: #fff;
    border-right: 1px solid #e1e5e9;
    position: fixed;
    height: 100vh;
    overflow-y: auto;
    z-index: 100;
}}

.docs-header {{
    padding: 20px;
    border-bottom: 1px solid #e1e5e9;
}}

.docs-header h2 {{
    color: #2c3e50;
    margin-bottom: 15px;
}}

.search-box {{
    position: relative;
}}

.search-box input {{
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
}}

#search-results {{
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: white;
    border: 1px solid #ddd;
    border-top: none;
    border-radius: 0 0 4px 4px;
    max-height: 300px;
    overflow-y: auto;
    display: none;
    z-index: 1000;
}}

.search-result {{
    padding: 10px;
    border-bottom: 1px solid #eee;
}}

.search-result:last-child {{
    border-bottom: none;
}}

.search-result a {{
    color: #007bff;
    text-decoration: none;
    font-weight: 500;
}}

.search-result p {{
    font-size: 12px;
    color: #666;
    margin-top: 4px;
}}

.no-results, .search-error {{
    padding: 10px;
    color: #666;
    font-size: 14px;
}}

.docs-nav {{
    list-style: none;
    padding: 20px 0;
}}

.docs-nav li {{
    margin: 0;
}}

.docs-nav a {{
    display: block;
    padding: 8px 20px;
    color: #555;
    text-decoration: none;
    transition: all 0.2s;
}}

.docs-nav a:hover {{
    background: #f8f9fa;
    color: #007bff;
}}

.docs-nav a.active {{
    background: #007bff;
    color: white;
}}

.docs-content {{
    flex: 1;
    margin-left: 280px;
    padding: 40px;
    max-width: calc(100% - 280px);
}}

.docs-page {{
    max-width: 800px;
    background: white;
    padding: 40px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}}

.docs-body h1 {{
    color: #2c3e50;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 2px solid #007bff;
}}

.docs-body h2 {{
    color: #34495e;
    margin: 30px 0 15px 0;
}}

.docs-body h3 {{
    color: #555;
    margin: 25px 0 10px 0;
}}

.docs-body p {{
    margin-bottom: 15px;
}}

.docs-body ul, .docs-body ol {{
    margin-bottom: 15px;
    padding-left: 30px;
}}

.docs-body li {{
    margin-bottom: 5px;
}}

.docs-body code {{
    background: #f8f9fa;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Monaco', 'Consolas', monospace;
    font-size: 0.9em;
}}

.docs-body pre {{
    background: #f8f9fa;
    padding: 15px;
    border-radius: 5px;
    overflow-x: auto;
    margin: 15px 0;
    border-left: 4px solid #007bff;
}}

.docs-body pre code {{
    background: none;
    padding: 0;
}}

.docs-body blockquote {{
    border-left: 4px solid #ddd;
    padding-left: 15px;
    margin: 15px 0;
    color: #666;
    font-style: italic;
}}

.docs-body table {{
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
}}

.docs-body th, .docs-body td {{
    padding: 10px;
    border: 1px solid #ddd;
    text-align: left;
}}

.docs-body th {{
    background: #f8f9fa;
    font-weight: 600;
}}

.toc {{
    background: #f8f9fa;
    padding: 15px;
    border-radius: 5px;
    margin-bottom: 30px;
}}

.toc ul {{
    list-style: none;
    padding-left: 0;
}}

.toc ul ul {{
    padding-left: 20px;
}}

.toc a {{
    color: #007bff;
    text-decoration: none;
}}

.no-docs {{
    color: #666;
    font-style: italic;
    padding: 20px;
}}

/* Pygments syntax highlighting */
{pygments_css}

/* Responsive design */
@media (max-width: 768px) {{
    .docs-sidebar {{
        transform: translateX(-100%);
        transition: transform 0.3s;
    }}

    .docs-content {{
        margin-left: 0;
        max-width: 100%;
        padding: 20px;
    }}

    .docs-page {{
        padding: 20px;
    }}
}}
"""

        self.css_cache = css
        return css
