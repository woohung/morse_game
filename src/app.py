"""
Main Morse Code Game Application
Refactored with proper separation of concerns.
"""
import pygame
import sys
import signal
from typing import Optional

# Import application components
from .core.game_state import GameStateManager
from .core.game_controller import GameController
from .core.config import SCREEN_WIDTH, SCREEN_HEIGHT, init_display
from .ui.renderer import UIRenderer
from .input.gpio_handler import GPIOHandler
from .input.event_handler import EventHandler


class MorseApp:
    """Main application class with proper separation of concerns."""
    
    def __init__(self, fullscreen=True, input_mode='auto'):
        pygame.init()
        self.fullscreen = fullscreen
        self.input_mode = input_mode
        self.running = True
        
        # Initialize display
        self._setup_display()
        
        # Initialize components
        self.state_manager = GameStateManager()
        self.game_controller = GameController(self.state_manager)
        self.ui_renderer = UIRenderer(self.screen)
        
        # Initialize GPIO handler
        self.gpio_handler = GPIOHandler(
            pin=17,  # Default GPIO pin
            on_press=self.game_controller.on_key_press,
            on_release=self.game_controller.on_key_release,
            input_mode=input_mode
        )
        
        # Initialize event handler
        self.event_handler = EventHandler(
            self.state_manager,
            self.game_controller,
            self.gpio_handler
        )
        
        # Clock for frame rate control
        self.clock = pygame.time.Clock()
    
    def _setup_display(self):
        """Set up the display based on configuration."""
        if self.fullscreen:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        pygame.display.set_caption("Morse Code Game")
        pygame.mouse.set_visible(False)
    
    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode."""
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode(
                (SCREEN_WIDTH, SCREEN_HEIGHT), 
                pygame.FULLSCREEN
            )
        else:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    
    def run(self):
        """Main application loop."""
        try:
            # Start GPIO handler
            self.gpio_handler.start()
            
            while self.running:
                # Process events
                if not self.event_handler.process_events():
                    self.running = False
                
                # Handle F11 for fullscreen toggle
                keys = pygame.key.get_pressed()
                if keys[pygame.K_F11]:
                    self.toggle_fullscreen()
                
                # Check game timeouts
                self.game_controller.check_timeouts()
                
                # Update display
                self.ui_renderer.render(self.state_manager, self.game_controller.current_sequence)
                
                # Control frame rate
                self.clock.tick(30)
                
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        self.gpio_handler.stop()
        pygame.quit()


def create_signal_handler():
    """Create signal handler for clean exit."""
    def signal_handler(sig, frame):
        print("\nExiting...")
        pygame.quit()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    return signal_handler


def parse_arguments():
    """Parse command line arguments."""
    fullscreen = True
    input_mode = 'auto'
    debug_mode = False
    
    if "--window" in sys.argv:
        fullscreen = False
    
    if "--gpio" in sys.argv:
        input_mode = 'gpio'
    elif "--keyboard" in sys.argv:
        input_mode = 'keyboard'
    
    debug_mode = "--debug" in sys.argv or "--debug=True" in sys.argv
    
    return fullscreen, input_mode, debug_mode


def main():
    """Main entry point."""
    # Set up signal handler
    create_signal_handler()
    
    # Parse command line arguments
    fullscreen, input_mode, debug_mode = parse_arguments()
    
    # Initialize display settings
    init_display()
    
    try:
        app = MorseApp(fullscreen=fullscreen, input_mode=input_mode)
        app.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()
        sys.exit(1)


if __name__ == "__main__":
    main()
