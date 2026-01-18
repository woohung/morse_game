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
                 key_pin: int = 17,
                 pwm_frequency: int = 1000,
                 initial_value: float = 0.0):
        """
        Инициализация контроллера мегомметра.
        
        Args:
            meter_pin: GPIO пин для управления стрелкой (PWM)
            key_pin: GPIO пин для телеграфного ключа
            pwm_frequency: Частота PWM для плавного движения стрелки
            initial_value: Начальное значение PWM (0.0 = минимум, 1.0 = максимум)
        """
        self.meter_pin = meter_pin
        self.key_pin = key_pin
        self.pwm_frequency = pwm_frequency
        self.current_value = initial_value
        
        # Инициализация компонентов
        self.meter_device = None
        self.key_button = None
        self.is_initialized = False
        self.is_key_pressed = False
        
        # Поток для плавных переходов
        self.transition_thread = None
        self.transition_running = False
        self.target_value = initial_value
        
    def initialize(self) -> bool:
        """
        Инициализация GPIO компонентов.
        
        Returns:
            bool: True если инициализация прошла успешно, False в противном случае
        """
        try:
            if PWMOutputDevice is None or Button is None:
                print("GPIO компоненты недоступны, используем режим симуляции")
                self.is_initialized = True
                return True
                
            # Инициализация PWM устройства для стрелки
            self.meter_device = PWMOutputDevice(
                pin=self.meter_pin,
                frequency=self.pwm_frequency,
                initial_value=self.current_value
            )
            
            # Инициализация кнопки для телеграфного ключа
            self.key_button = Button(
                pin=self.key_pin,
                pull_up=True,
                bounce_time=0.01
            )
            
            # Назначение обработчиков событий
            self.key_button.when_pressed = self._on_key_pressed
            self.key_button.when_released = self._on_key_released
            
            self.is_initialized = True
            print(f"Мегомметр инициализирован: пин стрелки={self.meter_pin}, пин ключа={self.key_pin}")
            return True
            
        except Exception as e:
            print(f"Ошибка инициализации мегомметра: {e}")
            return False
    
    def _on_key_pressed(self):
        """Обработчик нажатия на телеграфный ключ."""
        self.is_key_pressed = True
        self.set_value(1.0)  # Максимальное отклонение стрелки
        print("Ключ нажат - стрелка на максимуме")
    
    def _on_key_released(self):
        """Обработчик отпускания телеграфного ключа."""
        self.is_key_pressed = False
        self.set_value(0.0)  # Стрелка возвращается в ноль
        print("Ключ отпущен - стрелка в нуле")
    
    def set_value(self, value: float, smooth: bool = True):
        """
        Установить значение для стрелки.
        
        Args:
            value: Значение от 0.0 до 1.0
            smooth: Если True, плавный переход, если False - немедленная установка
        """
        value = max(0.0, min(1.0, value))  # Ограничение диапазона
        
        if not smooth or not self.is_initialized:
            self.current_value = value
            if self.meter_device:
                self.meter_device.value = value
            return
        
        # Запуск плавного перехода
        self.target_value = value
        if not self.transition_running:
            self._start_smooth_transition()
    
    def _start_smooth_transition(self):
        """Запустить поток плавного перехода."""
        if self.transition_thread and self.transition_thread.is_alive():
            return
        
        self.transition_running = True
        self.transition_thread = threading.Thread(target=self._smooth_transition_worker)
        self.transition_thread.daemon = True
        self.transition_thread.start()
    
    def _smooth_transition_worker(self):
        """Рабочий поток для плавного перехода значения."""
        step_size = 0.02  # Шаг изменения значения
        delay = 0.01      # Задержка между шагами
        
        while self.transition_running:
            diff = self.target_value - self.current_value
            
            if abs(diff) < step_size:
                self.current_value = self.target_value
                if self.meter_device:
                    self.meter_device.value = self.current_value
                break
            
            # Плавное изменение значения
            if diff > 0:
                self.current_value += step_size
            else:
                self.current_value -= step_size
            
            self.current_value = max(0.0, min(1.0, self.current_value))
            
            if self.meter_device:
                self.meter_device.value = self.current_value
            
            time.sleep(delay)
        
        self.transition_running = False
    
    def get_current_value(self) -> float:
        """Получить текущее значение стрелки."""
        return self.current_value
    
    def is_key_active(self) -> bool:
        """Проверить, нажат ли ключ в данный момент."""
        return self.is_key_pressed
    
    def cleanup(self):
        """Очистка ресурсов GPIO."""
        if self.transition_running:
            self.transition_running = False
            if self.transition_thread and self.transition_thread.is_alive():
                self.transition_thread.join(timeout=0.5)
        
        if self.meter_device:
            self.meter_device.value = 0.0
            self.meter_device.close()
            self.meter_device = None
        
        if self.key_button:
            self.key_button.close()
            self.key_button = None
        
        self.is_initialized = False
        print("Ресурсы мегомметра освобождены")


class MockMegohmmeterController(MegohmmeterController):
    """Mock версия контроллера для тестирования без GPIO."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("Используется Mock контроллер мегомметра (симуляция)")
    
    def initialize(self) -> bool:
        """Инициализация mock контроллера."""
        self.is_initialized = True
        print("Mock мегомметр инициализирован")
        return True
    
    def set_value(self, value: float, smooth: bool = True):
        """Установить значение в режиме симуляции."""
        self.current_value = max(0.0, min(1.0, value))
        print(f"Mock стрелка: {self.current_value:.2f}")
    
    def _on_key_pressed(self):
        """Mock обработчик нажатия."""
        self.is_key_pressed = True
        self.set_value(1.0)
        print("Mock: ключ нажат")
    
    def _on_key_released(self):
        """Mock обработчик отпускания."""
        self.is_key_pressed = False
        self.set_value(0.0)
        print("Mock: ключ отпущен")


def create_megohmmeter_controller(meter_pin: int = 13, key_pin: int = 17, 
                                 use_mock: bool = None) -> MegohmmeterController:
    """
    Создать экземпляр контроллера мегомметра.
    
    Args:
        meter_pin: GPIO пин для стрелки
        key_pin: GPIO пин для ключа
        use_mock: Принудительно использовать mock. Если None, автоопределение
    
    Returns:
        MegohmmeterController: Экземпляр контроллера
    """
    if use_mock is None:
        # Автоопределение необходимости mock
        use_mock = PWMOutputDevice is None or Button is None
    
    if use_mock:
        return MockMegohmmeterController(meter_pin=meter_pin, key_pin=key_pin)
    else:
        return MegohmmeterController(meter_pin=meter_pin, key_pin=key_pin)
