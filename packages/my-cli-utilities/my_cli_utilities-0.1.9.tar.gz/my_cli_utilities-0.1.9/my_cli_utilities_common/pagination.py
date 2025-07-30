"""
Pagination utilities for CLI tools.
Provides reusable pagination functionality for displaying large lists of items.
"""

import logging
import sys
from typing import List, Callable, Any

logger = logging.getLogger('pagination')


def _get_single_char() -> str:
    """Get a single character input without requiring Enter."""
    import os
    
    try:
        # Check platform and use appropriate implementation
        if os.name == 'nt':  # Windows
            import msvcrt
            char = msvcrt.getch().decode('utf-8')
            return char
        else:  # Unix/Linux/macOS (posix systems)
            import termios
            import tty
            
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                char = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return char
    except Exception:
        # Fallback to regular input if single char doesn't work
        fallback_input = input()
        return fallback_input.strip().lower()[:1] if fallback_input.strip() else ""


def paginated_display(
    items: List[Any], 
    display_func: Callable[[Any, int], None], 
    title: str = "", 
    page_size: int = 5,
    display_width: int = 50
) -> bool:
    """
    Display items with pagination support.
    
    Args:
        items: List of items to display
        display_func: Function to display each item, receives (item, index)
        title: Optional title to display at the top
        page_size: Number of items per page (default: 5)
        display_width: Width for separator lines (default: 50)
    
    Returns:
        bool: True if user completed viewing all items, False if quit early
    """
    if not items:
        logger.warning("No items to display")
        return True
        
    total_items = len(items)
    current_index = 0
    
    if title:
        print(f"\n{title}")
        print("=" * display_width)
    
    while current_index < total_items:
        # Display current page
        end_index = min(current_index + page_size, total_items)
        current_page_items = items[current_index:end_index]
        
        for i, item in enumerate(current_page_items):
            display_func(item, current_index + i + 1)
        
        current_index = end_index
        
        # Check if there are more items
        if current_index < total_items:
            remaining = total_items - current_index
            current_page = (current_index - 1) // page_size + 1
            total_pages = (total_items + page_size - 1) // page_size
            
            print(f"\n--- Page {current_page}/{total_pages} - Showing {end_index}/{total_items} items ---")
            print(f"--- {remaining} more items remaining ---")
            
            try:
                print("Press Enter to continue, 'q' to quit: ", end='', flush=True)
                response = _get_single_char().lower()
                
                if response == 'q':
                    print("q")  # Echo the character
                    logger.info("Display stopped by user")
                    return False
                elif response == '\r' or response == '\n' or response == '':
                    print()  # Just print newline for Enter
                else:
                    print()  # Print newline for any other character and continue
            except (KeyboardInterrupt, EOFError):
                print("\nDisplay stopped by user")
                return False
        else:
            print(f"\n--- All {total_items} items displayed ---")
            return True
    
    return True


def simple_paginated_display(
    items: List[Any], 
    display_func: Callable[[Any, int], None], 
    page_size: int = 5
) -> bool:
    """
    Simplified pagination without titles or separators.
    
    Args:
        items: List of items to display
        display_func: Function to display each item, receives (item, index)
        page_size: Number of items per page (default: 5)
    
    Returns:
        bool: True if user completed viewing all items, False if quit early
    """
    return paginated_display(items, display_func, "", page_size, 0) 