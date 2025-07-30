"""
Noble TLS Profiles Module

This module provides custom TLS profiles and identifiers for Noble TLS.
It includes functionality to load profiles from tls.peet.ws JSON files
and use them with custom client identifiers.
"""

# Use try-except to handle both package and direct imports
try:
    # Try relative imports first (when used as a package)
    from .profiles import ProfileLoader, load_profile, list_profiles
    from ..utils.custom_identifiers import CustomClient, CustomClientManager, custom_client_manager
    from .session_factory import create_session, list_all_identifiers
except ImportError:
    # Fall back to direct imports (when imported directly)
    from .profiles import ProfileLoader, load_profile, list_profiles
    from ..utils.custom_identifiers import CustomClient, CustomClientManager, custom_client_manager
    from .session_factory import create_session, list_all_identifiers

__all__ = [
    # Core classes
    'ProfileLoader',
    'CustomClient', 
    'CustomClientManager',
    
    # Factory functions
    'create_session',
    
    # Convenience functions
    'load_profile',
    'list_profiles', 
    'list_all_identifiers',
    
    # Global instances
    'custom_client_manager'
]

# Version info
__version__ = "1.0.0"
__author__ = "Noble TLS Team"
__description__ = "Custom TLS profiles and identifiers for Noble TLS" 