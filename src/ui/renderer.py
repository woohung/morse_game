"""
UI Renderer for Morse Code Game
Handles all rendering logic separated from game logic.
"""
import pygame
import time
import random
from typing import Optional, List, Dict, Any
from ..core.game_state import GameStateManager, GameState, GameData, MenuOption
from ..core.config import (COLORS, SCREEN_WIDTH, SCREEN_HEIGHT, FONT_SIZE, 
                          LETTER_SPACING_MULTIPLIER, WORD_PADDING, 
                          ENABLE_CRT_EFFECT, ENABLE_NEON_EFFECTS)


class UIRenderer:
    """Handles all UI rendering for the Morse Code Game."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.render_surface = None  # Will be set if using scaling
        self._setup_fonts()
    
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
    
    def _create_crt_effect(self, surface: pygame.Surface) -> pygame.Surface:
        """Create optimized CRT monitor effect with scanlines."""
        crt_surface = surface.copy()
        
        # Optimized scanlines - draw every 4th line instead of every 3rd
        surface_height = crt_surface.get_height()
        for y in range(0, surface_height, 4):
            pygame.draw.line(crt_surface, (0, 0, 0, 25), 
                           (0, y), (crt_surface.get_width(), y))
        
        # Optimized vignette - use larger steps and pre-calculated values
        surface_width = crt_surface.get_width()
        center_x, center_y = surface_width // 2, surface_height // 2
        max_dist = ((center_x ** 2 + center_y ** 2) ** 0.5)
        
        # Create vignette surface once and use larger steps
        vignette = pygame.Surface(crt_surface.get_size(), pygame.SRCALPHA)
        
        # Use larger steps (20 instead of 10) for better performance
        for x in range(0, surface_width, 20):
            for y in range(0, surface_height, 20):
                dist = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                alpha = int(15 * (dist / max_dist))  # Reduced alpha
                pygame.draw.circle(vignette, (0, 0, 0, alpha), (x, y), 8)  # Larger radius
        
        crt_surface.blit(vignette, (0, 0))
        return crt_surface

    def _create_glitch_effect(self, surface: pygame.Surface, intensity: float = 1.0) -> pygame.Surface:
        """Create glitch/static effect for error feedback."""
        glitch_surface = surface.copy()
        width, height = glitch_surface.get_size()
        
        # Create random noise lines
        num_lines = int(10 * intensity)  # Number of glitch lines based on intensity
        for _ in range(num_lines):
            y = random.randint(0, height - 1)
            line_height = random.randint(1, 3)
            x_offset = random.randint(-20, 20)
            
            # Create horizontal glitch line with color distortion
            for dy in range(line_height):
                if y + dy < height:
                    # Shift and distort the line
                    temp_line = glitch_surface.subsurface((0, y + dy, width, 1)).copy()
                    glitch_surface.blit(temp_line, (x_offset, y + dy))
                    
                    # Add color distortion
                    color_shift = random.choice([
                        (255, 0, 0),    # Red
                        (0, 255, 0),    # Green  
                        (0, 0, 255),    # Blue
                        (255, 255, 0),  # Yellow
                        (255, 0, 255),  # Magenta
                    ])
                    
                    # Apply color overlay with transparency
                    color_surface = pygame.Surface((width, 1))
                    color_surface.set_alpha(random.randint(20, 60))
                    color_surface.fill(color_shift)
                    glitch_surface.blit(color_surface, (0, y + dy))
        
        # Add random noise blocks
        num_blocks = int(5 * intensity)
        for _ in range(num_blocks):
            block_x = random.randint(0, width - 50)
            block_y = random.randint(0, height - 20)
            block_w = random.randint(10, 50)
            block_h = random.randint(2, 10)
            
            # Create noise block
            noise_surface = pygame.Surface((block_w, block_h))
            noise_surface.set_alpha(random.randint(30, 80))
            
            # Random color for noise
            noise_color = (
                random.randint(100, 255),
                random.randint(0, 100),
                random.randint(0, 100)
            )
            noise_surface.fill(noise_color)
            glitch_surface.blit(noise_surface, (block_x, block_y))
        
        # Add pixelation effect in random areas
        if random.random() < 0.3 * intensity:  # 30% chance per frame
            pixelate_x = random.randint(0, width - 100)
            pixelate_y = random.randint(0, height - 50)
            pixelate_w = random.randint(50, 100)
            pixelate_h = random.randint(20, 50)
            
            # Create pixelated area
            if pixelate_x + pixelate_w <= width and pixelate_y + pixelate_h <= height:
                area = glitch_surface.subsurface((pixelate_x, pixelate_y, pixelate_w, pixelate_h))
                pixelated = pygame.transform.scale(area, (pixelate_w // 4, pixelate_h // 4))
                pixelated = pygame.transform.scale(pixelated, (pixelate_w, pixelate_h))
                glitch_surface.blit(pixelated, (pixelate_x, pixelate_y))
        
        return glitch_surface

    def _create_neon_text(self, text: str, font: pygame.font.Font, color: tuple, 
                         glow_color: tuple = None, intensity: int = 1) -> pygame.Surface:
        """Create optimized text with subtle glow effect."""
        if not ENABLE_NEON_EFFECTS or intensity <= 1:
            # Skip glow effects entirely if disabled or low intensity
            return font.render(text, True, color)
        
        if glow_color is None:
            glow_color = tuple(c // 3 for c in color)
        
        # Create text surface
        text_surface = font.render(text, True, color)
        
        # Optimized glow - reduced intensity and layers for performance
        # Create single glow layer instead of multiple
        glow_surface = pygame.Surface(text_surface.get_size(), pygame.SRCALPHA)
        alpha = 20  # Reduced alpha for performance
        glow_color_with_alpha = (*glow_color, alpha)
        
        # Render glow text once
        glow_text = font.render(text, True, glow_color_with_alpha)
        glow_surface.blit(glow_text, (0, 0))
        
        # Apply simplified blur with fewer offsets
        for offset in [(-1, -1), (1, 1)]:  # Only 2 offsets instead of 4
            glow_surface.blit(glow_text, offset)
        
        # Combine glow and text
        final_surface = pygame.Surface(text_surface.get_size(), pygame.SRCALPHA)
        final_surface.blit(glow_surface, (0, 0))
        final_surface.blit(text_surface, (0, 0))
        
        return final_surface
    
    def _create_golden_glow_border(self, surface: pygame.Surface, intensity: float = 1.0) -> pygame.Surface:
        """Create golden glow effect around terminal border."""
        glow_surface = surface.copy()
        width, height = glow_surface.get_size()
        
        # Golden glow colors
        glow_colors = [
            (255, 215, 0),   # Gold
            (255, 223, 0),   # Golden yellow
            (255, 193, 37),  # Dark gold
            (255, 255, 100), # Light gold
        ]
        
        # Create multiple layers of glow with decreasing intensity
        for layer in range(3):
            alpha = int(80 * intensity * (1 - layer * 0.3))  # Decreasing alpha for each layer
            if alpha <= 0:
                continue
                
            glow_layer = pygame.Surface((width, height), pygame.SRCALPHA)
            
            # Draw border with glow effect
            border_width = 3 + layer * 2  # Increasing border width for each layer
            
            # Top and bottom borders
            for x in range(0, width, 5):  # Draw in steps for performance
                color_idx = (x // 10 + layer) % len(glow_colors)
                color = (*glow_colors[color_idx], alpha)
                
                # Top border
                pygame.draw.rect(glow_layer, color, (x, 0, 5, border_width))
                # Bottom border  
                pygame.draw.rect(glow_layer, color, (x, height - border_width, 5, border_width))
            
            # Left and right borders
            for y in range(0, height, 5):
                color_idx = (y // 10 + layer) % len(glow_colors)
                color = (*glow_colors[color_idx], alpha)
                
                # Left border
                pygame.draw.rect(glow_layer, color, (0, y, border_width, 5))
                # Right border
                pygame.draw.rect(glow_layer, color, (width - border_width, y, border_width, 5))
            
            # Apply the glow layer
            glow_surface.blit(glow_layer, (0, 0))
        
        return glow_surface

    def _create_bonus_time_overlay(self, bonus_amount: int, intensity: float = 1.0) -> pygame.Surface:
        """Create transparent overlay with bonus time text."""
        # Create a surface for the overlay
        overlay = pygame.Surface((400, 150), pygame.SRCALPHA)
        
        # Semi-transparent background
        bg_alpha = int(180 * intensity)
        pygame.draw.rect(overlay, (255, 215, 0, bg_alpha), (0, 0, 400, 150))
        pygame.draw.rect(overlay, (255, 255, 255, bg_alpha // 2), (2, 2, 396, 146), 3)
        
        # Create bonus text
        bonus_text = f"+{bonus_amount} сек."
        
        # Use large font for the bonus text
        try:
            font = pygame.font.Font(None, 72)
        except:
            font = self.title_font
        
        # Render text with golden glow effect
        text_surface = font.render(bonus_text, True, (255, 255, 255))
        
        # Center the text on the overlay
        text_rect = text_surface.get_rect(center=(200, 75))
        overlay.blit(text_surface, text_rect)
        
        return overlay

    def _draw_neon_text(self, text: str, x: int, y: int, font: pygame.font.Font, 
                       color: tuple, glow_color: tuple = None, intensity: int = 3, 
                       center_x: bool = False, center_y: bool = False):
        """Draw neon text at specified position."""
        neon_surface = self._create_neon_text(text, font, color, glow_color, intensity)
        
        if center_x:
            x = x - neon_surface.get_width() // 2
        if center_y:
            y = y - neon_surface.get_height() // 2
            
        self._blit_to_target(neon_surface, (x, y))
    
    def set_render_surface(self, render_surface: pygame.Surface):
        """Set the render surface for scaling mode."""
        self.render_surface = render_surface
    
    def _get_target_surface(self):
        """Get the target surface for rendering (screen or render_surface)."""
        return self.render_surface if self.render_surface else self.screen
    
    def _blit_to_target(self, surface, position):
        """Blit surface to the target surface."""
        target = self._get_target_surface()
        target.blit(surface, position)
    
    def _get_neon_color_for_state(self, color_state: str) -> tuple:
        if color_state == 'green':
            return COLORS['correct']
        elif color_state == 'red':
            return COLORS['wrong']
        else:
            return COLORS['text']
    
    def render(self, state_manager: GameStateManager, morse_sequence: str = ""):
        """Main render method based on current game state."""
        current_time = time.time()
        
        # Update cursor blinking
        state_manager.update_cursor(current_time)
        
        # Get target surface for rendering
        target_surface = self._get_target_surface()
        
        # Clear screen
        target_surface.fill(COLORS['background'])
        
        # Render based on current state
        if state_manager.current_state == GameState.MAIN_MENU:
            self._draw_main_menu(state_manager)
        elif state_manager.current_state == GameState.NUMBERED_MENU:
            self._draw_numbered_menu(state_manager)
        elif state_manager.current_state == GameState.DIFFICULTY_SELECT:
            self._draw_difficulty_select(state_manager)
        elif state_manager.current_state == GameState.NICKNAME_INPUT:
            self._draw_nickname_input(state_manager)
        elif state_manager.current_state == GameState.PLAYING:
            self._draw_game_screen(state_manager, morse_sequence, current_time)
        elif state_manager.current_state == GameState.PRACTICE:
            self._draw_practice_screen(state_manager, morse_sequence, current_time)
        elif state_manager.current_state == GameState.GAME_OVER:
            self._draw_game_over(state_manager)
        elif state_manager.current_state == GameState.HIGH_SCORES:
            self._draw_high_scores(state_manager)
        
        # Apply CRT effect for retro monitor feel (if enabled)
        if ENABLE_CRT_EFFECT:
            crt_surface = self._create_crt_effect(target_surface)
            target_surface.blit(crt_surface, (0, 0))
        
        # Apply glitch effect if there was a recent error
        if hasattr(state_manager.game_data, 'error_time') and state_manager.game_data.error_time:
            time_since_error = current_time - state_manager.game_data.error_time
            # Show glitch effect for 0.5 seconds after error
            if time_since_error < 0.5:
                # Calculate intensity based on time since error (fade out)
                intensity = 1.0 - (time_since_error / 0.5)
                glitch_surface = self._create_glitch_effect(target_surface, intensity)
                target_surface.blit(glitch_surface, (0, 0))
            else:
                # Clear error time after effect duration
                state_manager.game_data.error_time = None
        
        # Apply bonus time effects if bonus was recently received
        if hasattr(state_manager.game_data, 'bonus_time_received') and state_manager.game_data.bonus_time_received:
            time_since_bonus = current_time - state_manager.game_data.bonus_time_received
            # Show bonus effects for 2.0 seconds after bonus
            if time_since_bonus < 2.0:
                # Calculate intensity based on time since bonus (fade out)
                intensity = 1.0 - (time_since_bonus / 2.0)
                
                # Apply golden glow border effect
                if intensity > 0:
                    glow_surface = self._create_golden_glow_border(target_surface, intensity)
                    target_surface.blit(glow_surface, (0, 0))
                    
                    # Apply bonus time overlay in center
                    bonus_overlay = self._create_bonus_time_overlay(state_manager.game_data.bonus_amount, intensity)
                    # Center the overlay on screen
                    overlay_x = (target_surface.get_width() - bonus_overlay.get_width()) // 2
                    overlay_y = (target_surface.get_height() - bonus_overlay.get_height()) // 2
                    target_surface.blit(bonus_overlay, (overlay_x, overlay_y))
            else:
                # Clear bonus time after effect duration
                state_manager.game_data.bonus_time_received = None
                state_manager.game_data.bonus_amount = 0
    
    def _draw_practice_screen(self, state_manager: GameStateManager, morse_sequence: str, current_time: float):
        """Draw practice mode screen with single letter training and Morse alphabet reference."""
        from ..core.morse_decoder import MORSE_CODE_DICT
        
        terminal_width, terminal_height = self._get_terminal_dimensions()
        border_color = (100, 255, 100)  # Green phosphor
        
        # Add subtle screen flicker effect
        if random.random() < 0.05:  # 5% chance of flicker
            flicker_intensity = random.randint(20, 40)
            border_color = (100 - flicker_intensity, 255 - flicker_intensity, 100 - flicker_intensity)
        
        # Top border
        top_border = "╔" + "═" * (terminal_width - 2) + "╗"
        self._draw_terminal_text(top_border, 0, 0, border_color)
        
        # Content
        for i in range(1, terminal_height - 1):
            if i == 1:
                header_content = "PRACTICE MODE - MORSE TRAINING"
                header = self._format_terminal_line(header_content, terminal_width)
                self._draw_terminal_text(header, 0, i, COLORS['title'])
            elif i == 2:
                separator = "╠" + "═" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 3:
                status_content = f"COMPLETED: {state_manager.game_data.practice_completed}  |  ERRORS: {state_manager.game_data.practice_errors}"
                status = self._format_terminal_line(status_content, terminal_width)
                self._draw_terminal_text(status, 0, i, COLORS['text'])
            elif i == 4:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 5:
                target_header = f"TARGET LETTER:"
                target_line = self._format_terminal_line(target_header, terminal_width)
                self._draw_terminal_text(target_line, 0, i, COLORS['text'])
            elif i == 6:
                empty = "║" + " " * (terminal_width - 2) + "║"
                self._draw_terminal_text(empty, 0, i, border_color)
            elif i == 7:
                empty = "║" + " " * (terminal_width - 2) + "║"
                self._draw_terminal_text(empty, 0, i, border_color)
            elif i == 8:
                # Enhanced centered letter display with large font and scanning effect
                letter = state_manager.game_data.practice_letter
                if letter:
                    # Draw large centered letter with same style as main game
                    self._draw_enhanced_practice_letter(state_manager, i)
                else:
                    empty = self._format_terminal_line("", terminal_width)
                    self._draw_terminal_text(empty, 0, i, border_color)
            elif i == 9:
                # Morse hint is now displayed in _draw_enhanced_practice_letter
                empty = self._format_terminal_line("", terminal_width)
                self._draw_terminal_text(empty, 0, i, border_color)
            elif i == 10:
                empty = "║" + " " * (terminal_width - 2) + "║"
                self._draw_terminal_text(empty, 0, i, border_color)
            elif i == 11:
                empty = "║" + " " * (terminal_width - 2) + "║"
                self._draw_terminal_text(empty, 0, i, border_color)
            elif i == 12:
                empty = "║" + " " * (terminal_width - 2) + "║"
                self._draw_terminal_text(empty, 0, i, border_color)
            elif i == 13:
                empty = "║" + " " * (terminal_width - 2) + "║"
                self._draw_terminal_text(empty, 0, i, border_color)
            elif i == 14:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 15:
                input_header = f"MORSE INPUT:"
                input_line = self._format_terminal_line(input_header, terminal_width)
                self._draw_terminal_text(input_line, 0, i, COLORS['text'])
            elif i == 16:
                # Centered Morse input with awesome pulsing cursor - same as main game
                input_text = f"{morse_sequence}"
                if state_manager.cursor_visible and morse_sequence:
                    pulse_phase = int(time.time() * 10) % 5  # Very fast pulsing for Morse input
                    if pulse_phase == 0:
                        cursor_char = "█"  # Full block
                    elif pulse_phase == 1:
                        cursor_char = "▓"  # Medium block
                    elif pulse_phase == 2:
                        cursor_char = "▒"  # Light block
                    elif pulse_phase == 3:
                        cursor_char = "░"  # Very light block
                    else:
                        cursor_char = "○"  # Circle
                    input_text += cursor_char
                
                # Calculate padding to center the input
                total_input_length = len(input_text)
                padding = (terminal_width - total_input_length - 4) // 2
                morse_text = "║ " + " " * padding + input_text + " " * (terminal_width - padding - total_input_length - 4) + " ║"
                
                # Add animated background for centered Morse input field
                char_width, char_height = self.terminal_font.size("X")
                
                # Get global offset for centering
                offset_x, offset_y = self._get_terminal_offset()
                
                bg_x = offset_x + ((2 + padding) * char_width)  # Start after centered padding
                bg_y = offset_y + (i * char_height)
                bg_width = (len(input_text)) * char_width  # Cover input text + cursor
                bg_height = char_height
                
                if state_manager.cursor_visible and morse_sequence and bg_width > 0:
                    bg_surface = pygame.Surface((bg_width, bg_height))
                    bg_surface.set_alpha(40)
                    bg_pulse = int(time.time() * 4) % 3
                    if bg_pulse == 0:
                        bg_surface.fill((100, 200, 255))  # Blue
                    elif bg_pulse == 1:
                        bg_surface.fill((255, 200, 100))  # Amber
                    else:
                        bg_surface.fill((100, 255, 150))  # Green
                    self.screen.blit(bg_surface, (bg_x, bg_y))
                
                # Draw the Morse input text with enhanced color
                text_color = COLORS['morse']
                if state_manager.cursor_visible and morse_sequence:
                    text_pulse = int(time.time() * 3) % 3
                    if text_pulse == 0:
                        text_color = (180, 255, 180)  # Green phosphor
                    elif text_pulse == 1:
                        text_color = (200, 255, 255)  # Cyan
                    else:
                        text_color = (255, 200, 100)  # Golden
                
                self._draw_terminal_text(morse_text, 0, i, text_color)
            elif i == 18:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 19:
                alphabet_header = "MORSE ALPHABET:"
                alphabet_line = self._format_terminal_line(alphabet_header, terminal_width)
                self._draw_terminal_text_bold(alphabet_line, 0, i, COLORS['menu_header'])
            elif i == 20:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif 21 <= i <= 25:
                # Display Morse alphabet in 6 columns with proper alignment
                alphabet_start_index = (i - 21) * 6  # 6 letters per line
                # Show only letters A-Z for better fit
                letters = [k for k in MORSE_CODE_DICT.keys() if k.isalpha()][:26]
                alphabet_line_parts = []
                
                for j in range(6):
                    letter_index = alphabet_start_index + j
                    if letter_index < len(letters):
                        letter = letters[letter_index]
                        morse = MORSE_CODE_DICT[letter]
                        # Fixed width formatting for proper alignment
                        alphabet_line_parts.append(f"{letter:<2}{morse:<6}")
                
                # Join with single spaces for compact display
                alphabet_text = " ".join(alphabet_line_parts)
                alphabet_line = self._format_terminal_line(alphabet_text, terminal_width)
                self._draw_terminal_text(alphabet_line, 0, i, COLORS['text'])
            elif i == 26:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 27:
                inst_header_content = "COMMANDS:"
                inst_header = self._format_terminal_line(inst_header_content, terminal_width)
                self._draw_terminal_text(inst_header, 0, i, COLORS['title'])
            elif i == 28:
                inst_content = "• SPACE : Input Morse"
                inst_line = self._format_terminal_line(inst_content, terminal_width)
                self._draw_terminal_text(inst_line, 0, i, COLORS['hint'])
            elif i == 29:
                inst_content = "• ESC : Back to menu"
                inst_line = self._format_terminal_line(inst_content, terminal_width)
                self._draw_terminal_text(inst_line, 0, i, COLORS['hint'])
            elif i == terminal_height - 3:
                separator = "╠" + "═" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            else:
                empty = self._format_terminal_line("", terminal_width)
                self._draw_terminal_text(empty, 0, i, border_color)
        
        # Draw BBS-style status bar before bottom border
        self._draw_status_bar(state_manager)
        
        # Bottom border (now above status bar)
        bottom_border = "╚" + "═" * (terminal_width - 2) + "╝"
        self._draw_terminal_text(bottom_border, 0, terminal_height - 3, border_color)

    def _draw_main_menu(self, state_manager: GameStateManager):
        """Draw main menu screen with retro terminal/BBS style."""
        terminal_width, terminal_height = self._get_terminal_dimensions()
        border_color = (100, 255, 100)  # Green phosphor
        
        # Add subtle screen flicker effect
        if random.random() < 0.05:  # 5% chance of flicker
            flicker_intensity = random.randint(20, 40)
            border_color = (100 - flicker_intensity, 255 - flicker_intensity, 100 - flicker_intensity)
        
        # Top border
        top_border = "╔" + "═" * (terminal_width - 2) + "╗"
        self._draw_terminal_text(top_border, 0, 0, border_color)
        
        # Content
        for i in range(1, terminal_height - 1):
            if i == 1:
                header_content = "MORSE CODE TERMINAL v1.0 - ESTABLISHED CONNECTION"
                header = self._format_terminal_line(header_content, terminal_width)
                self._draw_terminal_text(header, 0, i, COLORS['title'])
            elif i == 2:
                separator = "╠" + "═" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif 4 <= i <= 12:
                # ASCII art title - Special for / LINKMEETUP
                title_lines = [
                    r"[ SPECIAL FOR ]",
                    r"",
                    r"__      ____  ____   __  _  ___ ___    ___    ___ ______  __ __  ____      ",
                    r"| |    |    ||    \ |  |/ ]|   |   |  /  _]  /  _]      ||  |  ||    \     ",
                    r"| |     |  | |  _  ||  ' / | _   _ | /  [_  /  [_|      ||  |  ||  o  )    ",
                    r"| |___  |  | |  |  ||    \ |  \_/  ||    _]|    _]_|  |_||  |  ||   _/     ",
                    r"|     | |  | |  |  ||     ||   |   ||   [_ |   [_  |  |  |  :  ||  |       ",
                    r"|     | |  | |  |  ||  .  ||   |   ||     ||     | |  |     ||  |       ",
                    r"|_____||____||__|__||__|\_||___|___||_____||_____| |__|   \__,_||__|       "
                    r"",
                ]
                line_index = i - 4
                if line_index < len(title_lines):
                    if line_index == 0:  # "Special for" - with gradient effect
                        # Create gradient from warm orange-red to deep red for "Special for"
                        gradient_start = (255, 200, 150)  # Warm orange-red
                        gradient_end = (200, 50, 50)      # Deep red
                        
                        # Add occasional flicker with gradient colors
                        text_color = gradient_start
                        if random.random() < 0.05:  # 5% chance of glow
                            # Interpolate between start and end for flicker
                            text_color = (255, 220, 200)  # Warm orange glow
                        self._draw_terminal_text(self._format_terminal_line(title_lines[line_index], terminal_width), 0, i, text_color)
                    elif line_index == 1:  # Empty line
                        self._draw_terminal_text(self._format_terminal_line("", terminal_width), 0, i, border_color)
                    else:  # ASCII art lines for LINKMEETUP with gradient effect
                        linkmeetup_lines = [
                            r"._      ____  ____   __  _  ___ ___    ___    ___ ______  __ __  ____      ",
                            r"| |    |    ||    \ |  |/ ]|   |   |  /  _]  /  _]      ||  |  ||    \     ",
                            r"| |     |  | |  _  ||  ' / | _   _ | /  [_  /  [_|      ||  |  ||  o  )    ",
                            r"| |___  |  | |  |  ||    \ |  \_/  ||    _]|    _]_|  |_||  |  ||   _/     ",
                            r"|     | |  | |  |  ||     ||   |   ||   [_ |   [_  |  |  |  :  ||  |       ",
                            r"|     | |  | |  |  ||  .  ||   |   ||     ||     | |  |     ||  |       ",
                            r"|_____||____||__|__||__|\_||___|___||_____||_____| |__|   \__,_||__|       "
                        ]
                        
                        # Calculate gradient colors for LINKMEETUP
                        gradient_start = (255, 180, 180)  # Bright coral red
                        gradient_end = (180, 60, 60)      # Deep crimson red
                        
                        # Find the actual index in linkmeetup_lines
                        actual_linkmeetup_index = line_index - 2  # Skip "Special for" and empty line
                        
                        if 0 <= actual_linkmeetup_index < len(linkmeetup_lines):
                            # Calculate gradient color for this line
                            progress = actual_linkmeetup_index / (len(linkmeetup_lines) - 1)
                            r = int(gradient_start[0] + (gradient_end[0] - gradient_start[0]) * progress)
                            g = int(gradient_start[1] + (gradient_end[1] - gradient_start[1]) * progress)
                            b = int(gradient_start[2] + (gradient_end[2] - gradient_start[2]) * progress)
                            art_color = (r, g, b)
                            
                            # Add occasional flicker effect
                            if random.random() < 0.02:  # 2% chance of flicker
                                art_color = (min(255, r + 50), min(255, g + 50), min(255, b + 50))  # Brighter flicker
                        else:
                            art_color = COLORS['title']
                            
                        self._draw_terminal_text(self._format_terminal_line(title_lines[line_index], terminal_width), 0, i, art_color)
            elif i == 14:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 15:
                menu_header_content = "MAIN MENU"
                menu_header = self._format_terminal_line(menu_header_content, terminal_width)
                self._draw_terminal_text_bold(menu_header, 0, i, COLORS['menu_header'])
            elif 16 <= i <= 21:
                # Menu options with unified color palette and solid background highlighting
                option_index = i - 16
                if option_index < len(state_manager.menu_options):
                    option = state_manager.menu_options[option_index]
                    
                    # Always create background highlight for better visibility
                    char_width, char_height = self.terminal_font.size("X")
                    
                    # Get global offset for centering
                    offset_x, offset_y = self._get_terminal_offset()
                    
                    bg_x = offset_x + (2 * char_width)
                    bg_y = offset_y + (i * char_height)
                    bg_width = (terminal_width - 4) * char_width
                    bg_height = char_height
                    
                    if option.selected:
                        # Selected item with unified color palette
                        pulse_phase = int(time.time() * 4) % 3  # Smooth pulsing
                        if pulse_phase == 0:
                            color = COLORS['menu_selected_text']
                            bg_color = COLORS['menu_selected_bg']
                            prefix = "> "
                            suffix = ""
                        elif pulse_phase == 1:
                            # Slightly brighter green variant
                            color = (220, 255, 220)
                            bg_color = (50, 140, 70)
                            prefix = "> "
                            suffix = ""
                        else:
                            # Warmer green variant
                            color = (180, 235, 180)
                            bg_color = (30, 100, 50)
                            prefix = "> "
                            suffix = ""
                        
                        menu_content = f"{prefix}{option.text.upper()}{suffix}"
                        menu_line = self._format_terminal_line(menu_content, terminal_width)
                        
                        # Solid background highlight for selected item
                        bg_surface = pygame.Surface((bg_width, bg_height))
                        bg_surface.set_alpha(200)  # More opaque for solid appearance
                        bg_surface.fill(bg_color)
                        self.screen.blit(bg_surface, (bg_x, bg_y))
                        
                        # Add unified border effect
                        border_surface = pygame.Surface((bg_width, 2))
                        border_surface.fill(COLORS['menu_selected_border'])
                        self.screen.blit(border_surface, (bg_x, bg_y - 1))
                        border_surface2 = pygame.Surface((bg_width, 2))
                        border_surface2.fill(COLORS['menu_border_dark'])
                        self.screen.blit(border_surface2, (bg_x, bg_y + bg_height - 1))
                        
                    else:
                        # Unselected items with unified palette
                        menu_content = f"  {option.text}  "
                        menu_line = self._format_terminal_line(menu_content, terminal_width)
                        
                        # Unified background for unselected items
                        bg_surface = pygame.Surface((bg_width, bg_height))
                        bg_surface.set_alpha(30)
                        bg_surface.fill(COLORS['menu_unselected_bg'])
                        self.screen.blit(bg_surface, (bg_x, bg_y))
                        
                        # Unified text color with subtle glow
                        if random.random() < 0.02:  # 2% chance of subtle glow
                            color = (180, 255, 180)  # Green glow
                        else:
                            color = COLORS['menu_unselected_text']
                    
                    self._draw_terminal_text(menu_line, 0, i, color)
                else:
                    empty = self._format_terminal_line("", terminal_width)
                    self._draw_terminal_text(empty, 0, i, border_color)
            elif i == 22:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 23:
                inst_header_content = "AVAILABLE COMMANDS:"
                inst_header = self._format_terminal_line(inst_header_content, terminal_width)
                self._draw_terminal_text(inst_header, 0, i, COLORS['title'])
            elif i == 24:
                inst_content = "• ENTER : Select option"
                inst_line = self._format_terminal_line(inst_content, terminal_width)
                self._draw_terminal_text(inst_line, 0, i, COLORS['hint'])
            elif i == 25:
                inst_content = "• ESC : Quit game"
                inst_line = self._format_terminal_line(inst_content, terminal_width)
                self._draw_terminal_text(inst_line, 0, i, COLORS['hint'])
            elif i == terminal_height - 2:
                separator = "╠" + "═" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            else:
                # BBS system information area - moved to bottom
                if i == terminal_height - 6:
                    bbs_header = "SYSTEM INFORMATION:"
                    bbs_line = self._format_terminal_line(bbs_header, terminal_width)
                    # Add subtle flicker to header
                    self._draw_terminal_text(bbs_line, 0, i, COLORS['title'])
                elif i == terminal_height - 5:
                    sys_info = "BBS VERSION: 1.0  NODE: 1  LINES: 1  USERS: 1"
                    sys_line = self._format_terminal_line(sys_info, terminal_width)
                    # Add data corruption effect occasionally
                    info_color = COLORS['text']
                    if random.random() < 0.02:  # 2% chance of corruption
                        # Simulate data corruption with character replacement
                        corrupted_chars = list(sys_info)
                        for j in range(len(corrupted_chars)):
                            if random.random() < 0.1:  # 10% chance per character
                                corrupted_chars[j] = random.choice(["@", "#", "$", "%", "&"])
                        sys_info = "".join(corrupted_chars)
                        info_color = (255, 100, 100)  # Red for corruption
                    self._draw_terminal_text(self._format_terminal_line(sys_info, terminal_width), 0, i, info_color)
                elif i == terminal_height - 4:
                    sys_info2 = "OS: CP/M 2.2  MEMORY: 64KB  STORAGE: 5MB"
                    sys_line2 = self._format_terminal_line(sys_info2, terminal_width)
                    self._draw_terminal_text(sys_line2, 0, i, COLORS['text'])
                elif i == terminal_height - 3:
                    # Skip MODEM line - removed as it's now in status bar
                    empty = self._format_terminal_line("", terminal_width)
                    self._draw_terminal_text(empty, 0, i, border_color)
                elif random.random() < 0.02:  # 2% chance of artifact
                    artifact_x = random.randint(5, max(10, terminal_width - 10))
                    artifact_chars = ["█", "▓", "▒", "░", "▄", "▀"]
                    artifact_content = " " * artifact_x + random.choice(artifact_chars)
                    artifact = self._format_terminal_line(artifact_content, terminal_width)
                    self._draw_terminal_text(artifact, 0, i, (50, 150, 50))
                else:
                    empty = self._format_terminal_line("", terminal_width)
                    self._draw_terminal_text(empty, 0, i, border_color)
        
        # Draw BBS-style status bar before bottom border
        self._draw_status_bar(state_manager)
        
        # Bottom border (now above status bar)
        bottom_border = "╚" + "═" * (terminal_width - 2) + "╝"
        self._draw_terminal_text(bottom_border, 0, terminal_height - 3, border_color)

    def _draw_enhanced_word(self, state_manager: GameStateManager, terminal_line: int):
        """Draw the current word with large font, centering, and scanning effect."""
        from ..core.morse_decoder import MorseDecoder
        
        word = state_manager.game_data.current_word
        colors = state_manager.game_data.letter_colors
        current_index = state_manager.game_data.current_letter_index
        
        # Create large font for the word using retro style
        from pathlib import Path
        fonts_dir = Path(__file__).parent.parent.parent / "fonts"
        
        # Try custom fonts for the main word display
        word_font_loaded = False
        for font_name in ["SpecialElite.ttf", "RobotoMono.ttf", "CourierPrime.ttf"]:
            font_path = fonts_dir / font_name
            if font_path.exists():
                try:
                    word_font = pygame.font.Font(str(font_path), int(FONT_SIZE * 2.5), bold=True)
                    word_font_loaded = True
                    break
                except:
                    continue
        
        if not word_font_loaded:
            # Use system fonts with retro feel
            for font_name in ['American Typewriter', 'Courier New', 'Monaco']:
                try:
                    word_font = pygame.font.SysFont(font_name, int(FONT_SIZE * 2.5), bold=True)
                    break
                except:
                    continue
            else:
                word_font = self.title_font  # Fallback to already loaded font
        
        # Calculate total width with actual character widths
        total_width = 0
        char_widths = []
        for char in word:
            char_width = word_font.size(char)[0]
            char_widths.append(char_width)
            total_width += char_width
        
        # Add spacing between characters
        char_spacing = int(FONT_SIZE * 0.8)
        total_width += char_spacing * (len(word) - 1)
        
        # Center the word on screen
        screen_info = pygame.display.Info()
        start_x = (screen_info.current_w - total_width) // 2
        word_y = terminal_line * 20 + 10  # Position within terminal line
        
        # Draw each character with color and glow effect
        current_x = start_x
        for i, (char, color) in enumerate(zip(word, colors)):
            # Determine color based on state
            if color == 'green':
                text_color = COLORS['correct']
                glow_color = COLORS['neon_glow_green']
                intensity = 3
            elif color == 'red':
                text_color = COLORS['wrong']
                glow_color = COLORS['neon_glow_red']
                intensity = 3
            else:
                if i == current_index:
                    text_color = COLORS['title']
                    glow_color = COLORS['neon_glow_orange']
                    intensity = 3
                else:
                    text_color = COLORS['text']
                    glow_color = COLORS['neon_glow_orange']
                    intensity = 2
            
            # Add phosphor flicker effect
            if random.random() < 0.02:  # 2% chance of flicker
                text_color = tuple(int(c * 0.7) for c in text_color)
            
            # Draw neon letter
            self._draw_neon_text(char, current_x, word_y, word_font, text_color, 
                                glow_color, intensity)
            
            # Draw Morse code hint below each letter
            if i <= current_index:
                decoder = MorseDecoder()
                morse_code = decoder.encode(char)
                hint_font = pygame.font.SysFont('Courier New', int(FONT_SIZE * 0.6))
                hint_color = COLORS['hint']
                char_width = char_widths[i]
                self._draw_neon_text(morse_code, 
                                   current_x + char_width // 2, 
                                   word_y + word_font.get_height() + 8,
                                   hint_font, hint_color, None, 1, 
                                   center_x=True)
            
            # Move to next position
            current_x += char_widths[i] + char_spacing
    
    def _draw_enhanced_practice_letter(self, state_manager: GameStateManager, terminal_line: int):
        """Draw current practice letter with large font, color coding, and Morse hint."""
        from ..core.morse_decoder import MorseDecoder
        
        letter = state_manager.game_data.practice_letter
        letter_color = state_manager.game_data.practice_letter_color
        
        if not letter:
            return
        
        # Create large font for letter using retro style
        from pathlib import Path
        fonts_dir = Path(__file__).parent.parent.parent / "fonts"
        
        # Try custom fonts for the main letter display
        letter_font_loaded = False
        for font_name in ["SpecialElite.ttf", "RobotoMono.ttf", "CourierPrime.ttf"]:
            font_path = fonts_dir / font_name
            if font_path.exists():
                try:
                    letter_font = pygame.font.Font(str(font_path), int(FONT_SIZE * 3.5), bold=True)
                    letter_font_loaded = True
                    break
                except:
                    continue
        
        if not letter_font_loaded:
            # Use system fonts with retro feel
            for font_name in ['American Typewriter', 'Courier New', 'Monaco']:
                try:
                    letter_font = pygame.font.SysFont(font_name, int(FONT_SIZE * 3.5), bold=True)
                    break
                except:
                    continue
            else:
                letter_font = self.title_font  # Fallback to already loaded font
        
        # Calculate total width with actual character width
        char_width = letter_font.size(letter)[0]
        
        # Center the letter on screen
        screen_info = pygame.display.Info()
        center_x = screen_info.current_w // 2
        start_x = center_x - char_width // 2
        letter_y = terminal_line * 20 + 10  # Position within terminal line (back to original)
        
        # Determine color based on practice letter state
        if letter_color == 'green':
            text_color = COLORS['correct']
            glow_color = COLORS['neon_glow_green']
            intensity = 3
        elif letter_color == 'red':
            text_color = COLORS['wrong']
            glow_color = COLORS['neon_glow_red']
            intensity = 3
        else:
            # Default/white state - use orange glow like current letter in game
            text_color = COLORS['title']
            glow_color = COLORS['neon_glow_orange']
            intensity = 3
        
        # Add phosphor flicker effect
        if random.random() < 0.02:  # 2% chance of flicker
            text_color = tuple(int(c * 0.7) for c in text_color)
        
        # Draw neon letter
        self._draw_neon_text(letter, start_x, letter_y, letter_font, text_color, 
                            glow_color, intensity)
        
        # Draw Morse code hint below the letter
        if letter:
            decoder = MorseDecoder()
            morse_code = decoder.encode(letter)
            hint_font = pygame.font.SysFont('Courier New', int(FONT_SIZE * 0.6))  # Same size as game mode
            hint_color = COLORS['hint']
            self._draw_neon_text(morse_code, 
                               start_x + char_width // 2,  # Same as game mode
                               letter_y + letter_font.get_height() + 8,  # Reduced distance to match game mode
                               hint_font, hint_color, None, 1, 
                               center_x=True)
    
    def _draw_colored_terminal_text(self, text: str, x: int, y: int, default_color: tuple):
        """Draw terminal text with color codes for individual characters and proper centering."""
        char_width, char_height = self.terminal_font.size("X")
        
        # Calculate position with centering adjustment for full screen
        pos_x = x * char_width
        pos_y = y * char_height
        
        # Center the entire terminal if there are remaining pixels
        # Calculate total text width first
        total_text_width = 0
        i = 0
        while i < len(text):
            if text[i:i+5] == '\033[92m' or text[i:i+5] == '\033[91m' or text[i:i+5] == '\033[93m':
                i += 5  # Skip color code
                start = i
                while i < len(text) and text[i:i+4] != '\033[0m':
                    i += 1
                char_text = text[start:i]
                total_text_width += self.terminal_font.size(char_text)[0]
                i += 4  # Skip reset code
            else:
                total_text_width += char_width
                i += 1
        
        screen_info = pygame.display.Info()
        remaining_x = screen_info.current_w - (pos_x + total_text_width)
        if remaining_x > 0 and remaining_x < char_width:
            pos_x += remaining_x // 2  # Center horizontally
        
        remaining_y = screen_info.current_h - (pos_y + char_height)
        if remaining_y > 0 and remaining_y < char_height:
            pos_y += remaining_y // 2  # Center vertically
        
        current_x = pos_x
        current_y = pos_y
        
        i = 0
        while i < len(text):
            if text[i:i+5] == '\033[92m':  # Green
                i += 5
                start = i
                while i < len(text) and text[i:i+4] != '\033[0m':
                    i += 1
                char_text = text[start:i]
                text_surface = self.terminal_font.render(char_text, True, COLORS['correct'])
                self.screen.blit(text_surface, (current_x, current_y))
                current_x += self.terminal_font.size(char_text)[0]
                i += 4  # Skip reset code
            elif text[i:i+5] == '\033[91m':  # Red
                i += 5
                start = i
                while i < len(text) and text[i:i+4] != '\033[0m':
                    i += 1
                char_text = text[start:i]
                text_surface = self.terminal_font.render(char_text, True, COLORS['wrong'])
                self.screen.blit(text_surface, (current_x, current_y))
                current_x += self.terminal_font.size(char_text)[0]
                i += 4  # Skip reset code
            elif text[i:i+5] == '\033[93m':  # Yellow
                i += 5
                start = i
                while i < len(text) and text[i:i+4] != '\033[0m':
                    i += 1
                char_text = text[start:i]
                text_surface = self.terminal_font.render(char_text, True, COLORS['title'])
                self.screen.blit(text_surface, (current_x, current_y))
                current_x += self.terminal_font.size(char_text)[0]
                i += 4  # Skip reset code
            else:
                # Regular character
                char_surface = self.terminal_font.render(text[i], True, default_color)
                self.screen.blit(char_surface, (current_x, current_y))
                current_x += char_width
                i += 1
    
    def _get_terminal_offset(self) -> tuple:
        """Calculate global offset for centering the entire terminal."""
        terminal_width, terminal_height = self._get_terminal_dimensions()
        char_width, char_height = self.terminal_font.size("X")
        
        # Get actual screen dimensions dynamically
        screen_info = pygame.display.Info()
        actual_screen_width = screen_info.current_w
        actual_screen_height = screen_info.current_h
        
        # Calculate total terminal area
        total_terminal_width = terminal_width * char_width
        total_terminal_height = terminal_height * char_height
        
        # Calculate global offset for centering the entire terminal
        offset_x = (actual_screen_width - total_terminal_width) // 2
        offset_y = (actual_screen_height - total_terminal_height) // 2
        
        # Ensure offset is non-negative (no negative positioning)
        offset_x = max(0, offset_x)
        offset_y = max(0, offset_y)
        
        return offset_x, offset_y
    
    def _draw_terminal_text(self, text: str, x: int, y: int, color: tuple):
        """Draw text in terminal style with fixed-width font and proper centering."""
        # Use the dedicated terminal font for consistent BBS display
        text_surface = self.terminal_font.render(text, True, color)
        # Calculate actual character dimensions from the terminal font
        char_width, char_height = self.terminal_font.size("X")
        
        # Get global offset for centering
        offset_x, offset_y = self._get_terminal_offset()
        
        # Calculate position with global centering offset
        pos_x = offset_x + (x * char_width)
        pos_y = offset_y + (y * char_height)
        
        self.screen.blit(text_surface, (pos_x, pos_y))
    
    def _draw_terminal_text_bold(self, text: str, x: int, y: int, color: tuple):
        """Draw bold text in terminal style with fixed-width font and proper centering."""
        # Use the bold terminal font for headers
        text_surface = self.terminal_font_bold.render(text, True, color)
        # Calculate actual character dimensions from the bold terminal font
        char_width, char_height = self.terminal_font_bold.size("X")
        
        # Get global offset for centering
        offset_x, offset_y = self._get_terminal_offset()
        
        # Calculate position with global centering offset
        pos_x = offset_x + (x * char_width)
        pos_y = offset_y + (y * char_height)
        
        self.screen.blit(text_surface, (pos_x, pos_y))
    
    def _format_terminal_line(self, content: str, terminal_width: int = 80) -> str:
        """Format a line to fit exactly in terminal width with borders."""
        # Remove any existing borders and padding
        clean_content = content.replace("║", "").strip()
        
        # Truncate content if it's too long for the terminal width (minus 2 for border characters)
        max_content_length = terminal_width - 2
        if len(clean_content) > max_content_length:
            clean_content = clean_content[:max_content_length]
        
        # Pad to exact width (minus 2 for border characters)
        padded_content = clean_content.ljust(max_content_length)
        # Add borders
        return f"║{padded_content}║"
    
    def _get_terminal_dimensions(self) -> tuple:
        """Calculate terminal dimensions for current screen."""
        # Calculate based on actual screen resolution and font metrics
        char_width, char_height = self.terminal_font.size("X")
        
        # Get actual screen dimensions dynamically
        screen_info = pygame.display.Info()
        actual_screen_width = screen_info.current_w
        actual_screen_height = screen_info.current_h
        
        # Calculate exact dimensions to fill screen completely
        terminal_width = actual_screen_width // char_width
        terminal_height = actual_screen_height // char_height
        
        # If there are remaining pixels, adjust by using slightly larger font or accepting small margins
        # For now, ensure we fill as much as possible while maintaining readability
        if actual_screen_width % char_width > char_width // 2:
            terminal_width += 1  # Use extra column if we have enough space
        if actual_screen_height % char_height > char_height // 2:
            terminal_height += 1  # Use extra row if we have enough space
        
        # Ensure minimum dimensions for readability
        terminal_width = max(80, terminal_width)
        terminal_height = max(25, terminal_height)
        
        return terminal_width, terminal_height
    
    def _draw_status_bar(self, state_manager: GameStateManager):
        """Draw BBS-style status bar at the bottom with adapted system information."""
        terminal_width, terminal_height = self._get_terminal_dimensions()
        
        # Get real system time
        import datetime
        current_time = datetime.datetime.now().strftime("%H:%M")
        
        # Create BBS-style status bar with separators and right-aligned time
        # Calculate exact spacing needed to align time to the right edge
        prefix = "Morse BBS | Connected | Ansi-BBS | 2400 BAUD |"
        available_space = terminal_width - 2 - len(prefix) - len(current_time)  # -2 for border characters
        status_content = f"{prefix}{current_time.rjust(available_space)}"
        
        # Format the status bar line
        formatted_status = self._format_terminal_line(status_content, terminal_width)
        
        # Draw status bar with distinctive background color (red like in the image)
        status_y = terminal_height - 2  # Position inside the green rectangle
        
        # Create background for status bar
        char_width, char_height = self.terminal_font.size("X")
        offset_x, offset_y = self._get_terminal_offset()
        
        bg_x = offset_x
        bg_y = offset_y + (status_y * char_height)
        bg_width = terminal_width * char_width
        bg_height = char_height
        
        # Red background for status bar (like in the image)
        bg_surface = pygame.Surface((bg_width, bg_height))
        bg_surface.set_alpha(200)
        bg_surface.fill((180, 50, 50))  # Red background
        self.screen.blit(bg_surface, (bg_x, bg_y))
        
        # Draw the status text with amber color
        self._draw_terminal_text(formatted_status, 0, status_y, (255, 220, 150))  # Amber text
        
        # Draw border around status bar to integrate it into the terminal frame
        # Top border of status bar
        top_border = "╠" + "═" * (terminal_width - 2) + "╣"
        self._draw_terminal_text(top_border, 0, status_y - 1, (100, 255, 100))  # Green border
        
        # Bottom border of status bar (before terminal bottom border)
        bottom_border = "╠" + "═" * (terminal_width - 2) + "╣"
        self._draw_terminal_text(bottom_border, 0, status_y + 1, (100, 255, 100))  # Green border
        
        # Add subtle flicker effect to simulate real BBS terminal
        if random.random() < 0.01:  # 1% chance of flicker
            # Occasionally show glitched version
            glitch_time = "??:??" if random.random() < 0.5 else current_time
            glitch_content = f"{prefix}{glitch_time.rjust(available_space)}"
            glitch_status = self._format_terminal_line(glitch_content, terminal_width)
            self._draw_terminal_text(glitch_status, 0, status_y, (200, 150, 100))  # Dimmer amber

    def _draw_difficulty_select(self, state_manager: GameStateManager):
        """Draw difficulty selection screen in BBS terminal style."""
        terminal_width, terminal_height = self._get_terminal_dimensions()
        border_color = (100, 255, 100)  # Green phosphor
        
        # Add subtle screen flicker effect like main menu
        if random.random() < 0.05:  # 5% chance of flicker
            flicker_intensity = random.randint(20, 40)
            border_color = (100 - flicker_intensity, 255 - flicker_intensity, 100 - flicker_intensity)
        
        # Top border
        top_border = "╔" + "═" * (terminal_width - 2) + "╗"
        self._draw_terminal_text(top_border, 0, 0, border_color)
        
        # Content
        for i in range(1, terminal_height - 1):
            if i == 1:
                header_content = "DIFFICULTY SELECTION - CHOOSE YOUR CHALLENGE"
                header = self._format_terminal_line(header_content, terminal_width)
                self._draw_terminal_text(header, 0, i, COLORS['title'])
            elif i == 2:
                separator = "╠" + "═" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 3:
                status_content = "SYSTEM: DIFFICULTY MATRIX LOADED - AWAITING SELECTION"
                status = self._format_terminal_line(status_content, terminal_width)
                self._draw_terminal_text(status, 0, i, COLORS['text'])
            elif i == 4:
                empty = "║" + " " * (terminal_width - 2) + "║"
                self._draw_terminal_text(empty, 0, i, border_color)
            elif 5 <= i <= 9:
                # ASCII art for difficulty
                difficulty_art = [
                    r"  _____ _   _ _   _    _    _   _  ____ _____ ____  _____   ",
                    r" |  ___| | | | \ | |  / \  | \ | |/ ___| ____|  _ \| ____|  ",
                    r" | |_  | | | |  \| | / _ \ |  \| | |   |  _| | |_) |  _|   ",
                    r" |  _| | |_| | |\  |/ ___ \| |\  | |___| |___|  _ <| |___  ",
                    r" |_|    \___/|_| \_/_/   \_\_| \_|\____|_____|_| \_\_____|  "
                ]
                line_index = i - 5
                if line_index < len(difficulty_art):
                    self._draw_terminal_text(difficulty_art[line_index], 0, i, COLORS['title'])
                else:
                    self._draw_terminal_text("║" + " " * (terminal_width - 2) + "║", 0, i, border_color)
            elif i == 10:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 11:
                menu_header_content = "AVAILABLE MODES"
                menu_header = self._format_terminal_line(menu_header_content, terminal_width)
                self._draw_terminal_text_bold(menu_header, 0, i, COLORS['menu_header'])
            elif 12 <= i <= 15:
                # Difficulty options with unified color palette and solid background highlighting
                option_index = i - 12
                if option_index < len(state_manager.difficulty_options):
                    option = state_manager.difficulty_options[option_index]
                    
                    # Always create background highlight for better visibility
                    char_width, char_height = self.terminal_font.size("X")
                    
                    # Get global offset for centering
                    offset_x, offset_y = self._get_terminal_offset()
                    
                    bg_x = offset_x + (2 * char_width)
                    bg_y = offset_y + (i * char_height)
                    bg_width = (terminal_width - 4) * char_width
                    bg_height = char_height
                    
                    if option.selected:
                        # Selected item with highest contrast
                        pulse_phase = int(time.time() * 4) % 3  # Smooth pulsing
                        if pulse_phase == 0:
                            color = (255, 255, 255)  # Pure white for maximum contrast
                            bg_color = (0, 100, 0)  # Dark green background
                            prefix = "> "
                            suffix = ""
                        elif pulse_phase == 1:
                            # Bright white variant
                            color = (240, 255, 240)  # Slightly blue-tinted white
                            bg_color = (20, 120, 20)  # Medium green background
                            prefix = "> "
                            suffix = ""
                        else:
                            # Warm white variant
                            color = (255, 250, 235)  # Warm white
                            bg_color = (10, 80, 10)  # Dark green background
                            prefix = "> "
                            suffix = ""
                        
                        menu_content = f"{prefix}{option.text.upper()}{suffix}"
                        menu_line = self._format_terminal_line(menu_content, terminal_width)
                        
                        # Solid background highlight for selected item
                        bg_surface = pygame.Surface((bg_width, bg_height))
                        bg_surface.set_alpha(200)  # More opaque for solid appearance
                        bg_surface.fill(bg_color)
                        self.screen.blit(bg_surface, (bg_x, bg_y))
                        
                        # Add unified border effect
                        border_surface = pygame.Surface((bg_width, 2))
                        border_surface.fill(COLORS['menu_selected_border'])
                        self.screen.blit(border_surface, (bg_x, bg_y - 1))
                        border_surface2 = pygame.Surface((bg_width, 2))
                        border_surface2.fill(COLORS['menu_border_dark'])
                        self.screen.blit(border_surface2, (bg_x, bg_y + bg_height - 1))
                        
                    else:
                        # Unselected items with unified palette
                        cursor = "  "
                        menu_content = f"{cursor}{option.text}"
                        menu_line = self._format_terminal_line(menu_content, terminal_width)
                        
                        # Unified background for unselected items
                        bg_surface = pygame.Surface((bg_width, bg_height))
                        bg_surface.set_alpha(30)
                        bg_surface.fill(COLORS['menu_unselected_bg'])
                        self.screen.blit(bg_surface, (bg_x, bg_y))
                        
                        # Unified text color with subtle glow
                        if random.random() < 0.03:  # 3% chance of subtle glow
                            color = (180, 255, 180)  # Green glow
                        else:
                            color = COLORS['menu_unselected_text']  # Use unified color                
                    self._draw_terminal_text(menu_line, 0, i, color)
                else:
                    empty = self._format_terminal_line("", terminal_width)
                    self._draw_terminal_text(empty, 0, i, border_color)
            elif i == 16:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 17:
                rules_header_content = "CONTEST RULES:"
                rules_header = self._format_terminal_line(rules_header_content, terminal_width)
                # Enhanced header with bright cyan and glow effect
                self._draw_terminal_text(rules_header, 0, i, COLORS['title'])
            elif i == 18:
                rules1_content = "• Type words using Morse code - dots and dashes"
                rules1 = self._format_terminal_line(rules1_content, terminal_width)
                # Bright green for rules with occasional glow
                rules_color = (150, 255, 150)  # Bright green
                if random.random() < 0.05:  # 5% chance of glow
                    rules_color = (200, 255, 200)  # Brighter green glow
                self._draw_terminal_text(rules1, 0, i, rules_color)
            elif i == 19:
                rules2_content = "• Faster and more accurate typing means higher scores and better chances to win"
                rules2 = self._format_terminal_line(rules2_content, terminal_width)
                # Bright green for rules with occasional glow
                rules_color = (150, 255, 150)  # Bright green
                if random.random() < 0.05:  # 5% chance of glow
                    rules_color = (200, 255, 200)  # Brighter green glow
                self._draw_terminal_text(rules2, 0, i, rules_color)
            elif i == 20:
                rules3_content = "• Each level has its own time, word difficulty, winner board and unique first place prize"
                rules3 = self._format_terminal_line(rules3_content, terminal_width)
                # Bright green for rules with occasional glow
                rules_color = (150, 255, 150)  # Bright green
                if random.random() < 0.05:  # 5% chance of glow
                    rules_color = (200, 255, 200)  # Brighter green glow
                self._draw_terminal_text(rules3, 0, i, rules_color)
            elif i == 21:
                bonus_content = "• HARD MODE BONUS: +15 seconds every 3rd correct word to help you beat the clock!"
                bonus = self._format_terminal_line(bonus_content, terminal_width)
                # Special golden color for bonus info with glow
                bonus_color = (255, 220, 100)  # Golden amber
                if random.random() < 0.1:  # 10% chance of glow
                    bonus_color = (255, 240, 150)  # Brighter golden glow
                self._draw_terminal_text(bonus, 0, i, bonus_color)
            elif i == 22:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 23:
                desc_header_content = "CONTEST PRIZES:"
                desc_header = self._format_terminal_line(desc_header_content, terminal_width)
                # Enhanced header with bright gold and glow effect
                self._draw_terminal_text(desc_header, 0, i, COLORS['title'])
            elif i == 24:
                desc1_content = "• 1ST PLACE (EASY): History of telephone devices book, sourced from ebay"
                desc1 = self._format_terminal_line(desc1_content, terminal_width)
                # Enhanced golden amber with glow for 1st place
                prize_color = (255, 220, 120)  # Bright golden amber
                if random.random() < 0.08:  # 8% chance of glow
                    prize_color = (255, 240, 160)  # Brighter golden glow
                self._draw_terminal_text(desc1, 0, i, prize_color)
            elif i == 25:
                desc2_content = "• 1ST PLACE (HARD): The actual telegraph key that you see right in front of you now"
                desc2 = self._format_terminal_line(desc2_content, terminal_width)
                # Enhanced golden orange with glow for 1st place hard
                prize_color = (255, 210, 110)  # Bright golden orange
                if random.random() < 0.1:  # 10% chance of glow
                    prize_color = (255, 230, 140)  # Brighter orange glow
                self._draw_terminal_text(desc2, 0, i, prize_color)
            elif i == 26:
                desc3_content = "• 2-3 PLACES: T-shirt of our telecommunications history podcast or meetup merch of your choice"
                desc3 = self._format_terminal_line(desc3_content, terminal_width)
                # Enhanced golden bronze with glow for other prizes
                prize_color = (255, 200, 100)  # Bright golden bronze
                if random.random() < 0.06:  # 6% chance of glow
                    prize_color = (255, 220, 130)  # Brighter bronze glow
                self._draw_terminal_text(desc3, 0, i, prize_color)
            elif i == 27:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 28:
                inst_header_content = "AVAILABLE COMMANDS:"
                inst_header = self._format_terminal_line(inst_header_content, terminal_width)
                self._draw_terminal_text(inst_header, 0, i, COLORS['title'])
            elif i == 29:
                inst1_content = "• ↑↓ : Select"
                inst1_line = self._format_terminal_line(inst1_content, terminal_width)
                self._draw_terminal_text(inst1_line, 0, i, COLORS['hint'])
            elif i == 30:
                inst2_content = "• ENTER : Confirm"
                inst2_line = self._format_terminal_line(inst2_content, terminal_width)
                self._draw_terminal_text(inst2_line, 0, i, COLORS['hint'])
            elif i == 31:
                inst3_content = "• ESC : Main menu"
                inst3_line = self._format_terminal_line(inst3_content, terminal_width)
                self._draw_terminal_text(inst3_line, 0, i, COLORS['hint'])
            elif i == terminal_height - 2:
                separator = "╠" + "═" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            else:
                empty = "║" + " " * (terminal_width - 2) + "║"
                self._draw_terminal_text(empty, 0, i, border_color)
        
        # Bottom border
        bottom_border = "╚" + "═" * (terminal_width - 2) + "╝"
        self._draw_terminal_text(bottom_border, 0, terminal_height - 1, border_color)
        
        # Draw status bar
        self._draw_status_bar(state_manager)
    
    def _draw_nickname_input(self, state_manager: GameStateManager):
        """Draw nickname input screen in BBS terminal style."""
        terminal_width, terminal_height = self._get_terminal_dimensions()
        border_color = (100, 255, 100)  # Green phosphor
        
        # Add subtle screen flicker effect like main menu
        if random.random() < 0.05:  # 5% chance of flicker
            flicker_intensity = random.randint(20, 40)
            border_color = (100 - flicker_intensity, 255 - flicker_intensity, 100 - flicker_intensity)
        
        # Top border
        top_border = "╔" + "═" * (terminal_width - 2) + "╗"
        self._draw_terminal_text(top_border, 0, 0, border_color)
        
        # Content
        for i in range(1, terminal_height - 1):
            if i == 1:
                header = f"USER REGISTRATION - CREATE YOUR CALLSIGN"
                header_line = self._format_terminal_line(header, terminal_width)
                self._draw_terminal_text(header_line, 0, i, border_color)
            elif i == 2:
                separator = "╠" + "═" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 3:
                status = f"BBS: NEW USER DETECTED - REGISTRATION REQUIRED"
                status_line = self._format_terminal_line(status, terminal_width)
                self._draw_terminal_text(status_line, 0, i, COLORS['text'])
            elif i == 4:
                empty = self._format_terminal_line("", terminal_width)
                self._draw_terminal_text(empty, 0, i, border_color)
            elif 5 <= i <= 9:
                # ASCII art for user/login
                login_art = [
                    r"    _    _   _   ____  _____ ____     ____    _    _     _   _____  ",
                    r"   / \  | \ | | / ___|| ____|  _ \   | __ )  / \  | |   | | | ____| ",
                    r"  / _ \ |  \| || |    |  _| | |_) |  |  _ \ / _ \ | |   | | |  _|  ",
                    r" / ___ \| |\  || |___ | |___|  _ <   | |_) / ___ \| |___| | | |___ ",
                    r"/_/   \_\_| \_| \____||_____|_| \_\  |____/_/   \_\_____|_|_|_____| "
                ]
                line_index = i - 5
                if line_index < len(login_art):
                    if random.random() < 0.05:  # Flicker effect
                        art_line = self._format_terminal_line(login_art[line_index], terminal_width)
                        self._draw_terminal_text(art_line, 0, i, (50, 150, 50))
                    else:
                        art_line = self._format_terminal_line(login_art[line_index], terminal_width)
                        self._draw_terminal_text(art_line, 0, i, COLORS['title'])
                else:
                    empty = self._format_terminal_line("", terminal_width)
                    self._draw_terminal_text(empty, 0, i, border_color)
            elif i == 10:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 11:
                rules_header = f"SYSTEM RULES:"
                rules_line = self._format_terminal_line(rules_header, terminal_width)
                self._draw_terminal_text(rules_line, 0, i, COLORS['title'])
            elif i == 12:
                rule1 = f"• UNIQUE CALLSIGN: Each operator may register only once"
                rule1_line = self._format_terminal_line(rule1, terminal_width)
                self._draw_terminal_text(rule1_line, 0, i, COLORS['hint'])
            elif i == 13:
                rule2 = f"• UNLIMITED ATTEMPTS: no limit on transmission attempts — just use a new callsign"
                rule2_line = self._format_terminal_line(rule2, terminal_width)
                self._draw_terminal_text(rule2_line, 0, i, COLORS['hint'])
            elif i == 14:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 15:
                input_header = f"ENTER YOUR CALLSIGN (MAX 15 CHARACTERS)"
                input_line = self._format_terminal_line(input_header, terminal_width)
                self._draw_terminal_text(input_line, 0, i, COLORS['text'])
            elif i == 16:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 17:
                # Enhanced input field with unified color palette and pulsing cursor effects
                input_text = state_manager.nickname_input
                
                # Enhanced cursor with unified color palette
                cursor_char = "_"
                cursor_color = COLORS['morse']
                
                if state_manager.cursor_visible:
                    pulse_phase = int(time.time() * 8) % 4  # Fast pulsing for cursor
                    if pulse_phase == 0:
                        cursor_char = "█"  # Full block
                        cursor_color = COLORS['menu_selected_text']  # Bright green
                    elif pulse_phase == 1:
                        cursor_char = "▓"  # Medium block
                        cursor_color = COLORS['menu_selected_border']  # Border green
                    elif pulse_phase == 2:
                        cursor_char = "▒"  # Light block
                        cursor_color = (150, 255, 150)  # Green phosphor
                    else:
                        cursor_char = "░"  # Very light block
                        cursor_color = (100, 200, 100)  # Dimmed green
                    
                    input_text += cursor_char
                
                input_display = f"║ > {input_text}{' ' * (terminal_width - len(input_text) - 5)} ║"
                
                # Add animated background for input field with unified palette
                char_width, char_height = self.terminal_font.size("X")
                
                # Get global offset for centering
                offset_x, offset_y = self._get_terminal_offset()
                
                bg_x = offset_x + (4 * char_width)  # Start after "║ > "
                bg_y = offset_y + (i * char_height)
                bg_width = len(input_text) * char_width  # Cover input text
                bg_height = char_height
                
                if state_manager.cursor_visible and bg_width > 0:
                    bg_surface = pygame.Surface((bg_width, bg_height))
                    bg_surface.set_alpha(40)  # Slightly more visible
                    bg_pulse = int(time.time() * 3) % 3
                    if bg_pulse == 0:
                        bg_surface.fill(COLORS['menu_selected_bg'])  # Green background
                    elif bg_pulse == 1:
                        bg_surface.fill(COLORS['menu_unselected_bg'])  # Dark green
                    else:
                        bg_surface.fill(COLORS['menu_border_dark'])  # Border dark
                    self.screen.blit(bg_surface, (bg_x, bg_y))
                
                # Draw the input text with unified color palette
                text_color = COLORS['morse']
                if state_manager.cursor_visible:
                    text_pulse = int(time.time() * 2) % 2
                    if text_pulse == 0:
                        text_color = (180, 255, 180)  # Green phosphor
                    else:
                        text_color = (200, 255, 255)  # Cyan
                
                self._draw_terminal_text(input_display, 0, i, text_color)
            elif i == 18:
                empty = self._format_terminal_line("", terminal_width)
                self._draw_terminal_text(empty, 0, i, border_color)
            elif i == 19:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 20 and state_manager.nickname_error:
                # Show error message if nickname is taken
                error_msg = "ERROR: CALLSIGN ALREADY REGISTERED - CHOOSE DIFFERENT CALLSIGN"
                error_line = self._format_terminal_line(error_msg, terminal_width)
                # Make error message blink/flicker
                if int(time.time() * 4) % 2 == 0:
                    self._draw_terminal_text(error_line, 0, i, COLORS['wrong'])
                else:
                    self._draw_terminal_text(error_line, 0, i, (150, 50, 50))
            elif i == 20 and not state_manager.nickname_error:
                empty = self._format_terminal_line("", terminal_width)
                self._draw_terminal_text(empty, 0, i, border_color)
            elif i == 21:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 22:
                inst_header = f"AVAILABLE COMMANDS:"
                inst_line = self._format_terminal_line(inst_header, terminal_width)
                self._draw_terminal_text(inst_line, 0, i, COLORS['hint'])
            elif i == 23:
                inst1 = f"• TYPE : Enter your callsign"
                inst1_line = self._format_terminal_line(inst1, terminal_width)
                self._draw_terminal_text(inst1_line, 0, i, COLORS['hint'])
            elif i == 24:
                inst2 = f"• BACKSPACE : Delete character"
                inst2_line = self._format_terminal_line(inst2, terminal_width)
                self._draw_terminal_text(inst2_line, 0, i, COLORS['hint'])
            elif i == 25:
                inst3 = f"• ENTER : Confirm registration"
                inst3_line = self._format_terminal_line(inst3, terminal_width)
                self._draw_terminal_text(inst3_line, 0, i, COLORS['hint'])
            elif i == 26:
                inst4 = f"• ESC : Abort registration"
                inst4_line = self._format_terminal_line(inst4, terminal_width)
                self._draw_terminal_text(inst4_line, 0, i, COLORS['hint'])
            elif i == 27:
                empty = self._format_terminal_line("", terminal_width)
                self._draw_terminal_text(empty, 0, i, border_color)
            elif i == 28:
                footer = f"SYSOP MESSAGE: WELCOME TO MORSE CODE BBS!"
                footer_line = self._format_terminal_line(footer, terminal_width)
                self._draw_terminal_text(footer_line, 0, i, border_color)
            elif i == terminal_height - 2:
                separator = "╠" + "═" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            else:
                empty = "║" + " " * (terminal_width - 2) + "║"
                self._draw_terminal_text(empty, 0, i, border_color)
        
        # Bottom border
        bottom_border = "╚" + "═" * (terminal_width - 2) + "╝"
        self._draw_terminal_text(bottom_border, 0, terminal_height - 1, border_color)
        
        # Draw status bar
        self._draw_status_bar(state_manager)
    
    def _draw_game_screen(self, state_manager: GameStateManager, morse_sequence: str, current_time: float):
        """Draw main game screen in BBS terminal style."""
        # Update game timer - don't overwrite bonus time, just let it decrease naturally
        # The game controller already handles time updates correctly
        
        terminal_width, terminal_height = self._get_terminal_dimensions()
        border_color = (100, 255, 100)  # Green phosphor
        
        # Add subtle screen flicker effect like main menu
        if random.random() < 0.05:  # 5% chance of flicker
            flicker_intensity = random.randint(20, 40)
            border_color = (100 - flicker_intensity, 255 - flicker_intensity, 100 - flicker_intensity)
        
        # Top border
        top_border = "╔" + "═" * (terminal_width - 2) + "╗"
        self._draw_terminal_text(top_border, 0, 0, border_color)
        
        word_time_remaining = state_manager.get_word_time_remaining()
        
        # Content
        for i in range(1, terminal_height - 1):
            if i == 1:
                header = f"║ MORSE CODE TRANSMISSION - ACTIVE SESSION{' ' * (terminal_width - 45)} ║"
                self._draw_terminal_text(header, 0, i, COLORS['title'])
            elif i == 2:
                separator = "╠" + "═" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 3:
                # Game status line
                status = f"PLAYER: {state_manager.game_data.nickname}  WORDS: {state_manager.game_data.words_completed}  TIME: {int(state_manager.game_data.time_remaining)}s  ERRORS: {state_manager.game_data.total_errors}"
                status_line = self._format_terminal_line(status, terminal_width)
                self._draw_terminal_text(status_line, 0, i, COLORS['text'])
            elif i == 4:
                # Word timer with color coding
                if word_time_remaining > 5:
                    timer_color = COLORS['text']
                    timer_text = f"WORD TIMER: {word_time_remaining:.1f}s - TRANSMISSION ACTIVE"
                elif word_time_remaining > 2:
                    timer_color = COLORS['wrong']
                    timer_text = f"WORD TIMER: {word_time_remaining:.1f}s - HURRY UP!"
                else:
                    timer_color = (255, 50, 50)
                    timer_text = f"WORD TIMER: {word_time_remaining:.1f}s - CRITICAL!"
                timer_line = self._format_terminal_line(timer_text, terminal_width)
                self._draw_terminal_text(timer_line, 0, i, timer_color)
            elif i == 5:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 6:
                target_header = f"TARGET TRANSMISSION:"
                target_line = self._format_terminal_line(target_header, terminal_width)
                self._draw_terminal_text(target_line, 0, i, COLORS['text'])
            elif 7 <= i <= 11:
                # Current word display area
                if i == 7:
                    empty = "║" + " " * (terminal_width - 2) + "║"
                    self._draw_terminal_text(empty, 0, i, border_color)
                elif i == 8:
                    # Enhanced centered word display with large font and scanning effect
                    word = state_manager.game_data.current_word
                    if word:
                        # Draw large centered word with scanning effect
                        self._draw_enhanced_word(state_manager, i)
                    else:
                        empty = self._format_terminal_line("", terminal_width)
                        self._draw_terminal_text(empty, 0, i, border_color)
                elif i == 9:
                    empty = "║" + " " * (terminal_width - 2) + "║"
                    self._draw_terminal_text(empty, 0, i, border_color)
                elif i == 10:
                    # Morse hints are now displayed directly under letters in _draw_enhanced_word
                    empty = self._format_terminal_line("", terminal_width)
                    self._draw_terminal_text(empty, 0, i, border_color)
                else:
                    empty = self._format_terminal_line("", terminal_width)
                    self._draw_terminal_text(empty, 0, i, border_color)
            elif i == 12:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 13:
                input_header = f"MORSE INPUT:"
                input_line = self._format_terminal_line(input_header, terminal_width)
                self._draw_terminal_text(input_line, 0, i, COLORS['text'])
            elif i == 14:
                # Centered Morse input with awesome pulsing cursor
                # Calculate centered position for input
                input_text = f"{morse_sequence}"
                if state_manager.cursor_visible and morse_sequence:
                    pulse_phase = int(time.time() * 10) % 5  # Very fast pulsing for Morse input
                    if pulse_phase == 0:
                        cursor_char = "█"  # Full block
                    elif pulse_phase == 1:
                        cursor_char = "▓"  # Medium block
                    elif pulse_phase == 2:
                        cursor_char = "▒"  # Light block
                    elif pulse_phase == 3:
                        cursor_char = "░"  # Very light block
                    else:
                        cursor_char = "○"  # Circle
                    input_text += cursor_char
                
                # Calculate padding to center the input
                total_input_length = len(input_text)
                padding = (terminal_width - total_input_length - 4) // 2
                morse_text = "║ " + " " * padding + input_text + " " * (terminal_width - padding - total_input_length - 4) + " ║"
                
                # Add animated background for centered Morse input field
                char_width, char_height = self.terminal_font.size("X")
                
                # Get global offset for centering
                offset_x, offset_y = self._get_terminal_offset()
                
                bg_x = offset_x + ((2 + padding) * char_width)  # Start after centered padding
                bg_y = offset_y + (i * char_height)
                bg_width = (len(input_text)) * char_width  # Cover input text + cursor
                bg_height = char_height
                
                if state_manager.cursor_visible and morse_sequence and bg_width > 0:
                    bg_surface = pygame.Surface((bg_width, bg_height))
                    bg_surface.set_alpha(40)
                    bg_pulse = int(time.time() * 4) % 3
                    if bg_pulse == 0:
                        bg_surface.fill((100, 200, 255))  # Blue
                    elif bg_pulse == 1:
                        bg_surface.fill((255, 200, 100))  # Amber
                    else:
                        bg_surface.fill((100, 255, 150))  # Green
                    self.screen.blit(bg_surface, (bg_x, bg_y))
                
                # Draw the Morse input text with enhanced color
                text_color = COLORS['morse']
                if state_manager.cursor_visible and morse_sequence:
                    text_pulse = int(time.time() * 3) % 3
                    if text_pulse == 0:
                        text_color = (180, 255, 180)  # Green phosphor
                    elif text_pulse == 1:
                        text_color = (200, 255, 255)  # Cyan
                    else:
                        text_color = (255, 200, 100)  # Golden
                
                self._draw_terminal_text(morse_text, 0, i, text_color)
            elif i == 15:
                empty = "║" + " " * (terminal_width - 2) + "║"
                self._draw_terminal_text(empty, 0, i, border_color)
            elif i == 16:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 17:
                inst_header = f"AVAILABLE COMMANDS:"
                inst_line = self._format_terminal_line(inst_header, terminal_width)
                self._draw_terminal_text(inst_line, 0, i, COLORS['hint'])
            elif i == 18:
                inst1 = f"• SPACE : Transmit dot/dash"
                inst1_line = self._format_terminal_line(inst1, terminal_width)
                self._draw_terminal_text(inst1_line, 0, i, COLORS['hint'])
            elif i == 19:
                inst2 = f"• C : Clear input"
                inst2_line = self._format_terminal_line(inst2, terminal_width)
                self._draw_terminal_text(inst2_line, 0, i, COLORS['hint'])
            elif i == 20:
                inst3 = f"• ESC : Abort transmission"
                inst3_line = self._format_terminal_line(inst3, terminal_width)
                self._draw_terminal_text(inst3_line, 0, i, COLORS['hint'])
            elif i == terminal_height - 2:
                separator = "╠" + "═" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            else:
                empty = "║" + " " * (terminal_width - 2) + "║"
                self._draw_terminal_text(empty, 0, i, border_color)
        
        # Bottom border
        bottom_border = "╚" + "═" * (terminal_width - 2) + "╝"
        self._draw_terminal_text(bottom_border, 0, terminal_height - 1, border_color)
        
        # Draw status bar
        self._draw_status_bar(state_manager)
    
    def _draw_current_word(self, state_manager: GameStateManager):
        """Draw the current word with neon letter colors and Morse hints."""
        from ..core.morse_decoder import MorseDecoder
        
        word = state_manager.game_data.current_word
        colors = state_manager.game_data.letter_colors
        current_index = state_manager.game_data.current_letter_index
        
        # Create larger font for the word using retro style
        from pathlib import Path
        fonts_dir = Path(__file__).parent.parent.parent / "fonts"
        
        # Try custom fonts for the main word display
        word_font_loaded = False
        for font_name in ["SpecialElite.ttf", "RobotoMono.ttf", "CourierPrime.ttf"]:
            font_path = fonts_dir / font_name
            if font_path.exists():
                try:
                    word_font = pygame.font.Font(str(font_path), int(FONT_SIZE * 3), bold=True)
                    word_font_loaded = True
                    break
                except:
                    continue
        
        if not word_font_loaded:
            # Use system fonts with retro feel
            for font_name in ['American Typewriter', 'Courier New', 'Monaco']:
                try:
                    word_font = pygame.font.SysFont(font_name, int(FONT_SIZE * 3), bold=True)
                    break
                except:
                    continue
            else:
                word_font = self.title_font  # Fallback to already loaded font
            
        hint_font = self.font
        
        # Calculate starting position to center the word with proper spacing
        # Adjust spacing based on font type (monospace vs proportional)
        font_name = word_font.get_name().lower() if hasattr(word_font, 'get_name') else ''
        if 'courier' in font_name or 'mono' in font_name:
            # Monospace fonts need less extra spacing
            char_spacing = int(FONT_SIZE * LETTER_SPACING_MULTIPLIER * 0.5)
        else:
            # Proportional fonts need more spacing
            char_spacing = int(FONT_SIZE * LETTER_SPACING_MULTIPLIER)
        
        # Calculate total width with actual character widths
        total_width = 0
        char_widths = []
        for char in word:
            char_width = word_font.size(char)[0]
            char_widths.append(char_width)
            total_width += char_width
        
        # Add spacing between characters
        total_width += char_spacing * (len(word) - 1)
        
        # Center the word on screen
        screen_info = pygame.display.Info()
        start_x = (screen_info.current_w - total_width) // 2
        word_y = 220
        
        # Draw background rectangle for the word
        word_height = word_font.get_height()
        bg_rect = pygame.Rect(start_x - WORD_PADDING, word_y - 10, total_width + WORD_PADDING * 2, word_height + 60)
        pygame.draw.rect(self.screen, (20, 20, 30), bg_rect, border_radius=10)
        pygame.draw.rect(self.screen, COLORS['title'], bg_rect, 2, border_radius=10)
        
        decoder = MorseDecoder()
        
        # Track current x position
        current_x = start_x
        
        for i, (char, color) in enumerate(zip(word, colors)):
            # Determine neon color based on state
            if color == 'green':
                text_color = COLORS['correct']
                glow_color = COLORS['neon_glow_green']
                intensity = 2
            elif color == 'red':
                text_color = COLORS['wrong']
                glow_color = COLORS['neon_glow_red']
                intensity = 2
            else:
                if i == current_index:
                    text_color = COLORS['title']
                    glow_color = COLORS['neon_glow_orange']
                    intensity = 2
                else:
                    text_color = COLORS['text']
                    glow_color = COLORS['neon_glow_orange']
                    intensity = 1
            
            # Draw neon letter at current position
            self._draw_neon_text(char, current_x, word_y, word_font, text_color, 
                                glow_color, intensity)
            
            # Draw Morse code hint below each letter with subtle glow
            if i <= current_index:
                morse_code = decoder.encode(char)
                hint_color = COLORS['hint']
                hint_glow = tuple(c // 4 for c in hint_color)
                char_width = char_widths[i]
                self._draw_neon_text(morse_code, 
                                   current_x + char_width // 2, 
                                   word_y + word_height + 10,
                                   hint_font, hint_color, hint_glow, 1, 
                                   center_x=True)
            
            # Move to next position with consistent spacing
            current_x += char_widths[i] + char_spacing
    
    def _draw_game_over(self, state_manager: GameStateManager):
        """Draw game over screen in BBS terminal style."""
        terminal_width, terminal_height = self._get_terminal_dimensions()
        border_color = (100, 255, 100)  # Green phosphor
        
        # Add subtle screen flicker effect like main menu
        if random.random() < 0.05:  # 5% chance of flicker
            flicker_intensity = random.randint(20, 40)
            border_color = (100 - flicker_intensity, 255 - flicker_intensity, 100 - flicker_intensity)
        
        # Top border
        top_border = "╔" + "═" * (terminal_width - 2) + "╗"
        self._draw_terminal_text(top_border, 0, 0, border_color)
        
        # Content
        for i in range(1, terminal_height - 1):
            if i == 1:
                header = f"TRANSMISSION COMPLETE - SESSION TERMINATED"
                header_line = self._format_terminal_line(header, terminal_width)
                self._draw_terminal_text(header_line, 0, i, border_color)
            elif i == 2:
                separator = "╠" + "═" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 3:
                status = f"BBS: DISCONNECTING FROM MORSE NETWORK"
                status_line = self._format_terminal_line(status, terminal_width)
                self._draw_terminal_text(status_line, 0, i, COLORS['text'])
            elif i == 4:
                empty = self._format_terminal_line("", terminal_width)
                self._draw_terminal_text(empty, 0, i, border_color)
            elif 5 <= i <= 9:
                # ASCII art for game over
                gameover_art = [
                    r"  ____  _   _ ____    ____    _    _     _   _____  ____  _____   ",
                    r" |  _ \| | | | __ )  / ___|  / \  | |   | | | ____|  _ \| ____|  ",
                    r" | |_) | | | |  _ \ | |  _  / _ \ | |   | | |  _| | |_) |  _|   ",
                    r" |  _ <| |_| | |_) || |_| |/ ___ \| |___| | | |___|  _ <| |___  ",
                    r" |_| \_\\___/|____/ \____|/_/   \_\\_____|_|_|_____|_| \_\\_____|  "
                ]
                line_index = i - 5
                if line_index < len(gameover_art):
                    if random.random() < 0.08:  # More flicker for game over
                        art_line = self._format_terminal_line(gameover_art[line_index], terminal_width)
                        self._draw_terminal_text(art_line, 0, i, (50, 150, 50))
                    else:
                        art_line = self._format_terminal_line(gameover_art[line_index], terminal_width)
                        self._draw_terminal_text(art_line, 0, i, COLORS['wrong'])
                else:
                    empty = self._format_terminal_line("", terminal_width)
                    self._draw_terminal_text(empty, 0, i, border_color)
            elif i == 10:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 11:
                results_header = f"TRANSMISSION STATISTICS:"
                results_line = self._format_terminal_line(results_header, terminal_width)
                self._draw_terminal_text(results_line, 0, i, COLORS['text'])
            elif i == 12:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 13:
                result1 = f"OPERATOR: {state_manager.game_data.nickname}"
                result1_line = self._format_terminal_line(result1, terminal_width)
                self._draw_terminal_text(result1_line, 0, i, COLORS['text'])
            elif i == 14:
                result2 = f"WORDS TRANSMITTED: {state_manager.game_data.words_completed}"
                result2_line = self._format_terminal_line(result2, terminal_width)
                self._draw_terminal_text(result2_line, 0, i, COLORS['text'])
            elif i == 15:
                result3 = f"FINAL SCORE: {state_manager.game_data.score} POINTS"
                result3_line = self._format_terminal_line(result3, terminal_width)
                self._draw_terminal_text(result3_line, 0, i, COLORS['title'])
            elif i == 16:
                empty = self._format_terminal_line("", terminal_width)
                self._draw_terminal_text(empty, 0, i, border_color)
            elif i == 17:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 18:
                inst_header = f"AVAILABLE COMMANDS:"
                inst_line = self._format_terminal_line(inst_header, terminal_width)
                self._draw_terminal_text(inst_line, 0, i, COLORS['hint'])
            elif i == 19:
                inst1 = f"• ENTER : Return to main menu"
                inst1_line = self._format_terminal_line(inst1, terminal_width)
                self._draw_terminal_text(inst1_line, 0, i, COLORS['hint'])
            elif i == 20:
                inst2 = f"• ESC : Quit BBS"
                inst2_line = self._format_terminal_line(inst2, terminal_width)
                self._draw_terminal_text(inst2_line, 0, i, COLORS['hint'])
            elif i == 21:
                footer = f"THANK YOU FOR USING MORSE CODE BBS!"
                footer_line = self._format_terminal_line(footer, terminal_width)
                self._draw_terminal_text(footer_line, 0, i, border_color)
            elif i == terminal_height - 2:
                separator = "╠" + "═" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            else:
                empty = "║" + " " * (terminal_width - 2) + "║"
                self._draw_terminal_text(empty, 0, i, border_color)
        
        # Bottom border
        bottom_border = "╚" + "═" * (terminal_width - 2) + "╝"
        self._draw_terminal_text(bottom_border, 0, terminal_height - 1, border_color)
        
        # Draw status bar
        self._draw_status_bar(state_manager)
    
    def _draw_high_scores(self, state_manager: GameStateManager):
        """Draw high scores screen in BBS terminal style."""
        from ..data.high_scores import HighScoreManager
        
        terminal_width, terminal_height = self._get_terminal_dimensions()
        border_color = (100, 255, 100)  # Green phosphor
        
        # Add subtle screen flicker effect
        if random.random() < 0.05:  # 5% chance of flicker
            flicker_intensity = random.randint(20, 40)
            border_color = (100 - flicker_intensity, 255 - flicker_intensity, 100 - flicker_intensity)
        
        # Top border
        top_border = "╔" + "═" * (terminal_width - 2) + "╗"
        self._draw_terminal_text(top_border, 0, 0, border_color)
        
        # Content
        for i in range(1, terminal_height - 1):
            if i == 1:
                header_content = f"OPERATORS LOG - {state_manager.high_score_difficulty.upper()} MODE"
                header = self._format_terminal_line(header_content, terminal_width)
                self._draw_terminal_text(header, 0, i, COLORS['title'])
            elif i == 2:
                separator = "╠" + "═" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 3:
                status_content = "BBS: LOADING OPERATORS LOG DATA..."
                status = self._format_terminal_line(status_content, terminal_width)
                self._draw_terminal_text(status, 0, i, COLORS['text'])
            elif i == 4:
                empty = self._format_terminal_line("", terminal_width)
                self._draw_terminal_text(empty, 0, i, border_color)
            elif 5 <= i <= 9:
                # ASCII art for operators log
                scores_art = [
                    r"  ____  ____  _____ ____  _____   ____  ____  ____  ____ _____  ",
                    r" |  _ \|  _ \|_   _|  _ \| ____| | __ )|  _ \|  _ \|  _ |_   _| ",
                    r" | |_) | |_) | | | | |_) |  _|    |  _ \| |_) | | | | |_) | | |   ",
                    r" |  _ <|  __/  | | |  _ <| |___   | |_) |  __/| |_| |  _ <| | |   ",
                    r" |_| \_\_|     |_| |_| \\_\\____| |____/|_|   |____/|_| \\_\\_|  "
                ]
                line_index = i - 5
                if line_index < len(scores_art):
                    # Add phosphor glow and flicker to ASCII art
                    art_color = COLORS['title']
                    if random.random() < 0.03:  # 3% chance of bright glow
                        art_color = (255, 255, 200)  # Brighter phosphor
                    elif random.random() < 0.02:  # 2% chance of flicker
                        art_color = (200, 200, 150)  # Dimmed phosphor
                    
                    # Format with proper borders
                    art_line = self._format_terminal_line(scores_art[line_index], terminal_width)
                    self._draw_terminal_text(art_line, 0, i, art_color)
                else:
                    empty = self._format_terminal_line("", terminal_width)
                    self._draw_terminal_text(empty, 0, i, border_color)
            elif i == 10:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 11:
                scores_header_content = "RANK  OPERATOR        SCORE    ERRORS  ACCURACY"
                scores_header = self._format_terminal_line(scores_header_content, terminal_width)
                self._draw_terminal_text(scores_header, 0, i, COLORS['title'])
            elif i == 12:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif 13 <= i <= 20:
                # High scores list
                score_index = i - 13
                high_scores = HighScoreManager()
                scores = high_scores.get_top_scores(state_manager.high_score_difficulty, limit=8)
                
                if score_index < len(scores):
                    score = scores[score_index]
                    rank = score_index + 1
                    nickname = score['nickname'][:15]  # Truncate long names
                    score_val = score['score']
                    words = score['words_completed']
                    errors = score.get('errors', 0)
                    
                    # Calculate accuracy
                    total_letters = sum(len(word) for word in ['TEST'] * words)  # Approximate
                    accuracy = ((total_letters - errors) / max(total_letters, 1)) * 100 if total_letters > 0 else 100
                    
                    if rank == 1:
                        # Champion with special formatting and effects
                        score_content = f"#{rank}  {nickname:<15}  {score_val:>6}    {errors:>6}   {accuracy:>5.1f}%"
                        score_line = self._format_terminal_line(score_content, terminal_width)
                        # Add pulsing effect for champion
                        pulse_intensity = int(time.time() * 3) % 2
                        if pulse_intensity == 0:
                            champion_color = COLORS['morse']
                        else:
                            champion_color = (255, 220, 150)  # Bright amber
                        self._draw_terminal_text(score_line, 0, i, champion_color)
                    else:
                        score_content = f"#{rank}  {nickname:<15}  {score_val:>6}    {errors:>6}   {accuracy:>5.1f}%"
                        score_line = self._format_terminal_line(score_content, terminal_width)
                        # Add subtle data corruption to other scores
                        score_color = COLORS['text']
                        if random.random() < 0.015:  # 1.5% chance of corruption
                            # Simulate data corruption with character replacement
                            corrupted_line = list(score_line)
                            for j in range(len(corrupted_line)):
                                if random.random() < 0.05:  # 5% chance per character
                                    corrupted_line[j] = random.choice(["@", "#", "$", "%"])
                            score_line = "".join(corrupted_line)
                            score_color = (255, 100, 100)  # Red for corruption
                        self._draw_terminal_text(score_line, 0, i, score_color)
                else:
                    empty = self._format_terminal_line("", terminal_width)
                    self._draw_terminal_text(empty, 0, i, border_color)
            elif i == 21:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 22:
                inst_header_content = "AVAILABLE COMMANDS:"
                inst_header = self._format_terminal_line(inst_header_content, terminal_width)
                # Add subtle flicker to commands header
                self._draw_terminal_text(inst_header, 0, i, COLORS['title'])
            elif i == 23:
                inst1_content = "• TAB : Switch difficulty"
                inst1_line = self._format_terminal_line(inst1_content, terminal_width)
                self._draw_terminal_text(inst1_line, 0, i, COLORS['hint'])
            elif i == 24:
                inst2_content = "• ESC : Main menu"
                inst2_line = self._format_terminal_line(inst2_content, terminal_width)
                self._draw_terminal_text(inst2_line, 0, i, COLORS['hint'])
            elif i == terminal_height - 2:
                separator = "╠" + "═" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            else:
                empty = "║" + " " * (terminal_width - 2) + "║"
                self._draw_terminal_text(empty, 0, i, border_color)
        
        # Bottom border
        bottom_border = "╚" + "═" * (terminal_width - 2) + "╝"
        self._draw_terminal_text(bottom_border, 0, terminal_height - 1, border_color)
        
        # Draw status bar
        self._draw_status_bar(state_manager)
    
    def _draw_numbered_menu(self, state_manager: GameStateManager):
        """Draw numbered menu with Morse input support in BBS terminal style."""
        terminal_width, terminal_height = self._get_terminal_dimensions()
        border_color = (100, 255, 100)  # Green phosphor
        
        # Add subtle screen flicker effect like main menu
        if random.random() < 0.05:  # 5% chance of flicker
            flicker_intensity = random.randint(20, 40)
            border_color = (100 - flicker_intensity, 255 - flicker_intensity, 100 - flicker_intensity)
        
        # Top border
        top_border = "╔" + "═" * (terminal_width - 2) + "╗"
        self._draw_terminal_text(top_border, 0, 0, border_color)
        
        # Content
        for i in range(1, terminal_height - 1):
            if i == 1:
                header_content = "NUMBERED MENU - SELECT OPTION"
                header = self._format_terminal_line(header_content, terminal_width)
                self._draw_terminal_text(header, 0, i, COLORS['title'])
            elif i == 2:
                separator = "╠" + "═" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 3:
                status_content = "SYSTEM: USE NUMBER KEYS OR MORSE CODE TO SELECT"
                status = self._format_terminal_line(status_content, terminal_width)
                self._draw_terminal_text(status, 0, i, COLORS['text'])
            elif i == 4:
                empty = self._format_terminal_line("", terminal_width)
                self._draw_terminal_text(empty, 0, i, border_color)
            elif 5 <= i <= 9:
                # Numbered menu options with unified color palette and background highlighting
                option_index = i - 5
                if option_index < len(state_manager.numbered_menu_options):
                    option = state_manager.numbered_menu_options[option_index]
                    menu_content = f"  {option_index + 1}. {option.text}"
                    menu_line = self._format_terminal_line(menu_content, terminal_width)
                    
                    # Always create background highlight for better visibility
                    char_width, char_height = self.terminal_font.size("X")
                    
                    # Get global offset for centering
                    offset_x, offset_y = self._get_terminal_offset()
                    
                    bg_x = offset_x + (2 * char_width)
                    bg_y = offset_y + (i * char_height)
                    bg_width = (terminal_width - 4) * char_width
                    bg_height = char_height
                    
                    # Unified background for all numbered menu items
                    bg_surface = pygame.Surface((bg_width, bg_height))
                    bg_surface.set_alpha(40)  # Slightly more visible than main menu
                    bg_surface.fill(COLORS['menu_numbered_bg'])
                    self.screen.blit(bg_surface, (bg_x, bg_y))
                    
                    # Unified text color with subtle glow
                    if random.random() < 0.03:  # 3% chance of glow
                        color = (180, 255, 180)  # Green glow
                    else:
                        color = COLORS['menu_unselected_text']  # Use unified color
                    
                    self._draw_terminal_text(menu_line, 0, i, color)
                else:
                    empty = self._format_terminal_line("", terminal_width)
                    self._draw_terminal_text(empty, 0, i, border_color)
            elif i == 10:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 11:
                input_header = "ENTER SELECTION (NUMBER OR MORSE)"
                input_header_line = self._format_terminal_line(input_header, terminal_width)
                self._draw_terminal_text(input_header_line, 0, i, COLORS['text'])
            elif i == 12:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 13:
                # Morse input field with unified color palette and awesome pulsing cursor
                input_text = state_manager.morse_input
                
                # Enhanced cursor with unified color palette
                cursor_char = "_"
                cursor_color = COLORS['morse']
                
                if state_manager.cursor_visible:
                    pulse_phase = int(time.time() * 8) % 4  # Fast pulsing for cursor
                    if pulse_phase == 0:
                        cursor_char = "█"  # Full block
                        cursor_color = COLORS['menu_selected_text']  # Bright green
                    elif pulse_phase == 1:
                        cursor_char = "▓"  # Medium block
                        cursor_color = COLORS['menu_selected_border']  # Border green
                    elif pulse_phase == 2:
                        cursor_char = "▒"  # Light block
                        cursor_color = (150, 255, 150)  # Green phosphor
                    else:
                        cursor_char = "░"  # Very light block
                        cursor_color = (100, 200, 100)  # Dimmed green
                    
                    input_text += cursor_char
                
                input_display = f"║ > {input_text}{' ' * (terminal_width - len(input_text) - 5)} ║"
                
                # Add animated background for input field with unified palette
                char_width, char_height = self.terminal_font.size("X")
                
                # Get global offset for centering
                offset_x, offset_y = self._get_terminal_offset()
                
                bg_x = offset_x + (4 * char_width)  # Start after "║ > "
                bg_y = offset_y + (i * char_height)
                bg_width = len(input_text) * char_width  # Cover input text
                bg_height = char_height
                
                if state_manager.cursor_visible and bg_width > 0:
                    bg_surface = pygame.Surface((bg_width, bg_height))
                    bg_surface.set_alpha(40)  # Slightly more visible
                    bg_pulse = int(time.time() * 3) % 3
                    if bg_pulse == 0:
                        bg_surface.fill(COLORS['menu_selected_bg'])  # Green background
                    elif bg_pulse == 1:
                        bg_surface.fill(COLORS['menu_unselected_bg'])  # Dark green
                    else:
                        bg_surface.fill(COLORS['menu_border_dark'])  # Border dark
                    self.screen.blit(bg_surface, (bg_x, bg_y))
                
                # Draw the input text with unified color palette
                text_color = COLORS['morse']
                if state_manager.cursor_visible:
                    text_pulse = int(time.time() * 2) % 2
                    if text_pulse == 0:
                        text_color = (180, 255, 180)  # Green phosphor
                    else:
                        text_color = COLORS['menu_selected_border']  # Border green
                
                self._draw_terminal_text(input_display, 0, i, text_color)
            elif i == 14:
                empty = self._format_terminal_line("", terminal_width)
                self._draw_terminal_text(empty, 0, i, border_color)
            elif i == 15:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 16:
                hints_header = "MORSE CODE FOR NUMBERS:"
                hints_line = self._format_terminal_line(hints_header, terminal_width)
                self._draw_terminal_text(hints_line, 0, i, COLORS['hint'])
            elif i == 17:
                hints_content = "1: .----  2: ..---  3: ...--  4: ....-  5: ....."
                hints_line = self._format_terminal_line(hints_content, terminal_width)
                self._draw_terminal_text(hints_line, 0, i, COLORS['hint'])
            elif i == 18:
                hints_content2 = "6: -....  7: --...  8: ---..  9: ----.  0: -----"
                hints_line2 = self._format_terminal_line(hints_content2, terminal_width)
                self._draw_terminal_text(hints_line2, 0, i, COLORS['hint'])
            elif i == 19:
                separator = "╠" + "─" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            elif i == 20:
                inst_content = "ENTER: CONFIRM  C: CLEAR  ESC: BACK TO MAIN MENU"
                inst_line = self._format_terminal_line(inst_content, terminal_width)
                self._draw_terminal_text(inst_line, 0, i, COLORS['hint'])
            elif i == terminal_height - 2:
                separator = "╠" + "═" * (terminal_width - 2) + "╣"
                self._draw_terminal_text(separator, 0, i, border_color)
            else:
                empty = "║" + " " * (terminal_width - 2) + "║"
                self._draw_terminal_text(empty, 0, i, border_color)
        
        # Bottom border
        bottom_border = "╚" + "═" * (terminal_width - 2) + "╝"
        self._draw_terminal_text(bottom_border, 0, terminal_height - 1, border_color)
    
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
