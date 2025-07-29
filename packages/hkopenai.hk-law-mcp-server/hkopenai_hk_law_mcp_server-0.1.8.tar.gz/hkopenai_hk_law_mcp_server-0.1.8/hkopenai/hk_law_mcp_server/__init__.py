"""Hong Kong law and security MCP Server package."""
from .app import main
from .foreign_domestic_helpers import get_fdh_statistics

__version__ = "0.1.0"
__all__ = ['main', 'get_fdh_statistics']
