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
                 pullback_pin: int = 12,
                 pwm_frequency: int = 1000,
                 initial_value: float = 0.0):
        """
        Инициализация контроллера мегомметра с двумя катушками.
        
        Args:
            meter_pin: GPIO пин для основной катушки (PWM)
            pullback_pin: GPIO пин для оттягивающей катушки (PWM)
            pwm_frequency: Частота PWM для плавного движения стрелки
            initial_value: Начальное значение PWM (0.0 = минимум, 1.0 = максимум)
        """
        self.meter_pin = meter_pin
        self.pullback_pin = pullback_pin
        self.pwm_frequency = pwm_frequency
        self.meter_device = None  # Основная катушка
        self.pullback_device = None  # Оттягивающая катушка
        self.is_initialized = False
        self.is_key_pressed = False
        
        # Параметры управления
        self.baseline_force = 0.25  # Сила оттягивающей катушки (еще увеличена)
        self.dot_amplitude = 0.4    # Амплитуда для точек
        self.dash_amplitude = 0.9   # Амплитуда для тире
        
        # Плавные переходы
        self.transition_running = False
        self.transition_thread = None
        self.current_value = 0.0
        
        print(f"Мегомметр: инициализация с основной катушкой GPIO {meter_pin} и оттягивающей GPIO {pullback_pin}")
    
    def initialize(self):
        """Инициализация PWM устройств."""
        try:
            from gpiozero import PWMOutputDevice
            
            # Инициализируем основную катушку
            self.meter_device = PWMOutputDevice(
                pin=self.meter_pin,
                frequency=self.pwm_frequency,
                initial_value=0.0
            )
            
            # Инициализируем оттягивающую катушку
            self.pullback_device = PWMOutputDevice(
                pin=self.pullback_pin,
                frequency=self.pwm_frequency,
                initial_value=0.0
            )
            
            print(f"Мегомметр: основная катушка инициализирована на GPIO {self.meter_pin}")
            print(f"Мегомметр: оттягивающая катушка инициализирована на GPIO {self.pullback_pin}")
            
            # Устанавливаем начальное состояние
            self._set_pullback_force()
            
            self.is_initialized = True
            return True
            
        except ImportError:
            print("gpiozero не найден, используем mock режим")
            return False
        except Exception as e:
            print(f"Ошибка инициализации мегомметра: {e}")
            return False
    
    def _set_pullback_force(self):
        """Установить силу оттягивающей катушки."""
        if self.pullback_device:
            self.pullback_device.value = self.baseline_force
            print(f"Мегомметр: оттягивающая катушка установлена на {self.baseline_force:.2f}")
    
    def _disable_pullback_force(self):
        """Отключить оттягивающую катушку."""
        if self.pullback_device:
            self.pullback_device.value = 0.0
            print("Мегомметр: оттягивающая катушка отключена")
    
    def _set_meter_value(self, value: float):
        """Установить значение на основной катушке."""
        if self.meter_device:
            self.meter_device.value = value
            self.current_value = value
            print(f"Мегомметр: основная катушка установлена на {value:.2f}")
    
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
        
        # Отключаем оттягивающую катушку при нажатии
        self._disable_pullback_force()
        
        # Небольшая задержка для исчезновения магнитного поля оттягивающей катушки
        time.sleep(0.05)
        
        # Устанавливаем начальное отклонение на основной катушке (амплитуда точки)
        initial_value = self.dot_amplitude
        self._set_meter_value(initial_value)
        print(f"Мегомметр: начальное отклонение установлено на {initial_value:.2f}")
    
    def key_released(self):
        """Обработчик отпускания телеграфного ключа - возврат к базовому подпору."""
        print("Мегомметр: ключ отпущен - возврат к базовому подпору")
        self.is_key_pressed = False
        # Принудительно останавливаем все переходы
        self.transition_running = False
        if self.transition_thread and self.transition_thread.is_alive():
            self.transition_thread.join(timeout=0.05)
        
        # Отключаем основную катушку
        self._set_meter_value(0.0)
        
        # Включаем оттягивающую катушку
        self._set_pullback_force()
        print(f"Мегомметр: оттягивающая катушка включена для возврата стрелки")
    
    def apply_dot(self):
        """Применить амплитуду точки (короткое отклонение)."""
        if not self.is_key_pressed:
            return
            
        # Убедимся, что оттягивающая катушка отключена
        self._disable_pullback_force()
        
        target_value = self.dot_amplitude
        print(f"Мегомметр: применяем точку - амплитуда {target_value:.2f}")
        self._smooth_transition_to(target_value, duration=0.15)  # Возвращено как было
    
    def apply_dash(self):
        """Применить амплитуду тире (сильное отклонение)."""
        if not self.is_key_pressed:
            return
            
        # Убедимся, что оттягивающая катушка отключена
        self._disable_pullback_force()
        
        target_value = self.dash_amplitude
        print(f"Мегомметр: применяем тире - амплитуда {target_value:.2f}")
        self._smooth_transition_to(target_value, duration=0.25)  # Возвращено как было
    
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
        
        # Отключаем основную катушку
        self._set_meter_value(0.0)
        
        # Включаем оттягивающую катушку
        self._set_pullback_force()
        print(f"Мегомметр: принудительно включена оттягивающая катушка для возврата стрелки")
    
    def cleanup(self):
        """Очистка ресурсов."""
        print("Мегомметр: начало очистки ресурсов")
        
        # Принудительно останавливаем все переходы
        self.transition_running = False
        if self.transition_thread and self.transition_thread.is_alive():
            self.transition_thread.join(timeout=0.5)
        
        # Отключаем обе катушки перед закрытием
        self._set_meter_value(0.0)
        if self.pullback_device:
            self.pullback_device.value = 0.0
            print("Мегомметр: оттягивающая катушка отключена")
        
        # Закрываем устройства
        if self.meter_device:
            self.meter_device.close()
            self.meter_device = None
        if self.pullback_device:
            self.pullback_device.close()
            self.pullback_device = None
            
        self.is_initialized = False
        print("Ресурсы мегомметра освобождены")


