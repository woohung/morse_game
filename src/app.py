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
from .core.config import (SCREEN_WIDTH, SCREEN_HEIGHT, init_display, 
                          TARGET_FPS, ENABLE_CRT_EFFECT, ENABLE_NEON_EFFECTS,
                          FULLSCREEN_SCALE, USE_HARDWARE_ACCELERATION, ENABLE_VSYNC, 
                          USE_DOUBLE_BUFFERING, SMOOTH_STARTUP)
from .ui.renderer import UIRenderer
from .input.gpio_handler import GPIOHandler
from .input.event_handler import EventHandler


def update_performance_settings(args):
    """Update performance settings based on command line arguments."""
    global TARGET_FPS, ENABLE_CRT_EFFECT, ENABLE_NEON_EFFECTS
    global USE_HARDWARE_ACCELERATION, ENABLE_VSYNC, USE_DOUBLE_BUFFERING, SMOOTH_STARTUP
    
    if "--low-fps" in args:
        TARGET_FPS = 10
        print("Low FPS mode enabled (10 FPS)")
    
    if "--no-crt" in args:
        ENABLE_CRT_EFFECT = False
        print("CRT effect disabled")
    
    if "--no-neon" in args:
        ENABLE_NEON_EFFECTS = False
        print("Neon effects disabled")
    
    if "--high-performance" in args:
        TARGET_FPS = 15
        ENABLE_CRT_EFFECT = False
        ENABLE_NEON_EFFECTS = False
        USE_HARDWARE_ACCELERATION = True
        ENABLE_VSYNC = True
        USE_DOUBLE_BUFFERING = True
        print("High performance mode enabled")
    
    if "--no-hw-accel" in args:
        USE_HARDWARE_ACCELERATION = False
        print("Hardware acceleration disabled")
    
    if "--no-vsync" in args:
        ENABLE_VSYNC = False
        print("VSync disabled")
    
    if "--no-smooth-startup" in args:
        SMOOTH_STARTUP = False
        print("Smooth startup disabled")


