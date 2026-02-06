"""
Event Handler for Morse Code Game
Handles all pygame events and user input.
"""
import pygame
import time
from typing import Callable, Optional
from ..core.game_state import GameStateManager, GameState


class EventHandler:
    """Handles pygame events and user input."""
    
    def __init__(self, state_manager: GameStateManager, game_controller, gpio_handler):
        self.state_manager = state_manager
        self.game_controller = game_controller
        self.gpio_handler = gpio_handler
        self.space_pressed = False
        self.space_press_time = 0
    
    def process_events(self) -> bool:
        """Process all pygame events. Returns False if application should quit."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            elif event.type == pygame.KEYDOWN:
                if not self._handle_keydown(event):
                    return False
            
            elif event.type == pygame.KEYUP:
                self._handle_keyup(event)
        
        return True
    
    def _handle_keydown(self, event) -> bool:
        """Handle key down events. Returns False if application should quit."""
        if self.state_manager.current_state == GameState.MAIN_MENU:
            return self._handle_menu_events(event)
        elif self.state_manager.current_state == GameState.NUMBERED_MENU:
            return self._handle_numbered_menu_events(event)
        elif self.state_manager.current_state == GameState.DIFFICULTY_SELECT:
            return self._handle_difficulty_events(event)
        elif self.state_manager.current_state == GameState.NICKNAME_INPUT:
            return self._handle_nickname_events(event)
        elif self.state_manager.current_state == GameState.READY:
            return self._handle_ready_events(event)
        elif self.state_manager.current_state == GameState.PLAYING:
            return self._handle_game_events(event)
        elif self.state_manager.current_state == GameState.PRACTICE:
            return self._handle_practice_events(event)
        elif self.state_manager.current_state == GameState.GAME_OVER:
            return self._handle_game_over_events(event)
        elif self.state_manager.current_state == GameState.HIGH_SCORES:
            return self._handle_high_scores_events(event)
        
        return True
    
    def _handle_keyup(self, event):
        """Handle key up events."""
        if self.state_manager.current_state == GameState.PLAYING:
            if event.key == pygame.K_SPACE and self.gpio_handler.input_mode == 'keyboard':
                # Handle space bar release for Morse input
                if self.space_pressed:
                    self.space_pressed = False
                    press_duration = time.time() - self.space_press_time
                    self.game_controller.on_key_release(press_duration)
        elif self.state_manager.current_state == GameState.PRACTICE:
            if event.key == pygame.K_SPACE and self.gpio_handler.input_mode == 'keyboard':
                # Handle space bar release for Morse input in practice mode
                if self.space_pressed:
                    self.space_pressed = False
                    press_duration = time.time() - self.space_press_time
                    self.game_controller.on_practice_key_release(press_duration)
        elif self.state_manager.current_state == GameState.NUMBERED_MENU:
            if event.key == pygame.K_SPACE:
                # Handle space bar release for Morse input in numbered menu
                if self.space_pressed:
                    self.space_pressed = False
                    press_duration = time.time() - self.space_press_time
                    # Add Morse character based on press duration
                    if press_duration < 0.2:  # Short press = dot
                        self.state_manager.add_morse_char('.')
                    else:  # Long press = dash
                        self.state_manager.add_morse_char('-')
    
    def _handle_menu_events(self, event) -> bool:
        """Handle events in main menu."""
        if event.key == pygame.K_ESCAPE:
            return False
        elif event.key == pygame.K_UP:
            self.state_manager.move_menu_selection(-1)
        elif event.key == pygame.K_DOWN:
            self.state_manager.move_menu_selection(1)
        elif event.key == pygame.K_RETURN:
            action = self.state_manager.get_selected_menu_action()
            if action == "start":
                self.state_manager.change_state(GameState.DIFFICULTY_SELECT)
            elif action == "practice":
                self.game_controller.start_practice_mode()
            elif action == "high_scores":
                self.state_manager.change_state(GameState.HIGH_SCORES)
            elif action == "exit":
                return False
        elif event.key == pygame.K_n:
            # Switch to numbered menu
            self.state_manager.change_state(GameState.NUMBERED_MENU)
        elif event.key == pygame.K_F11:
            # This will be handled by the main app
            pass
        
        return True
    
    def _handle_difficulty_events(self, event) -> bool:
        """Handle events in difficulty selection menu."""
        if event.key == pygame.K_ESCAPE:
            self.state_manager.change_state(GameState.MAIN_MENU)
        elif event.key == pygame.K_UP:
            self.state_manager.move_menu_selection(-1)
        elif event.key == pygame.K_DOWN:
            self.state_manager.move_menu_selection(1)
        elif event.key == pygame.K_RETURN:
            action = self.state_manager.get_selected_menu_action()
            if action in ["easy", "hard"]:
                self.state_manager.set_difficulty(action)
                self.state_manager.change_state(GameState.NICKNAME_INPUT)
            elif action == "back":
                self.state_manager.change_state(GameState.MAIN_MENU)
        
        return True
    
    def _handle_nickname_events(self, event) -> bool:
        """Handle events in nickname input screen."""
        if event.key == pygame.K_ESCAPE:
            self.state_manager.change_state(GameState.MAIN_MENU)
        elif event.key == pygame.K_RETURN:
            if self.state_manager.confirm_nickname():
                self.game_controller.start_new_game()
        elif event.key == pygame.K_BACKSPACE:
            self.state_manager.remove_nickname_char()
        elif event.key == pygame.K_F11:
            # This will be handled by the main app
            pass
        else:
            # Add character to nickname
            char = event.unicode
            if char.isalnum() or char in "-_":
                self.state_manager.add_nickname_char(char)
        
        return True
    
    def _handle_ready_events(self, event) -> bool:
        """Handle events in ready screen."""
        if event.key == pygame.K_ESCAPE:
            self.state_manager.change_state(GameState.MAIN_MENU)
        elif event.key == pygame.K_SPACE:
            # Start game when space is pressed
            self.game_controller.on_space_press()
        
        return True
    
    def _handle_game_events(self, event) -> bool:
        """Handle events during gameplay."""
        if event.key == pygame.K_F11:
            # This will be handled by the main app
            pass
        elif event.key == pygame.K_c:
            self.game_controller.clear_current_input()
        elif event.key == pygame.K_SPACE:
            # Handle space bar for Morse input when in keyboard mode
            if self.gpio_handler.input_mode == 'keyboard':
                # Simulate key press for Morse input
                if not self.space_pressed:
                    self.space_pressed = True
                    self.space_press_time = time.time()
                    self.game_controller.on_key_press()
        
        return True
    
    def _handle_game_over_events(self, event) -> bool:
        """Handle events in game over screen."""
        if event.key == pygame.K_ESCAPE:
            return False
        elif event.key == pygame.K_RETURN:
            self.state_manager.change_state(GameState.MAIN_MENU)
        elif event.key == pygame.K_F11:
            # This will be handled by the main app
            pass
        
        return True
    
    def _handle_high_scores_events(self, event) -> bool:
        """Handle events in high scores screen."""
        if event.key == pygame.K_ESCAPE:
            self.state_manager.change_state(GameState.MAIN_MENU)
        elif event.key == pygame.K_TAB:
            self.state_manager.switch_high_score_difficulty()
        elif event.key == pygame.K_F11:
            # This will be handled by the main app
            pass
        
        return True
    
    def _handle_numbered_menu_events(self, event) -> bool:
        """Handle events in numbered menu with Morse input support."""
        if event.key == pygame.K_ESCAPE:
            self.state_manager.change_state(GameState.MAIN_MENU)
        elif event.key == pygame.K_RETURN:
            # Process the selection
            action = self.state_manager.process_numbered_menu_selection()
            if action:
                if action == "start":
                    self.state_manager.change_state(GameState.DIFFICULTY_SELECT)
                elif action == "high_scores":
                    self.state_manager.change_state(GameState.HIGH_SCORES)
                elif action == "settings":
                    # TODO: Implement settings screen
                    pass
                elif action == "help":
                    # TODO: Implement help screen
                    pass
                elif action == "exit":
                    return False
            else:
                # Invalid selection - clear input
                self.state_manager.clear_morse_input()
        elif event.key == pygame.K_c:
            # Clear input
            self.state_manager.clear_morse_input()
        elif event.key == pygame.K_BACKSPACE:
            # Remove last character
            if self.state_manager.morse_input:
                self.state_manager.morse_input = self.state_manager.morse_input[:-1]
        elif event.key == pygame.K_SPACE:
            # Handle space for Morse input (simulated)
            if not self.space_pressed:
                self.space_pressed = True
                self.space_press_time = time.time()
        elif event.key == pygame.K_F11:
            # This will be handled by the main app
            pass
        else:
            # Handle number keys directly
            if pygame.K_1 <= event.key <= pygame.K_9:
                number = event.key - pygame.K_0  # Convert to actual number
                action = self.state_manager.get_numbered_menu_action_by_number(number)
                if action:
                    if action == "start":
                        self.state_manager.change_state(GameState.DIFFICULTY_SELECT)
                    elif action == "high_scores":
                        self.state_manager.change_state(GameState.HIGH_SCORES)
                    elif action == "settings":
                        # TODO: Implement settings screen
                        pass
                    elif action == "help":
                        # TODO: Implement help screen
                        pass
                    elif action == "exit":
                        return False
            elif event.key == pygame.K_0:
                action = self.state_manager.get_numbered_menu_action_by_number(0)
                if action:
                    # Handle 0 key if needed
                    pass
        
        return True
    
    def _handle_practice_events(self, event) -> bool:
        """Handle events in practice mode."""
        if event.key == pygame.K_ESCAPE:
            self.state_manager.change_state(GameState.MAIN_MENU)
        elif event.key == pygame.K_F11:
            # This will be handled by the main app
            pass
        elif event.key == pygame.K_c:
            # Clear input
            self.game_controller.clear_practice_input()
        elif event.key == pygame.K_SPACE:
            # Handle space bar for Morse input when in keyboard mode
            if self.gpio_handler.input_mode == 'keyboard':
                # Simulate key press for Morse input
                if not self.space_pressed:
                    self.space_pressed = True
                    self.space_press_time = time.time()
                    self.game_controller.on_practice_key_press()
        
        return True
