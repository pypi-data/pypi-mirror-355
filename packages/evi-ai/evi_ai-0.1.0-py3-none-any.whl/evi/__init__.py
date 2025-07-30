"""
evi - A flexible multi-agent framework generator
"""

__version__ = "0.1.0"

from .core import EviGenerator
from .providers import BaseProvider, create_provider, OpenAIProvider, GeminiProvider
from .frameworks import BaseFramework, create_framework, CrewAIFramework, LangGraphFramework, ReActFramework
