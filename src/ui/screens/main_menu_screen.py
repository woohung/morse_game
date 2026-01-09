"""
Main Menu Screen Component
Renders the main menu with BBS terminal style.
"""
import pygame
from typing import Dict, Any
from ..layout.position_calculator import PositionCalculator
from ...core.game_state import GameStateManager


class MainMenuScreen:
    """Renders the main menu screen."""
    
    def __init__(self, screen: pygame.Surface, fonts: Dict[str, Any], 
                 colors: Dict[str, Any], position_calculator: PositionCalculator):
        self.screen = screen
        self.fonts = fonts
        self.colors = colors
        self.position_calculator = position_calculator
        self.width, self.height = screen.get_size()
    
    def draw(self, state_manager: GameStateManager):
        """Draw the main menu screen."""
        # Clear screen with terminal background
        self.screen.fill(self.colors['background'])
        
        # Draw BBS-style header
        self._draw_header()
        
        # Draw menu options
        self._draw_menu_options(state_manager)
        
        # Draw footer
        self._draw_footer()
    
    def _draw_header(self):
        """Draw the BBS-style header."""
        header_lines = [
            "╔══════════════════════════════════════════════════════════════╗",
            "║                    MORSE CODE TERMINAL                       ║",
            "║                      Linkmeetup 2026                          ║",
            "╚══════════════════════════════════════════════════════════════╝",
            "",
            "Welcome to the Morse Code Training Terminal",
            "==========================================",
            "",
            "Please select an option:"
        ]
        
        y_offset = 50
        for line in header_lines:
            if line.startswith('╔') or line.startswith('╚') or line.startswith('║'):
                x = self.position_calculator.center_text(line, self.width, y_offset)
                self.screen.blit(self.fonts['terminal_bold'].render(line, True, self.colors['text']), 
                               (x, y_offset))
            else:
                x = self.position_calculator.center_text(line, self.width, y_offset)
                self.screen.blit(self.fonts['terminal'].render(line, True, self.colors['text']), 
                               (x, y_offset))
            y_offset += self.position_calculator.get_line_height()
    
    def _draw_menu_options(self, state_manager: GameStateManager):
        """Draw menu options with selection indicator."""
        menu_options = [
            "1. Start New Game",
            "2. High Scores",
            "3. Instructions",
            "4. Exit"
        ]
        
        current_selection = state_manager.menu_selection if hasattr(state_manager, 'menu_selection') else 0
        
        y_offset = 300
        for i, option in enumerate(menu_options):
            # Highlight selected option
            color = self.colors['highlight'] if i == current_selection else self.colors['text']
            font = self.fonts['terminal_bold'] if i == current_selection else self.fonts['terminal']
            
            x = self.position_calculator.center_text(option, self.width, y_offset)
            self.screen.blit(font.render(option, True, color), (x, y_offset))
            y_offset += self.position_calculator.get_line_height(1.5)
    
    def _draw_footer(self):
        """Draw footer information."""
        footer_lines = [
            "",
            "Use number keys or arrow keys to navigate",
            "Press ENTER to select, ESC to quit"
        ]
        
        y_offset = self.height - 100
        for line in footer_lines:
            x = self.position_calculator.center_text(line, self.width, y_offset)
            self.screen.blit(self.fonts['small'].render(line, True, self.colors['text']), 
                           (x, y_offset))
            y_offset += self.position_calculator.get_line_height()