class MockMegohmmeterController(MegohmmeterController):
    """Mock контроллер для тестирования без Raspberry Pi."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("Используем mock контроллер мегомметра")
    
    def initialize(self) -> bool:
        """Mock инициализация всегда успешна."""
        print(f"Mock мегомметр инициализирован:")
        print(f"  Основная катушка: GPIO {self.meter_pin}")
        print(f"  Оттягивающая катушка: GPIO {self.pullback_pin}")
        self.is_initialized = True
        # Устанавливаем начальное состояние
        self._set_pullback_force()
        return True
    
    def _set_pullback_force(self):
        """Mock установка силы оттягивающей катушки."""
        print(f"Mock мегомметр: оттягивающая катушка установлена на {self.baseline_force:.2f}")
    
    def _disable_pullback_force(self):
        """Mock отключение оттягивающей катушки."""
        print("Mock мегомметр: оттягивающая катушка отключена")
    
    def _set_meter_value(self, value: float):
        """Mock установка значения на основной катушке."""
        self.current_value = value
        print(f"Mock мегомметр: основная катушка установлена на {value:.2f}")
    
    def key_pressed(self):
        """Обработчик нажатия на телеграфный ключ - начало отклонения."""
        print("Mock мегомметр: ключ нажат - начинаем отклонение")
        self.is_key_pressed = True
        # Принудительно останавливаем все переходы
        self.transition_running = False
        if self.transition_thread and self.transition_thread.is_alive():
            self.transition_thread.join(timeout=0.05)
        
        # Отключаем оттягивающую катушку при нажатии
        self._disable_pullback_force()
        
        # Устанавливаем начальное отклонение на основной катушке (амплитуда точки)
        initial_value = self.dot_amplitude
        self._set_meter_value(initial_value)
        print(f"Mock мегомметр: начальное отклонение установлено на {initial_value:.2f}")
    
    def key_released(self):
        """Обработчик отпускания телеграфного ключа - возврат к базовому подпору."""
        print("Mock мегомметр: ключ отпущен - возврат к базовому подпору")
        self.is_key_pressed = False
        # Принудительно останавливаем все переходы
        self.transition_running = False
        if self.transition_thread and self.transition_thread.is_alive():
            self.transition_thread.join(timeout=0.05)
        
        # Отключаем основную катушку
        self._set_meter_value(0.0)
        
        # Включаем оттягивающую катушку
        self._set_pullback_force()
        print(f"Mock мегомметр: оттягивающая катушка включена для возврата стрелки")
    
    def apply_dot(self):
        """Применить амплитуду точки (короткое отклонение)."""
        if not self.is_key_pressed:
            return
            
        target_value = self.dot_amplitude
        print(f"Mock мегомметр: применяем точку - амплитуда {target_value:.2f}")
        self.current_value = target_value
    
    def apply_dash(self):
        """Применить амплитуду тире (сильное отклонение)."""
        if not self.is_key_pressed:
            return
            
        target_value = self.dash_amplitude
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
        
        # Принудительно устанавливаем базовый подпор (минимальное отклонение)
        self.current_value = self.baseline_force
        print(f"Mock мегомметр: принудительно установлен базовый подпор {self.baseline_force:.2f} (минимальное отклонение)")
    
    def cleanup(self):
        """Mock очистка."""
        print("Mock ресурсы мегомметра освобождены")
        self.is_initialized = False
