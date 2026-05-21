"""
Keyboard Shortcuts Configuration
You can modify the keys here to change how the app responds to keyboard input.
"""

# POS (Sales Tab) Shortcuts
SALES_KEYS = {
    "increment_qty": ["Up"],                        # Up Arrow to increase
    "decrement_qty": ["Down"],                      # Down Arrow to decrease
    "confirm_sale": ["Control_L", "Control_R"],     # Left or Right Control keys
    "clear_card": ["Escape"],                       # Escape to cancel/clear current product
    "focus_search": ["f", "F"],                     # Press F to focus search bar
}

# Global Shortcuts (can be added here later)
GLOBAL_KEYS = {
    "switch_sales": "F1",
    "switch_products": "F2",
    "switch_analytics": "F3",
    "switch_notifications": "F4",
    "switch_settings": "F5",
}
