"""
Configuration settings for the Morse Code Decoder application.
"""
import os
from pathlib import Path

# GPIO Configuration
GPIO_PIN = 17  # Default GPIO pin for the telegraph key (BCM numbering)
PULL_UP_DOWN = 'pull_up'  # 'pull_up' or 'pull_down' depending on wiring

# Megohmmeter configuration
MEGOHMMETER_PIN = 13  # GPIO pin for megohmmeter needle control (PWM) - основная катушка
MEGOHMMETER_PULLBACK_PIN = 12  # GPIO pin for pullback coil (PWM) - оттягивающая катушка
MEGOHMMETER_PWM_FREQUENCY = 1000  # PWM frequency for smooth needle movement
MEGOHMMETER_SMOOTH_TRANSITION = True  # Enable smooth needle transitions

# Megohmmeter needle behavior
MEGOHMMETER_BASELINE_FORCE = 0.05  # Pullback coil strength when key is released (reduced)
MEGOHMMETER_DOT_AMPLITUDE = 0.6    # Amplitude for dots (increased to overcome pullback)
MEGOHMMETER_DASH_AMPLITUDE = 1.0   # Amplitude for dashes (maximum to overcome pullback)


# Morse timing model
DIT = 0.16

DOT_DURATION = DIT
DASH_DURATION = 3 * DIT

LETTER_GAP = 2 * DASH_DURATION
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
        'time_bonus_amount': 15.0     # Bonus time amount in seconds
    }
}


# Display settings - optimized for Raspberry Pi 4 performance
# These will be updated at runtime to match the display
SCREEN_INFO = None  # Will store display info
SCREEN_WIDTH = 1024  # Optimized resolution for RPi 4
SCREEN_HEIGHT = 768   # Optimized resolution for RPi 4 (corrected from 728)
FONT_SIZE = 48  # Base font size, will be scaled

# Scaling for fullscreen mode on high-res displays
FULLSCREEN_SCALE = 1.0  # Will be calculated based on actual display resolution
USE_HARDWARE_ACCELERATION = True  # Enable hardware acceleration on RPi

# Performance settings for Raspberry Pi 4
TARGET_FPS = 20  # Reduced from 30 for better performance on RPi 4
ENABLE_CRT_EFFECT = True  # Can be disabled for performance
ENABLE_NEON_EFFECTS = True  # Can be disabled for performance
ENABLE_PARTICLE_EFFECTS = False  # Disabled by default for performance

# Additional performance optimizations
ENABLE_VSYNC = True  # Enable VSync for smoother rendering
USE_DOUBLE_BUFFERING = True  # Enable double buffering

# Typography settings
LETTER_SPACING_MULTIPLIER = 0.6  # Spacing between letters as fraction of font size (increased)
WORD_PADDING = 20  # Padding around word display

# Colors (RGB) - Enhanced retro telegraph theme with better contrast
COLORS = {
    'background': (10, 10, 20),        # Deeper dark blue-black for better contrast
    'text': (255, 235, 180),           # Brighter warm amber for readability
    'title': (255, 245, 200),          # Lighter amber for titles with more pop
    'menu_header': (220, 200, 140),       # Brighter amber for menu headers
    'morse': (255, 220, 120),          # Brighter golden amber for Morse input
    'decoded': (150, 255, 150),        # Brighter green phosphor for better visibility
    'hint': (200, 200, 170),           # Brighter muted amber for hints
    'wrong': (255, 100, 100),          # Brighter red for errors (more attention-grabbing)
    'correct': (100, 255, 100),        # Brighter green for success feedback
    'neon_glow_orange': (200, 140, 80),   # Brighter amber glow
    'neon_glow_green': (80, 160, 80),      # Brighter green phosphor glow
    'neon_glow_red': (160, 80, 80),        # Brighter red phosphor glow
    
    # Enhanced menu color palette - Improved contrast and visual hierarchy
    'menu_selected_bg': (50, 140, 70),       # Brighter green phosphor background for selected items
    'menu_selected_text': (220, 255, 220),     # Brighter green phosphor text for selected items
    'menu_selected_border': (120, 255, 140),  # Brighter green border for selected items
    'menu_unselected_bg': (25, 70, 35),        # Slightly brighter green background for unselected items
    'menu_unselected_text': (170, 220, 170),   # Brighter muted green text for unselected items
    'menu_numbered_bg': (30, 80, 40),         # Brighter background for numbered menu items
    'menu_border_dark': (35, 90, 45),          # Brighter dark green border
}

