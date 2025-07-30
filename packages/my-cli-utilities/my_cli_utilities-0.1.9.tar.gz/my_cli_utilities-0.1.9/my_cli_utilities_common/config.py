"""
Common configuration management utilities.
Provides base configuration classes and utilities for CLI tools.
"""

import os
import tempfile
from typing import Optional, Dict, Any


class BaseConfig:
    """Base configuration class with common settings."""
    
    # Display settings
    DISPLAY_WIDTH = 50
    PAGE_SIZE = 5
    
    # Emoji and formatting
    EMOJI_SEARCH = "🔍"
    EMOJI_SUCCESS = "✅"
    EMOJI_ERROR = "❌"
    EMOJI_WARNING = "⚠️"
    EMOJI_INFO = "ℹ️"
    
    @classmethod
    def get_temp_dir(cls) -> str:
        """Get system temporary directory."""
        return tempfile.gettempdir()
    
    @classmethod
    def get_cache_file(cls, filename: str) -> str:
        """Get full path for a cache file in temp directory."""
        return os.path.join(cls.get_temp_dir(), filename)


class DisplayUtils:
    """Utilities for consistent display formatting."""
    
    @staticmethod
    def format_title(title: str, width: int = 50) -> str:
        """Format a title with separator lines."""
        return f"\n{title}\n{'=' * width}"
    
    @staticmethod
    def format_search_info(query: str, extra_info: Optional[Dict[str, str]] = None) -> None:
        """Display standardized search information."""
        print(f"\n🔍 Searching...")
        print(f"   Query: '{query}'")
        
        if extra_info:
            for key, value in extra_info.items():
                print(f"   {key}: {value}")
    
    @staticmethod
    def format_success(message: str) -> None:
        """Display success message."""
        print(f"   ✅ {message}")
    
    @staticmethod
    def format_error(message: str) -> None:
        """Display error message."""
        print(f"   ❌ {message}")
    
    @staticmethod
    def format_info(message: str) -> None:
        """Display info message."""
        print(f"   ℹ️  {message}")


class LoggingUtils:
    """Utilities for consistent logging setup."""
    
    @staticmethod
    def setup_logger(name: str, level: str = 'INFO') -> 'logging.Logger':
        """Setup a standard logger with consistent formatting."""
        import logging
        
        # Convert string level to logging constant
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        
        logging.basicConfig(
            level=numeric_level, 
            format='%(levelname)s: %(message)s'
        )
        
        return logging.getLogger(name)


class ValidationUtils:
    """Common validation utilities."""
    
    @staticmethod
    def is_numeric_string(value) -> bool:
        """Check if value is numeric (int or digit string)."""
        return isinstance(value, int) or (isinstance(value, str) and value.isdigit())
    
    @staticmethod
    def normalize_phone_number(phone_number) -> str:
        """Normalize phone number by adding + prefix if missing."""
        phone_str = str(phone_number)
        return phone_str if phone_str.startswith("+") else "+" + phone_str
    
    @staticmethod
    def truncate_text(text: str, max_length: int) -> str:
        """Truncate text to specified length with ellipsis."""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..." 
    
    @staticmethod
    def format_account_type_display(account_type: str, max_line_length: int = 75) -> str:
        """Format account type for better display with line breaks when too long."""
        if len(account_type) <= max_line_length:
            return account_type
        
        # Simple line wrapping: break at max_line_length and indent continuation
        lines = []
        remaining = account_type
        
        while len(remaining) > max_line_length:
            # Take the first max_line_length characters
            lines.append(remaining[:max_line_length])
            # Keep the rest with indentation
            remaining = '   ' + remaining[max_line_length:]
        
        # Add the final part
        if remaining:
            lines.append(remaining)
        
        return '\n'.join(lines)