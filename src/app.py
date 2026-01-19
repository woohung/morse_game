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
                          TARGET_FPS, ENABLE_CRT_EFFECT, ENABLE_NEON_EFFECTS)
from .ui.renderer import UIRenderer
from .input.gpio_handler import GPIOHandler
from .input.event_handler import EventHandler


def update_performance_settings(args):
    """Update performance settings based on command line arguments."""
    global TARGET_FPS, ENABLE_CRT_EFFECT, ENABLE_NEON_EFFECTS
    
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
        print("High performance mode enabled")


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
        """Set up display based on configuration and platform."""
        from .config import (RPI_FULLSCREEN, RPI_NATIVE_RESOLUTION, RPI_SCALING,
                          RPI_HARDWARE_ACCEL, RPI_DOUBLE_BUFFER, RPI_VSYNC)
        
        # Check if running on Raspberry Pi
        is_rpi = self._is_raspberry_pi()
        
        if is_rpi and RPI_NATIVE_RESOLUTION:
            # Get native display resolution on RPi
            info = pygame.display.Info()
            native_width = info.current_w
            native_height = info.current_h
            
            print(f"RPi detected: native resolution {native_width}x{native_height}")
            
            # Set up display flags for RPi
            flags = pygame.FULLSCREEN if RPI_FULLSCREEN else 0
            if RPI_HARDWARE_ACCEL:
                flags |= pygame.HWSURFACE
            if RPI_DOUBLE_BUFFER:
                flags |= pygame.DOUBLEBUF
            
            self.screen = pygame.display.set_mode((native_width, native_height), flags)
            
            # Apply scaling if needed
            if RPI_SCALING != 1.0:
                self.screen = pygame.transform.scale(self.screen, 
                    (int(native_width * RPI_SCALING), 
                     int(native_height * RPI_SCALING)))
        else:
            # Standard display setup for non-RPi or windowed mode
            if self.fullscreen:
                self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
            else:
                self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        pygame.display.set_caption("Morse Code Game")
        pygame.mouse.set_visible(False)
    
    def _is_raspberry_pi(self):
        """Check if running on Raspberry Pi."""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                return 'BCM2835' in cpuinfo or 'BCM2711' in cpuinfo
        except:
            return False
    
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