# File paths
BASE_DIR = Path(__file__).parent
RESULTS_FILE = str(BASE_DIR / 'morse_results.json')

# Ensure results directory exists
os.makedirs(os.path.dirname(RESULTS_FILE), exist_ok=True)

def init_display():
    """Initialize display settings based on actual display resolution."""
    global SCREEN_WIDTH, SCREEN_HEIGHT, FONT_SIZE, SCREEN_INFO
    global TARGET_FPS, ENABLE_CRT_EFFECT, ENABLE_NEON_EFFECTS, FULLSCREEN_SCALE
    global USE_HARDWARE_ACCELERATION, ENABLE_VSYNC, USE_DOUBLE_BUFFERING
    
    try:
        import pygame
        pygame.display.init()
        
        # Get the primary display info for reference
        SCREEN_INFO = pygame.display.Info()
        
        # Calculate scaling factor for fullscreen mode
        if SCREEN_INFO.current_w > SCREEN_WIDTH or SCREEN_INFO.current_h > SCREEN_HEIGHT:
            # Display is higher resolution than our target
            FULLSCREEN_SCALE = min(
                SCREEN_INFO.current_w / SCREEN_WIDTH,
                SCREEN_INFO.current_h / SCREEN_HEIGHT
            )
            print(f"High-res display detected: {SCREEN_INFO.current_w}x{SCREEN_INFO.current_h}")
            print(f"Using scaling factor: {FULLSCREEN_SCALE:.2f}")
        else:
            FULLSCREEN_SCALE = 1.0
            print(f"Display resolution: {SCREEN_INFO.current_w}x{SCREEN_INFO.current_h}")
        
        print(f"Target resolution: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
        
        # Scale font size based on our optimized resolution
        FONT_SIZE = max(24, int(min(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.04))  # Slightly larger font for 720p
        
        # Auto-adjust performance settings for Raspberry Pi
        import platform
        import subprocess
        
        try:
            # Check if running on Raspberry Pi
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                if 'BCM' in cpuinfo or 'Raspberry Pi' in cpuinfo:
                    print("Raspberry Pi detected - applying performance optimizations")
                    # Further optimize for RPi
                    TARGET_FPS = 15  # Even lower FPS for RPi
                    ENABLE_CRT_EFFECT = False  # Disable CRT by default on RPi
                    ENABLE_NEON_EFFECTS = False  # Disable neon by default on RPi
                    USE_HARDWARE_ACCELERATION = True  # Enable RPi GPU acceleration
                    ENABLE_VSYNC = True  # Enable VSync for smoother rendering
                    USE_DOUBLE_BUFFERING = True  # Enable double buffering
        except:
            pass  # Not on RPi or can't detect
        
        print(f"Display initialized: {SCREEN_WIDTH}x{SCREEN_HEIGHT}, Font size: {FONT_SIZE}")
        print(f"Performance settings: FPS={TARGET_FPS}, CRT={ENABLE_CRT_EFFECT}, Neon={ENABLE_NEON_EFFECTS}")
        print(f"Hardware acceleration: {USE_HARDWARE_ACCELERATION}, VSync: {ENABLE_VSYNC}")
        
    except Exception as e:
        print(f"Error initializing display: {e}")
        print("Using default display settings")

# Initialize display settings when this module is imported
init_display()
