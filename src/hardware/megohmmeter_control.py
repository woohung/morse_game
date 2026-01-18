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
        
        # Параметры "оттягивающей силы" и амплитуд
        self.baseline_force = 0.08  # Базовый подпор для возврата стрелки к нулю
        self.dot_amplitude = 0.4    # Амплитуда для точки (короткое отклонение)
        self.dash_amplitude = 0.9   # Амплитуда для тире (сильное отклонение)
        
        # Инициализация компонентов
        self.meter_device = None
        self.is_initialized = False
        
        # Поток для плавных переходов
        self.transition_thread = None
        self.transition_running = False
        self.target_value = initial_value
        
        # Состояние ключа для отслеживания
        self.is_key_pressed = False
        
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
            print(f"Мегомметр: значение установлено на {value:.2f}")
    
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
        """Обработчик нажатия на телеграфный ключ - начало отклонения."""
        print("Мегомметр: ключ нажат - начинаем отклонение")
        self.is_key_pressed = True
        # Принудительно останавливаем все переходы
        self.transition_running = False
        if self.transition_thread and self.transition_thread.is_alive():
            self.transition_thread.join(timeout=0.05)
        
        # Устанавливаем начальное отклонение (базовое + амплитуда точки)
        initial_value = self.baseline_force + self.dot_amplitude
        if self.meter_device:
            self.meter_device.value = initial_value
            self.current_value = initial_value
            print(f"Мегомметр: начальное отклонение установлено на {initial_value:.2f}")
    
    def key_released(self):
        """Обработчик отпускания телеграфного ключа - возврат к базовому подпору."""
        print("Мегомметр: ключ отпущен - возврат к базовому подпору")
        self.is_key_pressed = False
        # Принудительно останавливаем все переходы
        self.transition_running = False
        if self.transition_thread and self.transition_thread.is_alive():
            self.transition_thread.join(timeout=0.05)
        
        # Возвращаем к базовому подпору (оттягивающая сила)
        if self.meter_device:
            self.meter_device.value = self.baseline_force
            self.current_value = self.baseline_force
            print(f"Мегомметр: базовый подпор установлен на {self.baseline_force:.2f}")
    
    def apply_dot(self):
        """Применить амплитуду точки (короткое отклонение)."""
        if not self.is_key_pressed:
            return
            
        target_value = self.baseline_force + self.dot_amplitude
        print(f"Мегомметр: применяем точку - амплитуда {target_value:.2f}")
        self._smooth_transition_to(target_value, duration=0.15)
    
    def apply_dash(self):
        """Применить амплитуду тире (сильное отклонение)."""
        if not self.is_key_pressed:
            return
            
        target_value = self.baseline_force + self.dash_amplitude
        print(f"Мегомметр: применяем тире - амплитуда {target_value:.2f}")
        self._smooth_transition_to(target_value, duration=0.25)
    
    def _smooth_transition_to(self, target_value: float, duration: float):
        """Плавный переход к указанному значению за заданное время."""
        if self.transition_running:
            self.transition_running = False
            if self.transition_thread and self.transition_thread.is_alive():
                self.transition_thread.join(timeout=0.05)
        
        self.transition_running = True
        self.transition_thread = threading.Thread(
            target=self._transition_worker_to, 
            args=(target_value, duration),
            daemon=True
        )
        self.transition_thread.start()
    
    def _transition_worker_to(self, target_value: float, duration: float):
        """Рабочий поток для плавного перехода к целевому значению."""
        steps = int(duration * 50)  # 50 шагов в секунду
        if steps < 2:
            steps = 2
            
        step_delay = duration / steps
        start_value = self.current_value
        value_diff = target_value - start_value
        
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
    
    def force_reset(self):
        """Принудительно сбросить стрелку к базовому подпору."""
        print("Мегомметр: принудительный сброс стрелки к базовому подпору")
        self.is_key_pressed = False
        # Останавливаем все переходы
        self.transition_running = False
        if self.transition_thread and self.transition_thread.is_alive():
            self.transition_thread.join(timeout=0.05)
        
        # Принудительно устанавливаем базовый подпор
        if self.meter_device:
            self.meter_device.value = self.baseline_force
            self.current_value = self.baseline_force
            print(f"Мегомметр: принудительно установлен базовый подпор {self.baseline_force:.2f}")
    
    def cleanup(self):
        """Очистка ресурсов."""
        print("Мегомметр: начало очистки ресурсов")
        
        # Принудительно останавливаем все переходы
        self.transition_running = False
        if self.transition_thread and self.transition_thread.is_alive():
            self.transition_thread.join(timeout=0.5)
        
        # Гарантированно устанавливаем базовый подпор перед закрытием
        if self.meter_device:
            self.meter_device.value = self.baseline_force
            self.current_value = self.baseline_force
            print(f"Мегомметр: базовый подпор установлен перед закрытием {self.baseline_force:.2f}")
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
        print(f"Mock мегомметр: значение установлено на {value:.2f}")
    
    def key_pressed(self):
        """Обработчик нажатия на телеграфный ключ - начало отклонения."""
        print("Mock мегомметр: ключ нажат - начинаем отклонение")
        self.is_key_pressed = True
        # Принудительно останавливаем все переходы
        self.transition_running = False
        if self.transition_thread and self.transition_thread.is_alive():
            self.transition_thread.join(timeout=0.05)
        
        # Устанавливаем начальное отклонение (базовое + амплитуда точки)
        initial_value = self.baseline_force + self.dot_amplitude
        self.current_value = initial_value
        print(f"Mock мегомметр: начальное отклонение установлено на {initial_value:.2f}")
    
    def key_released(self):
        """Обработчик отпускания телеграфного ключа - возврат к базовому подпору."""
        print("Mock мегомметр: ключ отпущен - возврат к базовому подпору")
        self.is_key_pressed = False
        # Принудительно останавливаем все переходы
        self.transition_running = False
        if self.transition_thread and self.transition_thread.is_alive():
            self.transition_thread.join(timeout=0.05)
        
        # Возвращаем к базовому подпору (оттягивающая сила)
        self.current_value = self.baseline_force
        print(f"Mock мегомметр: базовый подпор установлен на {self.baseline_force:.2f}")
    
    def apply_dot(self):
        """Применить амплитуду точки (короткое отклонение)."""
        if not self.is_key_pressed:
            return
            
        target_value = self.baseline_force + self.dot_amplitude
        print(f"Mock мегомметр: применяем точку - амплитуда {target_value:.2f}")
        self.current_value = target_value
    
    def apply_dash(self):
        """Применить амплитуду тире (сильное отклонение)."""
        if not self.is_key_pressed:
            return
            
        target_value = self.baseline_force + self.dash_amplitude
        print(f"Mock мегомметр: применяем тире - амплитуда {target_value:.2f}")
        self.current_value = target_value
    
    def force_reset(self):
        """Принудительно сбросить стрелку к базовому подпору."""
        print("Mock мегомметр: принудительный сброс стрелки к базовому подпору")
        self.is_key_pressed = False
        # Останавливаем все переходы
        self.transition_running = False
        if self.transition_thread and self.transition_thread.is_alive():
            self.transition_thread.join(timeout=0.05)
        
        # Принудительно устанавливаем базовый подпор
        self.current_value = self.baseline_force
        print(f"Mock мегомметр: принудительно установлен базовый подпор {self.baseline_force:.2f}")
    
    def cleanup(self):
        """Mock очистка."""
        print("Mock ресурсы мегомметра освобождены")
        self.is_initialized = False
