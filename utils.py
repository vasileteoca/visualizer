# utils.py
"""
Utility functions for the water visualizer project.
Add shared logic here if needed.
"""

def clamp(value, min_value, max_value):
    """
    Clamp a numeric value between min_value and max_value.
    """
    return max(min_value, min(value, max_value))
