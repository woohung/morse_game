"""
GPIO handler module for telegraph key input.
Supports both real GPIO input and keyboard input for testing.
"""
import time
import threading
from typing import Optional, Callable
try:
    import RPi.GPIO as GPIO
except ImportError:
    # Mock GPIO for testing on non-RPi platforms
    GPIO = None
    
class GPIOHandler:
    """Handles GPIO input for telegraph key with keyboard fallback."""
    
    def __init__(self, pin: int, on_press: Callable, on_release: Callable, 
                 input_mode: str = 'auto'):
        self.pin = pin
        self.on_press = on_press
        self.on_release = on_release
        self.input_mode = input_mode  # 'auto', 'keyboard', or 'gpio'
        self.is_pressed = False
        self.press_start_time = 0
        self.thread = None
        self.running = True
        
    def start(self):
        """Start the GPIO handler."""
        if self.input_mode == 'keyboard':
            print("Using keyboard input mode")
            return
            
        if GPIO is None:
            print("GPIO not available, using keyboard input for testing")
            self.input_mode = 'keyboard'
            return
            
        print(f"Using GPIO input mode on pin {self.pin}")
        
        # Set up GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Start monitoring thread
        self.thread = threading.Thread(target=self._monitor_gpio, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the GPIO handler."""
        self.running = False
        if self.thread:
            self.thread.join()
        if GPIO:
            GPIO.cleanup()
    
    def _monitor_gpio(self):
        """Monitor GPIO pin for key presses."""
        last_state = GPIO.input(self.pin)
        
        while self.running:
            current_state = GPIO.input(self.pin)
            
            # Detect state change
            if current_state != last_state:
                if current_state == GPIO.LOW:  # Key pressed
                    self.is_pressed = True
                    self.press_start_time = time.time()
                    if self.on_press:
                        self.on_press()
                elif current_state == GPIO.HIGH:  # Key released
                    if self.is_pressed:
                        press_duration = time.time() - self.press_start_time
                        if self.on_release:
                            self.on_release(press_duration)
                    self.is_pressed = False
                
                last_state = current_state
            
            time.sleep(0.01)  # Small delay to prevent CPU overload
    
    def set_mode(self, mode: str):
        """Switch between input modes."""
        if mode in ['auto', 'keyboard', 'gpio']:
            self.input_mode = mode
            if mode == 'keyboard':
                print("Switched to keyboard mode")
            elif mode == 'gpio':
                print(f"Switched to GPIO mode on pin {self.pin}")
            elif mode == 'auto':
                print("Auto-detecting input mode")
                self.input_mode = 'keyboard' if GPIO is None else 'gpio'
    
    def cleanup(self):
        """Clean up GPIO resources."""
        if GPIO:
            GPIO.cleanup()


class MockGPIOHandler(GPIOHandler):
    """Mock GPIO handler for testing without a Raspberry Pi."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pygame.init()
        self._screen = pygame.display.set_mode((100, 100))
        pygame.display.set_caption("Morse Tester (Press ESC to quit)")
    
    def _read_gpio(self) -> bool:
        """Read keyboard input for testing."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._running = False
                    return False
        
        keys = pygame.key.get_pressed()
        return keys[pygame.K_SPACE]
    
    def cleanup(self):
        """Clean up resources."""
        super().cleanup()
        pygame.quit()