class MorseApp:
    """Main application class with proper separation of concerns."""
    
    def __init__(self, fullscreen=True, input_mode='auto'):
        # Initialize pygame with minimal settings first to avoid flickering
        pygame.init()
        pygame.display.init()
        pygame.font.init()
        
        self.fullscreen = fullscreen
        self.input_mode = input_mode
        self.running = True
        
        # Initialize display first
        self._setup_display()
        
        # Initialize components
        self.state_manager = GameStateManager()
        self.game_controller = GameController(self.state_manager)
        self.ui_renderer = UIRenderer(self.screen)
        
        # Set render surface if using scaling
        if hasattr(self, 'render_surface') and self.render_surface:
            self.ui_renderer.set_render_surface(self.render_surface)
        
        # Initialize GPIO handler
        self.gpio_handler = GPIOHandler(
            pin=17,  # Default GPIO pin
            on_press=self._on_gpio_press,
            on_release=self._on_gpio_release,
            input_mode=input_mode,
            bounce_time=0.05  # 50ms debounce time for telegraph key
        )
        
        # Initialize event handler
        self.event_handler = EventHandler(
            self.state_manager,
            self.game_controller,
            self.gpio_handler
        )
        
        # Clock for frame rate control
        self.clock = pygame.time.Clock()
        self.target_fps = TARGET_FPS
    
    def _setup_display(self):
        """Set up the display based on configuration with proper scaling and smooth initialization."""
        from .core.config import SCREEN_INFO, FULLSCREEN_SCALE
        
        # Set up display flags for performance
        flags = 0
        if USE_HARDWARE_ACCELERATION:
            flags |= pygame.HWSURFACE
        if USE_DOUBLE_BUFFERING:
            flags |= pygame.DOUBLEBUF
        
        # Initialize display once to avoid flickering
        if self.fullscreen:
            # For fullscreen, use actual display resolution but scale our content
            actual_width = SCREEN_INFO.current_w if SCREEN_INFO else SCREEN_WIDTH
            actual_height = SCREEN_INFO.current_h if SCREEN_INFO else SCREEN_HEIGHT
            
            if FULLSCREEN_SCALE > 1.0:
                # High-res display: use native resolution for scaling
                self.screen = pygame.display.set_mode((actual_width, actual_height), pygame.FULLSCREEN | flags)
                self.render_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                print(f"Fullscreen mode: {actual_width}x{actual_height} with {SCREEN_WIDTH}x{SCREEN_HEIGHT} render surface")
            else:
                # Standard resolution: use our target resolution directly
                self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | flags)
                self.render_surface = None
                print(f"Fullscreen mode: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
        else:
            # Windowed mode: always use our target resolution
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
            self.render_surface = None
            print(f"Windowed mode: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
        
        # Set caption and hide mouse once
        pygame.display.set_caption("Morse Code Game")
        pygame.mouse.set_visible(False)
        
        # Clear screen to black to avoid flickering
        self.screen.fill((0, 0, 0))
        pygame.display.flip()
        
        # Small delay to ensure display is stable (only if smooth startup enabled)
        if SMOOTH_STARTUP:
            pygame.time.wait(100)
    
    def _on_gpio_press(self):
        """Handle GPIO key press - route to appropriate controller based on game state."""
        from .core.game_state import GameState
        
        print(f"GPIO Press: текущее состояние = {self.state_manager.current_state}")
        
        if self.state_manager.current_state == GameState.PLAYING:
            print("GPIO Press: маршрутизация в on_key_press (игра)")
            self.game_controller.on_key_press()
        elif self.state_manager.current_state == GameState.PRACTICE:
            print("GPIO Press: маршрутизация в on_practice_key_press (практика)")
            self.game_controller.on_practice_key_press()
        else:
            print("GPIO Press: состояние не требует обработки")
    
    def _on_gpio_release(self, press_duration: float):
        """Handle GPIO key release - route to appropriate controller based on game state."""
        from .core.game_state import GameState
        
        print(f"GPIO Release: текущее состояние = {self.state_manager.current_state}, длительность = {press_duration:.3f}s")
        
        if self.state_manager.current_state == GameState.PLAYING:
            print("GPIO Release: маршрутизация в on_key_release (игра)")
            self.game_controller.on_key_release(press_duration)
        elif self.state_manager.current_state == GameState.PRACTICE:
            print("GPIO Release: маршрутизация в on_practice_key_release (практика)")
            self.game_controller.on_practice_key_release(press_duration)
        else:
            print("GPIO Release: состояние не требует обработки")
    
    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode."""
        self.fullscreen = not self.fullscreen
        self._setup_display()  # Re-setup display with new mode
        
        # Update renderer with new render surface if needed
        if hasattr(self, 'render_surface') and self.render_surface:
            self.ui_renderer.set_render_surface(self.render_surface)
        else:
            self.ui_renderer.set_render_surface(None)
    
    def run(self):
        """Main application loop."""
        try:
            # Start GPIO handler
            self.gpio_handler.start()
            
            # Small delay to ensure everything is stable before first render (only if smooth startup enabled)
            if SMOOTH_STARTUP:
                pygame.time.wait(200)
            
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
                
                # Handle scaling for high-res displays
                if hasattr(self, 'render_surface') and self.render_surface:
                    # Scale our render surface to fit the actual screen
                    scaled_surface = pygame.transform.scale(self.render_surface, 
                                                          (self.screen.get_width(), self.screen.get_height()))
                    self.screen.blit(scaled_surface, (0, 0))
                
                pygame.display.flip()
                
                # Control frame rate
                self.clock.tick(self.target_fps)
                
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
    
    # Update performance settings based on arguments
    update_performance_settings(sys.argv)
    
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
