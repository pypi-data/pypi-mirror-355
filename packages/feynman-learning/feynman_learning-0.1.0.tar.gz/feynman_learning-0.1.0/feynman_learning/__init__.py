"""
Feynman Learning - AI-powered learning using the Feynman Technique
"""

from .core import FeynmanLearner
from .ai_explainer import AIExplainer, OpenAICompatibleProvider
from .session_manager import LearningSession, SessionManager
from .config import ConfigManager, get_config_manager, reset_config_manager

__version__ = "0.1.0"
__all__ = ["FeynmanLearner", "AIExplainer", "OpenAICompatibleProvider", "LearningSession", "SessionManager", "ConfigManager", "get_config_manager", "reset_config_manager"]