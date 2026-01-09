"""
UI Renderer for Morse Code Game - Refactored Version
Handles all rendering logic separated from game logic using modular components.
"""
import pygame
import time
from typing import Optional, Dict, Any
from ..core.game_state import GameStateManager, GameState
from ..core.config import COLORS
from .effects.crt_effects import CRTEffects
from .layout.position_calculator import PositionCalculator
from .screens.main_menu_screen import MainMenuScreen
from .screens.game_screen import GameScreen
from .screens.nickname_screen import NicknameScreen
from .screens.difficulty_screen import DifficultyScreen
from .screens.game_over_screen import GameOverScreen
from .screens.high_scores_screen import HighScoresScreen
from .screens.numbered_menu_screen import NumberedMenuScreen


class UIRenderer:
    """Handles all UI rendering for the Morse Code Game using modular components."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self._setup_fonts()
        self._setup_components()
    
    def _setup_fonts(self):
        """Initialize font objects with retro telegraph-style fonts."""
        import os
        from pathlib import Path
        
        # Path to fonts directory
        fonts_dir = Path(__file__).parent.parent.parent / "fonts"
        
        # List of retro-style system fonts to try in order
        retro_fonts = [
            'American Typewriter',
            'Courier New', 
            'Monaco',
            'Menlo',
            'Consolas',
            'Courier',
            'Monospace'
        ]
        
        try:
            # Try to load custom fonts first
            custom_fonts = [
                fonts_dir / "SpecialElite.ttf",
                fonts_dir / "RobotoMono.ttf",
                fonts_dir / "CourierPrime.ttf"
            ]
            
            font_loaded = False
            for font_path in custom_fonts:
                if font_path.exists():
                    try:
                        self.title_font = pygame.font.Font(str(font_path), FONT_SIZE * 2)
                        self.large_font = pygame.font.Font(str(font_path), int(FONT_SIZE * 1.5))
                        self.font = pygame.font.Font(str(font_path), FONT_SIZE)
                        self.small_font = pygame.font.Font(str(font_path), FONT_SIZE // 2)
                        font_loaded = True
                        print(f"Loaded custom font: {font_path.name}")
                        break
                    except Exception as e:
                        print(f"Failed to load {font_path.name}: {e}")
                        continue
            
            if not font_loaded:
                # Try system retro fonts
                for font_name in retro_fonts:
                    try:
                        self.title_font = pygame.font.SysFont(font_name, FONT_SIZE * 2, bold=True)
                        self.large_font = pygame.font.SysFont(font_name, int(FONT_SIZE * 1.5))
                        self.font = pygame.font.SysFont(font_name, FONT_SIZE)
                        self.small_font = pygame.font.SysFont(font_name, FONT_SIZE // 2)
                        print(f"Loaded system font: {font_name}")
                        break
                    except:
                        continue
                        
        except Exception as e:
            print(f"Error loading fonts: {e}")
            # Ultimate fallback
            self.title_font = pygame.font.SysFont(None, FONT_SIZE * 2, bold=True)
            self.large_font = pygame.font.SysFont(None, int(FONT_SIZE * 1.5))
            self.font = pygame.font.SysFont(None, FONT_SIZE)
            self.small_font = pygame.font.SysFont(None, FONT_SIZE // 2)
        
        # Store terminal font separately for BBS display
        self.terminal_font = pygame.font.SysFont('Courier New', 20)  # Even larger font for better readability
        self.terminal_font_bold = pygame.font.SysFont('Courier New', 20, bold=True)  # Bold version for headers
    
    def _setup_components(self):
        """Initialize all rendering components."""
        # Create font dictionary for screens
        self.fonts = {
            'title': self.title_font,
            'large': self.large_font,
            'normal': self.font,
            'small': self.small_font,
            'terminal': self.terminal_font,
            'terminal_bold': self.terminal_font_bold
        }
        
        # Initialize position calculator
        self.position_calculator = PositionCalculator(self.terminal_font)
        
        # Initialize CRT effects
        self.crt_effects = CRTEffects()
        
        # Initialize screen components
        self.screens = {
            GameState.MAIN_MENU: MainMenuScreen(self.screen, self.fonts, COLORS, self.position_calculator),
            GameState.NUMBERED_MENU: NumberedMenuScreen(self.screen, self.fonts, COLORS, self.position_calculator),
            GameState.DIFFICULTY_SELECT: DifficultyScreen(self.screen, self.fonts, COLORS, self.position_calculator),
            GameState.NICKNAME_INPUT: NicknameScreen(self.screen, self.fonts, COLORS, self.position_calculator),
            GameState.PLAYING: GameScreen(self.screen, self.fonts, COLORS, self.position_calculator),
            GameState.GAME_OVER: GameOverScreen(self.screen, self.fonts, COLORS, self.position_calculator),
            GameState.HIGH_SCORES: HighScoresScreen(self.screen, self.fonts, COLORS, self.position_calculator)
        }
    
    def render(self, state_manager: GameStateManager, morse_sequence: str = ""):
        """Main render method based on current game state."""
        current_time = time.time()
        
        # Update cursor blinking
        state_manager.update_cursor(current_time)
        
        # Clear screen
        self.screen.fill(COLORS['background'])
        
        # Render based on current state using appropriate screen component
        screen_component = self.screens.get(state_manager.current_state)
        if screen_component:
            if state_manager.current_state == GameState.PLAYING:
                screen_component.draw(state_manager, morse_sequence)
            else:
                screen_component.draw(state_manager)
        
        # Apply CRT effect for retro monitor feel
        crt_surface = self.crt_effects.create_crt_effect(self.screen)
        self.screen.blit(crt_surface, (0, 0))
        
        pygame.display.flip()
    
    def draw_text(self, text: str, x: int, y: int, color: tuple, 
                  font=None, max_width: int = None) -> int:
        """Draw text on screen with optional word wrapping."""
        if font is None:
            font = self.font
            
        if not max_width or max_width <= 0:
            surface = font.render(text, True, color)
            self.screen.blit(surface, (x, y))
            return y + font.get_height()
            
        # Word wrapping
        space_width = font.size(' ')[0]
        words = text.split(' ')
        lines = []
        current_line = []
        current_width = 0
        
        for word in words:
            word_surface = font.render(word, True, color)
            word_width = word_surface.get_width()
            
            if current_line and (current_width + space_width + word_width > max_width):
                lines.append((' '.join(current_line), current_width))
                current_line = []
                current_width = 0
                
            current_line.append(word)
            current_width += word_width + (space_width if current_line else 0)
        
        if current_line:
            lines.append((' '.join(current_line), current_width))
        
        # Draw each line
        y_pos = y
        for line, line_width in lines:
            line_surface = font.render(line, True, color)
            self.screen.blit(line_surface, (x, y_pos))
            y_pos += font.get_height() + 5
            
        return y_pos
