"""
Контроллер мегомметра для управления аналоговой стрелкой через GPIO.
Использует GPIO 13 для PWM управления стрелкой.
"""
import time
import threading
from typing import Optional
try:
    from gpiozero import PWMOutputDevice, Button
    from gpiozero.pins.mock import MockFactory
except ImportError:
    # Mock для тестирования на платформах без Raspberry Pi
    PWMOutputDevice = None
    Button = None
    MockFactory = None


class MegohmmeterController:
    """Контроллер мегомметра для управления аналоговой стрелкой."""
    
    def __init__(self, 
                 meter_pin: int = 13, 
                 pwm_frequency: int = 1000,
                 initial_value: float = 0.0):
        """
        Инициализация контроллера мегомметра.
        
        Args:
            meter_pin: GPIO пин для управления стрелкой (PWM)
            pwm_frequency: Частота PWM для плавного движения стрелки
            initial_value: Начальное значение PWM (0.0 = минимум, 1.0 = максимум)
        """
        self.meter_pin = meter_pin
        self.pwm_frequency = pwm_frequency
        self.current_value = initial_value
        
        # Инициализация компонентов
        self.meter_device = None
        self.is_initialized = False
        
        # Поток для плавных переходов
        self.transition_thread = None
        self.transition_running = False
        self.target_value = initial_value
        
    def initialize(self) -> bool:
        """
        Инициализация GPIO компонентов.
        
        Returns:
            bool: True если инициализация прошла успешно, иначе False
        """
        try:
            if PWMOutputDevice is None:
                print("PWMOutputDevice не доступен, используем mock режим")
                self.is_initialized = False
                return False
                
            # Создаем PWM устройство для управления стрелкой
            self.meter_device = PWMOutputDevice(
                pin=self.meter_pin,
                frequency=self.pwm_frequency,
                initial_value=self.current_value
            )
            
            self.is_initialized = True
            print(f"Мегомметр инициализирован на GPIO {self.meter_pin}")
            return True
            
        except Exception as e:
            print(f"Ошибка инициализации мегомметра: {e}")
            self.is_initialized = False
            return False
    
    def set_value(self, value: float, smooth: bool = True):
        """
        Установить значение для стрелки.
        
        Args:
            value: Значение от 0.0 до 1.0
            smooth: Если True, плавный переход, иначе мгновенный
        """
        if not self.is_initialized:
            return
            
        # Ограничиваем значение в диапазоне 0.0 - 1.0
        value = max(0.0, min(1.0, value))
        self.target_value = value
        
        if smooth:
            self._smooth_transition()
        else:
            self._set_immediate(value)
    
    def _set_immediate(self, value: float):
        """Мгновенно установить значение."""
        if self.meter_device:
            self.meter_device.value = value
            self.current_value = value
    
    def _smooth_transition(self):
        """Плавный переход к целевому значению."""
        if self.transition_running:
            return
            
        self.transition_running = True
        self.transition_thread = threading.Thread(target=self._transition_worker)
        self.transition_thread.daemon = True
        self.transition_thread.start()
    
    def _transition_worker(self):
        """Рабочий поток для плавного перехода."""
        steps = 20  # Количество шагов для плавности
        step_delay = 0.02  # Задержка между шагами
        
        start_value = self.current_value
        value_diff = self.target_value - start_value
        
        for i in range(steps):
            if not self.transition_running:
                break
                
            progress = (i + 1) / steps
            new_value = start_value + (value_diff * progress)
            
            if self.meter_device:
                self.meter_device.value = new_value
                self.current_value = new_value
                
            time.sleep(step_delay)
        
        self.transition_running = False
    
    def key_pressed(self):
        """Обработчик нажатия на телеграфный ключ - стрелка на максимум."""
        self.set_value(1.0, smooth=True)
    
    def key_released(self):
        """Обработчик отпускания телеграфного ключа - стрелка на ноль."""
        self.set_value(0.0, smooth=True)
    
    def cleanup(self):
        """Очистка ресурсов."""
        self.transition_running = False
        
        if self.transition_thread and self.transition_thread.is_alive():
            self.transition_thread.join(timeout=1.0)
        
        if self.meter_device:
            self.meter_device.value = 0.0
            self.meter_device.close()
            self.meter_device = None
            
        self.is_initialized = False
        print("Ресурсы мегомметра освобождены")


class MockMegohmmeterController(MegohmmeterController):
    """Mock контроллер для тестирования без Raspberry Pi."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("Используем mock контроллер мегомметра")
    
    def initialize(self) -> bool:
        """Mock инициализация всегда успешна."""
        print(f"Mock мегомметр инициализирован на GPIO {self.meter_pin}")
        self.is_initialized = True
        return True
    
    def _set_immediate(self, value: float):
        """Mock установка значения."""
        self.current_value = value
        print(f"Mock стрелка установлена на {value:.2f}")
    
    def cleanup(self):
        """Mock очистка."""
        print("Mock ресурсы мегомметра освобождены")
        self.is_initialized = False
