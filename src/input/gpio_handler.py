"""
GPIO handler module for telegraph key input.
Supports both real GPIO input and keyboard input for testing.
"""
import time
import threading
from typing import Optional, Callable
try:
    from gpiozero import Button
    from gpiozero.pins.mock import MockFactory
except ImportError:
    # Mock gpiozero for testing on non-RPi platforms
    Button = None
    MockFactory = None
    
class GPIOHandler:
    """Handles GPIO input for telegraph key with keyboard fallback."""
    
    def __init__(self, pin: int, on_press: Callable, on_release: Callable, 
                 input_mode: str = 'auto', bounce_time: float = 0.05):
        self.pin = pin
        self.on_press = on_press
        self.on_release = on_release
        self.input_mode = input_mode  # 'auto', 'keyboard', or 'gpio'
        self.bounce_time = bounce_time  # Debounce time in seconds
        self.is_pressed = False
        self.press_start_time = 0
        self.thread = None
        self.running = True
        self.button = None
        
    def start(self):
        """Start the GPIO handler."""
        if self.input_mode == 'keyboard':
            print("Using keyboard input mode")
            return
            
        if Button is None:
            print("gpiozero not available, using keyboard input for testing")
            self.input_mode = 'keyboard'
            return
            
        print(f"Using GPIO input mode on pin {self.pin}")
        
        try:
            # Set up button using gpiozero with debouncing
            self.button = Button(self.pin, pull_up=True, bounce_time=self.bounce_time)
            self.button.when_pressed = self._on_button_press
            self.button.when_released = self._on_button_release
        except Exception as e:
            print(f"Failed to initialize GPIO: {e}")
            print("Falling back to keyboard input mode")
            self.input_mode = 'keyboard'
    
    def stop(self):
        """Stop the GPIO handler."""
        self.running = False
        if self.thread:
            self.thread.join()
        if self.button:
            self.button.close()
    
    def _on_button_press(self):
        """Handle button press event."""
        print(f"GPIO: Ключ нажат (pin {self.pin})")
        self.is_pressed = True
        self.press_start_time = time.time()
        if self.on_press:
            self.on_press()
    
    def _on_button_release(self):
        """Handle button release event."""
        print(f"GPIO: Ключ отпущен (pin {self.pin}), длительность: {time.time() - self.press_start_time:.3f}s")
        if self.is_pressed:
            press_duration = time.time() - self.press_start_time
            if self.on_release:
                self.on_release(press_duration)
        self.is_pressed = False
    
    def set_mode(self, mode: str):
        """Switch between input modes."""
        if mode in ['auto', 'keyboard', 'gpio']:
            self.input_mode = mode
            if mode == 'keyboard':
                print("Switched to keyboard mode")
                if self.button:
                    self.button.close()
                    self.button = None
            elif mode == 'gpio':
                print(f"Switched to GPIO mode on pin {self.pin}")
                self.start()
            elif mode == 'auto':
                print("Auto-detecting input mode")
                self.input_mode = 'keyboard' if Button is None else 'gpio'
                if self.input_mode == 'gpio':
                    self.start()
    
    def reset_state(self):
        """Reset the pressed state to prevent accidental key press detection."""
        self.is_pressed = False
        self.press_start_time = 0
        print("GPIO: состояние ключа сброшено")
    
    def cleanup(self):
        """Clean up GPIO resources."""
        if self.button:
            self.button.close()
            self.button = None


class MockGPIOHandler(GPIOHandler):
    """Mock GPIO handler for testing without a Raspberry Pi."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            import pygame
            pygame.init()
            self._screen = pygame.display.set_mode((100, 100))
            pygame.display.set_caption("Morse Tester (Press ESC to quit)")
            self._running = True
            
            # Start keyboard monitoring thread
            self.thread = threading.Thread(target=self._monitor_keyboard, daemon=True)
            self.thread.start()
        except ImportError:
            print("pygame not available for mock GPIO handler")
            self._running = False
    
    def _monitor_keyboard(self):
        """Monitor keyboard input for testing."""
        import pygame
        
        last_pressed = False
        
        while self.running and self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                    return
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._running = False
                        return
            
            keys = pygame.key.get_pressed()
            current_pressed = keys[pygame.K_SPACE]
            
            # Detect state change
            if current_pressed != last_pressed:
                if current_pressed:  # Space pressed
                    self._on_button_press()
                else:  # Space released
                    self._on_button_release()
                
                last_pressed = current_pressed
            
            pygame.time.wait(10)  # Small delay to prevent CPU overload
    
    def cleanup(self):
        """Clean up resources."""
        super().cleanup()
        try:
            import pygame
            pygame.quit()
        except ImportError:
            pass
