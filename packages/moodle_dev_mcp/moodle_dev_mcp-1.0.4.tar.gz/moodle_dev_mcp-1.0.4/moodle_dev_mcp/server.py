#!/usr/bin/env python3
"""
Moodle Developer Documentation MCP Server

This server provides tools to fetch and search Moodle developer documentation
from moodledev.io with dynamic version support and API focus.
/// script
requires-python = ">=3.8"
dependencies = [
    "mcp",
    "aiohttp",
    "beautifulsoup4",
]
///
"""

import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin
import aiohttp
from bs4 import BeautifulSoup, Tag
from pydantic import AnyUrl
import sys

# MCP Server imports
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("moodle_dev_docs_mcp")

class MoodleDevDocsServer:
    def __init__(self):
        self.base_url = "https://moodledev.io"
        self.session: Optional[aiohttp.ClientSession] = None
        self.default_version = "5.0"

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_available_versions(self) -> List[str]:
        """Get available Moodle versions from the documentation site."""
        if not self.session:
            raise RuntimeError("Session not initialized")

        try:
            # Try to get version info from the docs root
            async with self.session.get(f"{self.base_url}/docs/") as response:
                if response.status != 200:
                    return [self.default_version]  # Fallback

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Look for version links or dropdown
                versions = []
                version_links = soup.find_all('a', href=re.compile(r'/docs/\d+\.\d+'))

                for link in version_links:
                    if isinstance(link, Tag):
                        href = link.get('href')
                        if href and isinstance(href, str):
                            version_match = re.search(r'/docs/(\d+\.\d+)', href)
                            if version_match:
                                versions.append(version_match.group(1))

                # Remove duplicates and sort
                versions = sorted(list(set(versions)), reverse=True)
                return versions if versions else [self.default_version]

        except Exception as e:
            logger.error(f"Error getting available versions: {e}")
            return [self.default_version]

    async def get_api_structure(self, version: str) -> Dict[str, Any]:
        """Get the API documentation structure for a specific version."""
        if not self.session:
            raise RuntimeError("Session not initialized")

        api_url = f"{self.base_url}/docs/{version}/apis"

        try:
            async with self.session.get(api_url) as response:
                if response.status != 200:
                    return {'error': f'Version {version} not found or APIs not available'}

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Extract navigation or content structure
                apis = []

                # Look for main content area
                content = soup.find('main') or soup.find('div', class_='content') or soup.find('article')
                if content and isinstance(content, Tag):
                    # Find API links
                    api_links = content.find_all('a', href=re.compile(r'/docs/' + re.escape(version) + r'/apis/'))

                    for link in api_links:
                        if isinstance(link, Tag):
                            title = link.get_text(strip=True)
                            href = link.get('href')
                            if href and isinstance(href, str):
                                url = urljoin(self.base_url, href)

                                # Get description if available
                                description = ""
                                parent = link.find_parent(['li', 'div', 'p'])
                                if parent and isinstance(parent, Tag):
                                    desc_text = parent.get_text(strip=True)
                                    if desc_text != title and len(desc_text) > len(title):
                                        description = desc_text.replace(title, '').strip()

                                apis.append({
                                    'title': title,
                                    'url': url,
                                    'description': description
                                })

                # Also look for headings that might indicate API sections
                sections = []
                if content and isinstance(content, Tag):
                    headings = content.find_all(['h1', 'h2', 'h3', 'h4'])
                    for heading in headings:
                        if isinstance(heading, Tag) and heading.name:
                            sections.append({
                                'level': int(heading.name[1]),
                                'title': heading.get_text(strip=True)
                            })

                return {
                    'version': version,
                    'base_url': api_url,
                    'apis': apis,
                    'sections': sections
                }

        except Exception as e:
            logger.error(f"Error getting API structure: {e}")
            return {'error': str(e)}

    async def search_documentation(self, query: str, version: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search Moodle developer documentation for a specific query."""
        if not self.session:
            raise RuntimeError("Session not initialized")

        if not version:
            version = self.default_version

        # Try to search within the version docs
        search_url = f"{self.base_url}/docs/{version}"

        try:
            # First, get the main page to understand the structure
            async with self.session.get(search_url) as response:
                if response.status != 200:
                    return []

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                results = []

                # Look for links that might match our query
                all_links = soup.find_all('a', href=re.compile(r'/docs/' + re.escape(version)))

                for link in all_links:
                    if isinstance(link, Tag):
                        link_text = link.get_text(strip=True).lower()
                        href = link.get('href')

                        # Simple text matching
                        if href and isinstance(href, str) and (query.lower() in link_text or query.lower() in href.lower()):
                            title = link.get_text(strip=True)
                            url = urljoin(self.base_url, href)

                            # Try to get context
                            context = ""
                            parent = link.find_parent(['li', 'div', 'p', 'section'])
                            if parent and isinstance(parent, Tag):
                                context = parent.get_text(strip=True)[:200]

                            results.append({
                                'title': title,
                                'url': url,
                                'context': context,
                                'relevance': 'high' if query.lower() in title.lower() else 'medium'
                            })

                            if len(results) >= limit:
                                break

                return results

        except Exception as e:
            logger.error(f"Error searching documentation: {e}")
            return []

    async def fetch_page_content(self, url: str) -> Dict[str, Any]:
        """Fetch the content of a specific Moodle developer documentation page."""
        if not self.session:
            raise RuntimeError("Session not initialized")

        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return {'error': f'HTTP {response.status}', 'content': ''}

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Extract title
                title_elem = soup.find('h1') or soup.find('title')
                title = title_elem.get_text(strip=True) if title_elem and isinstance(title_elem, Tag) else "Unknown Title"

                # Extract main content - try different selectors for different layouts
                content_elem = (
                    soup.find('main') or
                    soup.find('article') or
                    soup.find('div', class_='content') or
                    soup.find('div', {'id': 'content'}) or
                    soup.find('div', class_='markdown-body')
                )

                if not content_elem:
                    # Fallback to body but exclude nav/header/footer
                    content_elem = soup.find('body')
                    if content_elem and isinstance(content_elem, Tag):
                        for elem in content_elem.find_all(['nav', 'header', 'footer', 'aside']):
                            if isinstance(elem, Tag):
                                elem.decompose()

                if not content_elem or not isinstance(content_elem, Tag):
                    return {'error': 'Content not found', 'content': ''}

                # Remove unwanted elements
                for elem in content_elem.find_all(['script', 'style', 'nav', 'header', 'footer']):
                    if isinstance(elem, Tag):
                        elem.decompose()

                # Extract text content
                content = content_elem.get_text(separator='\n', strip=True)

                # Extract code blocks
                code_blocks = []
                # Look for pre elements first, then check their code children
                for pre in content_elem.find_all('pre'):
                    if isinstance(pre, Tag):
                        code_text = pre.get_text(strip=True)
                        if len(code_text) > 20:  # Only include substantial code blocks
                            language = ""

                            # Try to detect language from code element inside pre
                            code_elem = pre.find('code')
                            if code_elem and isinstance(code_elem, Tag):
                                classes = code_elem.get('class')
                                if classes and isinstance(classes, list):
                                    for cls in classes:
                                        if isinstance(cls, str) and cls.startswith('language-'):
                                            language = cls.replace('language-', '')
                                            break

                            # If no code element, check pre element itself
                            if not language:
                                classes = pre.get('class')
                                if classes and isinstance(classes, list):
                                    for cls in classes:
                                        if isinstance(cls, str) and cls.startswith('language-'):
                                            language = cls.replace('language-', '')
                                            break

                            code_blocks.append({
                                'language': language,
                                'code': code_text
                            })

                # Extract headings for structure
                headings = []
                for heading in content_elem.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                    if isinstance(heading, Tag) and heading.name:
                        level = int(heading.name[1])
                        text = heading.get_text(strip=True)
                        headings.append({'level': level, 'text': text})

                # Extract version from URL
                version_match = re.search(r'/docs/(\d+\.\d+)/', url)
                version = version_match.group(1) if version_match else "unknown"

                return {
                    'title': title,
                    'url': url,
                    'version': version,
                    'content': content,
                    'headings': headings,
                    'code_blocks': code_blocks,
                    'word_count': len(content.split())
                }

        except Exception as e:
            logger.error(f"Error fetching page content: {e}")
            return {'error': str(e), 'content': ''}

    async def get_api_categories(self, version: Optional[str] = None) -> Dict[str, Any]:
        """Get available API categories for a specific version."""
        if not version:
            version = self.default_version

        # This will use the existing API structure method
        return await self.get_api_structure(version)


# Initialize the MCP server
app = Server("moodle_dev_docs_server")
moodle_server = MoodleDevDocsServer()


@app.list_resources()
async def handle_list_resources() -> List[Resource]:
    """List available Moodle developer documentation resources."""
    return [
        Resource(
            uri=AnyUrl("https://moodledev.io/versions"),
            name="Available Moodle Versions",
            description="List of available Moodle versions in the developer documentation",
            mimeType="application/json",
        ),
        Resource(
            uri=AnyUrl("https://moodledev.io/api-categories"),
            name="API Categories",
            description="Available API categories in Moodle developer documentation",
            mimeType="application/json",
        ),
    ]


@app.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """Read a specific resource."""
    async with moodle_server:
        uri_str = str(uri)
        if uri_str == "https://moodledev.io/versions":
            versions = await moodle_server.get_available_versions()
            return json.dumps({"versions": versions, "default": moodle_server.default_version}, indent=2)
        elif uri_str == "https://moodledev.io/api-categories":
            categories = await moodle_server.get_api_categories()
            return json.dumps(categories, indent=2)
        else:
            raise ValueError(f"Unknown resource: {uri_str}")


@app.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available Moodle developer documentation tools."""
    return [
        Tool(
            name="get_versions",
            description="Get available Moodle versions in the developer documentation",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="search_docs",
            description="Search Moodle developer documentation for specific topics or APIs",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for documentation (e.g., 'database API', 'plugin development')",
                    },
                    "version": {
                        "type": "string",
                        "description": "Specific Moodle version to search (optional, defaults to latest)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_api_structure",
            description="Get the API documentation structure for a specific Moodle version",
            inputSchema={
                "type": "object",
                "properties": {
                    "version": {
                        "type": "string",
                        "description": "Moodle version (e.g., '4.1', '4.2') - defaults to latest if not specified",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="fetch_page",
            description="Fetch full content of a specific Moodle developer documentation page",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Full URL of the documentation page to fetch",
                    },
                },
                "required": ["url"],
            },
        ),
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls for Moodle developer documentation."""
    async with moodle_server:
        try:
            if name == "get_versions":
                versions = await moodle_server.get_available_versions()
                result = {
                    "available_versions": versions,
                    "default_version": moodle_server.default_version,
                    "base_url": moodle_server.base_url
                }
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            elif name == "search_docs":
                query = arguments.get("query", "")
                if not query:
                    return [TextContent(type="text", text="Error: Query parameter is required")]

                version = arguments.get("version")
                limit = arguments.get("limit", 10)

                results = await moodle_server.search_documentation(query, version, limit)

                if not results:
                    return [TextContent(type="text", text=f"No results found for query: {query}")]

                # Format results nicely
                formatted_results = {
                    "query": query,
                    "version": version or moodle_server.default_version,
                    "results_count": len(results),
                    "results": results
                }

                return [TextContent(type="text", text=json.dumps(formatted_results, indent=2))]

            elif name == "get_api_structure":
                version = arguments.get("version", moodle_server.default_version)
                structure = await moodle_server.get_api_structure(version)
                return [TextContent(type="text", text=json.dumps(structure, indent=2))]

            elif name == "fetch_page":
                url = arguments.get("url", "")
                if not url:
                    return [TextContent(type="text", text="Error: URL parameter is required")]

                # Validate URL
                if not url.startswith(moodle_server.base_url):
                    return [TextContent(type="text", text=f"Error: URL must be from {moodle_server.base_url}")]

                content = await moodle_server.fetch_page_content(url)

                if 'error' in content:
                    return [TextContent(type="text", text=f"Error fetching page: {content['error']}")]

                # Format the content nicely
                formatted_content = {
                    "title": content["title"],
                    "url": content["url"],
                    "version": content["version"],
                    "word_count": content["word_count"],
                    "headings": content["headings"],
                    "code_blocks_count": len(content["code_blocks"]),
                    "content": content["content"][:2000] + "..." if len(content["content"]) > 2000 else content["content"],
                    "code_blocks": content["code_blocks"][:5]  # Limit code blocks shown
                }

                return [TextContent(type="text", text=json.dumps(formatted_content, indent=2))]

            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

        except Exception as e:
            logger.error(f"Error in tool {name}: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Main function to run the MCP server."""
    # Asyncio servers have a bug where they don't flush stdout on exit
    # which can result in messages being lost
    import atexit
    atexit.register(lambda: sys.stdout.flush())

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="moodle_dev_docs_server",
                server_version="0.1.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
