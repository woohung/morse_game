"""
Configuration settings for the Morse Code Decoder application.
"""
import os
from pathlib import Path

# GPIO Configuration
GPIO_PIN = 17  # Default GPIO pin for the telegraph key (BCM numbering)
PULL_UP_DOWN = 'pull_up'  # 'pull_up' or 'pull_down' depending on wiring


# Morse timing model
DIT = 0.2

DOT_DURATION = DIT
DASH_DURATION = 2 * DIT

LETTER_GAP = 5 * DIT
WORD_GAP   = 7 * DIT

DEBOUNCE_TIME = 0

# Game timing
WORD_TIME_LIMIT = 10.0  # Base time limit per word in seconds
TIME_PER_LETTER = 3.0   # Additional time per letter
O_LETTER_BONUS = 2.0    # Extra time for each 'O' letter (--- is long)

# Difficulty settings
DIFFICULTY_SETTINGS = {
    'easy': {
        'word_time_limit': 15.0,  # More base time for easy mode
        'time_per_letter': 2.5,   # Less time pressure per letter
        'o_letter_bonus': 1.5,    # Smaller bonus for O letters
        'game_duration': 120.0    # 2 minutes for easy mode
    },
    'hard': {
        'word_time_limit': 8.0,   # Less base time for hard mode
        'time_per_letter': 2.0,   # More time pressure per letter
        'o_letter_bonus': 1.0,    # Minimal bonus for O letters
        'game_duration': 90.0,     # 1.5 minutes for hard mode
        'time_bonus_every_words': 3,  # Bonus time every N words
        'time_bonus_amount': 10.0     # Bonus time amount in seconds
    }
}


# Display settings - will be set based on actual display resolution
# These will be updated at runtime to match the display
SCREEN_INFO = None  # Will store display info
SCREEN_WIDTH = 1920  # Default, will be updated
SCREEN_HEIGHT = 1080  # Default, will be updated
FONT_SIZE = 48  # Base font size, will be scaled

# Typography settings
LETTER_SPACING_MULTIPLIER = 0.6  # Spacing between letters as fraction of font size (increased)
WORD_PADDING = 20  # Padding around word display

# Colors (RGB) - Retro telegraph theme
COLORS = {
    'background': (15, 15, 25),        # Dark blue-black like old screens
    'text': (255, 220, 150),           # Warm amber like old monitors
    'title': (255, 235, 180),          # Light amber for titles
    'menu_header': (200, 180, 120),       # Darker amber for menu headers
    'morse': (255, 200, 100),          # Golden amber for Morse input
    'decoded': (200, 255, 150),        # Green phosphor like old terminals
    'hint': (180, 180, 150),           # Muted amber for hints
    'wrong': (255, 120, 120),          # Red phosphor for errors
    'correct': (120, 255, 120),        # Bright green phosphor for success
    'neon_glow_orange': (180, 120, 60),   # Amber glow
    'neon_glow_green': (60, 140, 60),      # Green phosphor glow
    'neon_glow_red': (140, 60, 60),        # Red phosphor glow
    
    # Unified menu color palette - Retro terminal green phosphor
    'menu_selected_bg': (40, 120, 60),       # Rich green phosphor background for selected items
    'menu_selected_text': (200, 255, 200),     # Bright green phosphor text for selected items
    'menu_selected_border': (100, 255, 120),  # Bright green border for selected items
    'menu_unselected_bg': (20, 60, 30),        # Dark green background for unselected items
    'menu_unselected_text': (150, 200, 150),   # Muted green text for unselected items
    'menu_numbered_bg': (25, 70, 35),         # Background for numbered menu items
    'menu_border_dark': (30, 80, 40),          # Dark green border
}

# File paths
BASE_DIR = Path(__file__).parent
RESULTS_FILE = str(BASE_DIR / 'morse_results.json')

# Ensure results directory exists
os.makedirs(os.path.dirname(RESULTS_FILE), exist_ok=True)

def init_display():
    """Initialize display settings based on actual display resolution."""
    global SCREEN_WIDTH, SCREEN_HEIGHT, FONT_SIZE, SCREEN_INFO
    
    try:
        import pygame
        pygame.display.init()
        
        # Get the primary display info
        SCREEN_INFO = pygame.display.Info()
        SCREEN_WIDTH = SCREEN_INFO.current_w
        SCREEN_HEIGHT = SCREEN_INFO.current_h
        
        # Scale font size based on display resolution
        FONT_SIZE = max(24, int(min(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.03))
        
        print(f"Display initialized: {SCREEN_WIDTH}x{SCREEN_HEIGHT}, Font size: {FONT_SIZE}")
        
    except Exception as e:
        print(f"Error initializing display: {e}")
        print("Using default display settings")

# Initialize display settings when this module is imported
init_display()
