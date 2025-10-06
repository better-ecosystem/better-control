"""
Adding new languages for better user preferences

To add a new language, create a new class that inherits from the Translation base class
and update the get_translations function to include the new language.
The class should contain all the translations for the new language.

Usage in tab files:
    from utils.translations import Translation

    class SomeTab(Gtk.Box):
        def __init__(self, logging: Logger, txt: Translation):
            # Use txt for translations
"""

import os
from logging import Logger
from typing import Protocol, Optional

from utils.logger import LogLevel


class Translation(Protocol):
    """Base protocol for all translations in the application.

    This provides type hints without needing to import all language classes.
    All language classes should implement these properties and methods.
    """
    # Common properties that all translations must have
    msg_desc: str
    msg_app_url: str
    msg_usage: str

    # Tab names
    msg_tab_volume: str
    msg_tab_wifi: str
    msg_tab_bluetooth: str
    msg_tab_battery: str
    msg_tab_display: str
    msg_tab_power: str
    msg_tab_autostart: str
    msg_tab_usbguard: str

    # Common UI elements
    loading: str
    loading_tabs: str
    close: str
    enable: str
    disable: str


class English:
    """English language translation for the application"""

    def __init__(self):
        # app description
        self.msg_desc = "A sleek GTK-themed control panel for Linux."

        # USB notifications
        self.usb_connected = "{device} connected."
        self.usb_disconnected = "{device} disconnected."
        self.permission_allowed = "USB permission granted"
        self.permission_blocked = "USB permission blocked"
        self.msg_app_url = "https://github.com/quantumvoid0/better-control"
        self.msg_usage = "Usage"

        # for args
        self.msg_args_help = "Prints this message"
        self.msg_args_autostart = "Starts with the autostart tab open"
        self.msg_args_battery = "Starts with the battery tab open"
        self.msg_args_bluetooth = "Starts with the bluetooth tab open"
        self.msg_args_display = "Starts with the display tab open"
        self.msg_args_force = "Makes the app force to have all dependencies installed"
        self.msg_args_power = "Starts with the power tab open"
        self.msg_args_volume = "Starts with the volume tab open"
        self.msg_args_volume_v = "Also starts with the volume tab open"
        self.msg_args_wifi = "Starts with the wifi tab open"

        self.msg_args_log = "The program will either log to a file if given a file path,\n or output to stdout based on the log level if given a value between 0, and 3."
        self.msg_args_redact = "Redact sensitive information from logs (network names, device IDs, etc.)"
        self.msg_args_size = "Sets a custom window size"

        # commonly used
        self.connect = "Connect"
        self.connected = "Connected"
        self.connecting = "Connecting..."
        self.disconnect = "Disconnect"
        self.disconnected = "Disconnected"
        self.disconnecting = "Disconnecting..."
        self.enable = "Enable"
        self.disable = "Disable"
        self.close = "Close"
        self.show = "Show"
        self.loading = "Loading..."
        self.loading_tabs = "Loading tabs..."

        # for tabs
        self.msg_tab_autostart = "Autostart"
        self.msg_tab_usbguard = "USBGuard"
        self.usbguard_title = "USB Device Control"
        self.refresh = "Refresh"
        self.allow = "Allow"
        self.block = "Block"
        self.allowed = "Allowed"
        self.blocked = "Blocked"
        self.rejected = "Rejected"
        self.policy = "View Policy"
        self.usbguard_error = "Error accessing USBGuard"
        self.usbguard_not_installed = "USBGuard not installed"
        self.usbguard_not_running = "USBGuard service not running"
        self.no_devices = "No USB devices connected"
        self.operation_failed = "Operation failed"
        self.policy_error = "Failed to load policy"
        self.permanent_allow = "Permanently Allow"
        self.permanent_allow_tooltip = "Permanently allow this device (adds to policy)"
        self.msg_tab_battery = "Battery"
        self.msg_tab_bluetooth = "Bluetooth"
        self.msg_tab_display = "Display"
        self.msg_tab_power = "Power"
        self.msg_tab_volume = "Volume"
        self.msg_tab_wifi = "Wi-Fi"

        # Autostart tab translations
        self.autostart_title = "Autostart Applications"
        self.autostart_session = "Session"
        self.autostart_show_system_apps = "Show system autostart applications"
        self.autostart_configured_applications = "Configured Applications"
        self.autostart_tooltip_rescan = "Rescan autostart apps"

        # Battery tab translations
        self.battery_title = "Battery Dashboard"
        self.battery_power_saving = "Power Saving"
        self.battery_balanced = "Balanced"
        self.battery_performance = "Performance"
        self.battery_batteries = "Batteries"
        self.battery_overview = "Overview"
        self.battery_details = "Details"
        self.battery_tooltip_refresh = "Refresh Battery Information"
        self.battery_no_batteries = "No battery detected"

        # Bluetooth tab translations
        self.bluetooth_title = "Bluetooth Devices"
        self.bluetooth_scan_devices = "Scan for Devices"
        self.bluetooth_scanning = "Scanning..."
        self.bluetooth_power = "Bluetooth"
        self.bluetooth_available_devices = "Available Devices"
        self.bluetooth_tooltip_refresh = "Scan for Devices"
        self.bluetooth_connect_failed = "Failed to connect to device"
        self.bluetooth_disconnect_failed = "Failed to disconnect from device"
        self.bluetooth_try_again = "Please try again later."

        # Bluetooth forget button translations
        self.bluetooth_forget_failed = "Failed to forget device"
        self.forget = "Forget"
        self.forget_in_progress = "Forgetting..."

        # Display tab translations
        self.display_title = "Display Settings"
        self.display_brightness = "Screen Brightness"
        self.display_blue_light = "Blue Light"
        self.display_orientation = "Orientation"
        self.display_default = "Default"
        self.display_left = "Left"
        self.display_right = "Right"
        self.display_inverted = "Inverted"

        self.display_rotation = "Rotation Options"
        self.display_simple_rotation = "Quick Rotation"
        self.display_specific_orientation = "Specific Orientation"
        self.display_flip_controls = "Display Flipping"
        self.display_rotate_cw = "Rotate Clockwise"
        self.display_rotate_ccw = "Rotate Counter-clockwise"
        self.display_rotation_help = "Rotation applies right away. It’ll reset if you don’t confirm in 10 seconds."

        # Power tab translations
        self.power_title = "Power Management"
        self.power_tooltip_menu = "Configure Power Menu"
        self.power_menu_buttons = "Buttons"
        self.power_menu_commands = "Commands"
        self.power_menu_colors = "Colors"
        self.power_menu_show_hide_buttons = "Show/Hide Buttons"
        self.power_menu_shortcuts_tab_label = "Shortcuts"
        self.power_menu_visibility = "Buttons"
        self.power_menu_keyboard_shortcut = "Keyboard Shortcuts"
        self.power_menu_show_keyboard_shortcut = "Show Keyboard Shortcuts"
        self.power_menu_lock = "Lock"
        self.power_menu_logout = "Logout"
        self.power_menu_suspend = "Suspend"
        self.power_menu_hibernate = "Hibernate"
        self.power_menu_reboot = "Reboot"
        self.power_menu_shutdown = "Shutdown"
        self.power_menu_apply = "Apply"
        self.power_menu_tooltip_lock = "Lock the screen"
        self.power_menu_tooltip_logout = "Log out of the current session"
        self.power_menu_tooltip_suspend = "Suspend the system (sleep)"
        self.power_menu_tooltip_hibernate = "Hibernate the system"
        self.power_menu_tooltip_reboot = "Restart the screen"
        self.power_menu_tooltip_shutdown = "Power off the screen"

        # Volume tab translations
        self.volume_title = "Volume Settings"
        self.volume_speakers = "Speakers"
        self.volume_tab_tooltip = "Speakers Settings"
        self.volume_output_device = "Output Device"
        self.volume_device = "Device"
        self.volume_output = "Output"
        self.volume_speaker_volume = "Speaker Volume"
        self.volume_mute_speaker = "Mute Speakers"
        self.volume_unmute_speaker = "Unmute Speakers"
        self.volume_quick_presets = "Quick Presets"
        self.volume_output_combo_tooltip = "Select output device for this application"

        # Volume tab microphone translations
        self.microphone_tab_microphone = "Microphone"
        self.microphone_tab_input_device = "Input Device"
        self.microphone_tab_volume = "Microphone Volume"
        self.microphone_tab_mute_microphone = "Mute Microphone"
        self.microphone_tab_unmute_microphone = "Unmute Microphone"
        self.microphone_tab_tooltip = "Microphone Settings"

        # Volume tab App output translations
        self.app_output_title = "App Output"
        self.app_output_volume = "Application Output Volume"
        self.app_output_mute = "Mute"
        self.app_output_unmute = "Unmute"
        self.app_output_tab_tooltip = "Application Output Settings"
        self.app_output_no_apps = "No applications playing audio"
        self.app_output_dropdown_tooltip = "Select output device for this application"

        # Volume tab App input translations
        self.app_input_title = "App Input"
        self.app_input_volume = "Application Input Volume"
        self.app_input_mute = "Mute Microphone for this application"
        self.app_input_unmute = "Unmute Microphone for this application"
        self.app_input_tab_tooltip = "Application Microphone Settings"
        self.app_input_no_apps = "No applications using microphone"

        # WiFi tab translations
        self.wifi_title = "Wi-Fi Networks"
        self.wifi_refresh_tooltip = "Refresh Networks"
        self.wifi_power = "Wi-Fi"
        self.wifi_speed = "Connection Speed"
        self.wifi_download = "Download"
        self.wifi_upload = "Upload"
        self.wifi_available = "Available Networks"
        self.wifi_forget = "Forget"
        self.wifi_share_title = "Share Network"
        self.wifi_share_scan = "Scan to connect"
        self.wifi_network_name = "Network Name"
        self.wifi_password = "Password"
        self.wifi_loading_networks = "Loading Networks..."

        # Settings tab translations
        self.settings_title = "Settings"
        self.settings_tab_settings = "Tab Settings"
        self.settings_language = "Language"
        self.settings_language_changed_restart = "Please restart the application for the language change to take effect."
        self.settings_language_changed = "Language changed"


class Russian:
    """Русский перевод утилиты"""

    def __init__(self):
        # app description
        self.msg_desc = "Красивая панель управления для Linux на тулките GTK"

        # USB notifications
        self.usb_connected = "{device} подключено."
        self.usb_disconnected = "{device} отключено."
        self.permission_allowed = "Доступ к USB разрешён"
        self.permission_blocked = "Доступ к USB запрещён"
        self.msg_app_url = "https://github.com/quantumvoid0/better-control"
        self.msg_usage = "Инструкция"

        # for args
        self.msg_args_help = "Выводит это сообщение"
        self.msg_args_autostart = "При запуске, открывает вкладку автозапуска"
        self.msg_args_battery = "При запуске, открывает вкладку управления батареей"
        self.msg_args_bluetooth = "При запуске, открывает вкладку управления Bluetooth"
        self.msg_args_display = "При запуске, открывает вкладку настройки экранов"
        self.msg_args_force = "Принуждает приложение запускаться только в случае, если установлены все зависимости"
        self.msg_args_power = "При запуске, открывает вкладку управления питанием"
        self.msg_args_volume = "При запуске, открывает вкладку управления громкостью"
        self.msg_args_volume_v = "Также, при запуске, открывает вкладку управления громкостью"
        self.msg_args_wifi = "При запуске, открывает вкладку управления сетями Wi-Fi"

        self.msg_args_log = "Программа либо выведет логи в файл, если таков указан,\n либо в stdout на основе уровня логов от 0 до 3"
        self.msg_args_redact = "Меняет важную информацию об оборудовании (имена сетей, идентификаторы устройств, т.д.)"
        self.msg_args_size = "Устанавливает указанный пользователем размер окна"

        # commonly used
        self.connect = "Подключить"
        self.connected = "Подключено"
        self.connecting = "Подключение..."
        self.disconnect = "Отключить"
        self.disconnected = "Не подключено"
        self.disconnecting = "Отключение..."
        self.enable = "Включить"
        self.disable = "Выключить"
        self.close = "Закрыть"
        self.show = "Показать"
        self.loading = "Загрузка..."
        self.loading_tabs = "Загрузка вкладок..."

        # for tabs
        self.msg_tab_autostart = "Автозапуск"
        self.msg_tab_usbguard = "USBGuard"
        self.usbguard_title = "Управление устройствами USB"
        self.refresh = "Обновить"
        self.allow = "Разрешить"
        self.block = "Запретить"
        self.allowed = "Разрешено"
        self.blocked = "Запрещено"
        self.rejected = "Отклонено"
        self.policy = "Просмотреть политику"
        self.usbguard_error = "Ошибка доступа к USBGuard"
        self.usbguard_not_installed = "USBGuard не установлен"
        self.usbguard_not_running = "Служба USBGuard не запущена"
        self.no_devices = "Ни одно USB-устройство не подключено"
        self.operation_failed = "Операция провалена"
        self.policy_error = "Не удалось загрузить политику"
        self.permanent_allow = "Разрешить временно"
        self.permanent_allow_tooltip = "Разрешить навсегда (добавить в политику)"
        self.msg_tab_battery = "Батарея"
        self.msg_tab_bluetooth = "Bluetooth"
        self.msg_tab_display = "Экран"
        self.msg_tab_power = "Питание"
        self.msg_tab_volume = "Громкость"
        self.msg_tab_wifi = "Wi-Fi"

        # Autostart tab translations
        self.autostart_title = "Приложения в автозапуске"
        self.autostart_session = "Сессия"
        self.autostart_show_system_apps = "Показать системные приложения в автозапуске"
        self.autostart_configured_applications = "Настроенные приложения"
        self.autostart_tooltip_rescan = "Пересканировать приложения в автозапуске"

        # Battery tab translations
        self.battery_title = "Дэшборд батареи"
        self.battery_power_saving = "Энергосбережение"
        self.battery_balanced = "Сбалансированный"
        self.battery_performance = "Макс. производительность"
        self.battery_batteries = "Батареи"
        self.battery_overview = "Просмотр"
        self.battery_details = "Подробности"
        self.battery_tooltip_refresh = "Обновить информацию о батареях"
        self.battery_no_batteries = "Батареи отсутствуют"

        # Bluetooth tab translations
        self.bluetooth_title = "Устройства Bluetooth"
        self.bluetooth_scan_devices = "Поиск устройств"
        self.bluetooth_scanning = "Поиск..."
        self.bluetooth_power = "Bluetooth"
        self.bluetooth_available_devices = "Доступные устройства"
        self.bluetooth_tooltip_refresh = "Поиск устройств"
        self.bluetooth_connect_failed = "Не удалось подключиться к устройству"
        self.bluetooth_disconnect_failed = "Не удалось отключиться от устройсва"
        self.bluetooth_try_again = "Попробуйте позже"

        # Bluetooth forget button translations
        self.bluetooth_forget_failed = "Не удалось разорвать сопряжение"
        self.forget = "Разовать сопряжение"
        self.forget_in_progress = "Идёт разрыв сопряжения..."

        # Display tab translations
        self.display_title = "Параметры экрана"
        self.display_brightness = "Яркость экрана"
        self.display_blue_light = "Синий цвет"
        self.display_orientation = "Угол поворота"
        self.display_default = "Стандарт"
        self.display_left = "Влево"
        self.display_right = "Вправо"
        self.display_inverted = "Снизу вверх"

        self.display_rotation = "Параметры поворота"
        self.display_simple_rotation = "Быстрый поворот"
        self.display_specific_orientation = "Точный поворот"
        self.display_flip_controls = "Поворот экрана"
        self.display_rotate_cw = "Повернутьпо часовой"
        self.display_rotate_ccw = "Повернуть против часовой"
        self.display_rotation_help = "Поворот применится немедленно. Через 10 секунд без подтверждения произойдёт сброс."

        # Power tab translations
        self.power_title = "Управление питанием"
        self.power_tooltip_menu = "Настройка меню питания"
        self.power_menu_buttons = "Кнопки"
        self.power_menu_commands = "Комманды"
        self.power_menu_colors = "Цвета"
        self.power_menu_show_hide_buttons = "Показать/Спрятать кнопки"
        self.power_menu_shortcuts_tab_label = "Ссылки"
        self.power_menu_visibility = "Кнопки"
        self.power_menu_keyboard_shortcut = "Комбинации клавиш"
        self.power_menu_show_keyboard_shortcut = "Показать комбинации клавиш"
        self.power_menu_lock = "Запереть"
        self.power_menu_logout = "Завершить сеанс"
        self.power_menu_suspend = "Спящий режим"
        self.power_menu_hibernate = "Гибернация"
        self.power_menu_reboot = "Перезагрузка"
        self.power_menu_shutdown = "Выключение"
        self.power_menu_apply = "Применить"
        self.power_menu_tooltip_lock = "Запереть экран"
        self.power_menu_tooltip_logout = "Завершить текуший сеанс"
        self.power_menu_tooltip_suspend = "Перевести устройство в спящий режим"
        self.power_menu_tooltip_hibernate = "Гибернировать устройство"
        self.power_menu_tooltip_reboot = "Перезагрузить устройство"
        self.power_menu_tooltip_shutdown = "Выключить устройство"

        # Volume tab translations
        self.volume_title = "Параметры громкости"
        self.volume_speakers = "Динамики"
        self.volume_tab_tooltip = "Параметры динамиков"
        self.volume_output_device = "Устройство вывода"
        self.volume_device = "Устройство"
        self.volume_output = "Вывод"
        self.volume_speaker_volume = "Громкость динамика"
        self.volume_mute_speaker = "Заглушить динамики"
        self.volume_unmute_speaker = "Отключить глушение динамиков"
        self.volume_quick_presets = "Быстрые преднастройки"
        self.volume_output_combo_tooltip = "Выберите устройство вывода для этого приложения"

        # Volume tab microphone translations
        self.microphone_tab_microphone = "Микрофон"
        self.microphone_tab_input_device = "Устройство ввода"
        self.microphone_tab_volume = "Громкость микрофона"
        self.microphone_tab_mute_microphone = "Заглушить микрофон"
        self.microphone_tab_unmute_microphone = "Отключить глушение микрофона"
        self.microphone_tab_tooltip = "Параметры микрофона"

        # Volume tab App output translations
        self.app_output_title = "Вывод приложения"
        self.app_output_volume = "Громкость вывода приложения"
        self.app_output_mute = "Заглушить"
        self.app_output_unmute = "Отключить глушение"
        self.app_output_tab_tooltip = "Параметры вывода приложения"
        self.app_output_no_apps = "Ни в одном приложении не проигрывается аудио"
        self.app_output_dropdown_tooltip = "Выберите устройство выбора для этого приложения"

        # Volume tab App input translations
        self.app_input_title = "Ввод приложения"
        self.app_input_volume = "Громкость ввода приложения"
        self.app_input_mute = "Заглушить микрофон этому приложению"
        self.app_input_unmute = "Отключить глушение микрофона этому приложению"
        self.app_input_tab_tooltip = "Параметры микрофона приложения"
        self.app_input_no_apps = "Ни одно приложение не использует микрофон"

        # WiFi tab translations
        self.wifi_title = "Сети Wi-Fi"
        self.wifi_refresh_tooltip = "Поиск сетей"
        self.wifi_power = "Wi-Fi"
        self.wifi_speed = "Скорость подключения"
        self.wifi_download = "Скачивание"
        self.wifi_upload = "Загрузка"
        self.wifi_available = "Доступные сети"
        self.wifi_forget = "Забыть"
        self.wifi_share_title = "Поделиться сетью"
        self.wifi_share_scan = "Сканируйте, чтобы поделиться"
        self.wifi_network_name = "Имя сети"
        self.wifi_password = "Пароль"
        self.wifi_loading_networks = "Загрузка сетей..."

        # Settings tab translations
        self.settings_title = "Параметры"
        self.settings_tab_settings = "Параметры вкладок"
        self.settings_language = "Язык"
        self.settings_language_changed_restart = "Перезапустите приложение для смены языка."
        self.settings_language_changed = "Язык изменён"


class German:
    """German language translation for the application"""

    def __init__(self):
        # app description
        self.msg_desc = "Ein elegantes Bedienfeld für Linux mit GTK-Theming."

        # USB notifications
        self.usb_connected = "{device} verbunden."
        self.usb_disconnected = "{device} getrennt."
        self.permission_allowed = "USB Zugriff gewährt"
        self.permission_blocked = "USB Zugriff verweigert"
        self.msg_app_url = "https://github.com/quantumvoid0/better-control"
        self.msg_usage = "Nutzung"

        # for args
        self.msg_args_help = "Zeigt diese Meldung an"
        self.msg_args_autostart = "Startet die Anwendung mit dem Autorstart-Tab"
        self.msg_args_battery = "Startet die Anwendung mit dem Batterie-Tab"
        self.msg_args_bluetooth = "Startet die Anwendung mit dem Bluetooth-Tab"
        self.msg_args_display = "Startet die Anwendung mit dem Display-Tab"
        self.msg_args_force = "Zwingt die Anwendung dazu alle Abhängigkeiten installiert zu haben"
        self.msg_args_power = "Startet die Anwendung mit dem Power-Tab"
        self.msg_args_volume = "Startet die Anwendung mit dem Lautstärke-Tab"
        self.msg_args_volume_v = "Startet die Anwendung ebenfalls mit dem Bluetooth-Tab"
        self.msg_args_wifi = "Startet die Anwendung mit dem WLAN-Tab"

        self.msg_args_log = "Das Programm schreibt das Log an den angegeben Pfad,\n oder an stdout basierend auf dem Log-Level, wenn ein Wert zwischen 0 und 3 angegeben wird."
        self.msg_args_redact = "Entfernt sesible Daten aus dem Log (Netzwerknamen, Geräte IDs, usw.)"
        self.msg_args_size = "Legt eine benutzerdefinierte Fenstergröße fest"

        # commonly used
        self.connect = "Verbinden"
        self.connected = "Verbunden"
        self.connecting = "Verbinde..."
        self.disconnect = "Verbindung trennen"
        self.disconnected = "Verbindung getrennt"
        self.disconnecting = "Trenne Verbindung..."
        self.enable = "Einschalten"
        self.disable = "Ausschalten"
        self.close = "Schließen"
        self.show = "Einblenden"
        self.loading = "Laden..."
        self.loading_tabs = "Lade Tabs..."

        # for tabs
        self.msg_tab_autostart = "Autostart"
        self.msg_tab_usbguard = "USBGuard"
        self.usbguard_title = "USB-Geräte Einstellungen"
        self.refresh = "Aktualisieren"
        self.allow = "Erlauben"
        self.block = "Blockieren"
        self.allowed = "Erlaubt"
        self.blocked = "Blockiert"
        self.rejected = "Verweigert"
        self.policy = "Richtlienen Ansehen"
        self.usbguard_error = "Fehler beim zugreifen auf USBGuard"
        self.usbguard_not_installed = "USBGuard nicht installiert"
        self.usbguard_not_running = "USBGuard Dienst läuft nicht"
        self.no_devices = "keine USB-Geräte verbunden"
        self.operation_failed = "Operation fehlgeschlagen"
        self.policy_error = "Laden der Richtliene fehlgeschlagen"
        self.permanent_allow = "Dauerhaft erlauben"
        self.permanent_allow_tooltip = "Gerät dauerhaft erlauben (Hinzufügen zur Richtliene)"
        self.msg_tab_battery = "Akku"
        self.msg_tab_bluetooth = "Bluetooth"
        self.msg_tab_display = "Bildschirm"
        self.msg_tab_power = "Energieoptionen"
        self.msg_tab_volume = "Lautstärke"
        self.msg_tab_wifi = "WLAN"

        # Autostart tab translations
        self.autostart_title = "Autostart Anwendungen"
        self.autostart_session = "Sitzung"
        self.autostart_show_system_apps = "Zeige System Anwendungen an"
        self.autostart_configured_applications = "Konfigurierte Anwendungen"
        self.autostart_tooltip_rescan = "Autostart Anwendungen aktualisieren"

        # Battery tab translations
        self.battery_title = "Akku Dashboard"
        self.battery_power_saving = "Energiesparen"
        self.battery_balanced = "Ausbalanciert"
        self.battery_performance = "Höchstleistung"
        self.battery_batteries = "Akkus"
        self.battery_overview = "Übersicht"
        self.battery_details = "Details"
        self.battery_tooltip_refresh = "Akkuinformationen Aktualisieren"
        self.battery_no_batteries = "Keine Akkus gefunden"

        # Bluetooth tab translations
        self.bluetooth_title = "Bluetooth Geräte"
        self.bluetooth_scan_devices = "Nach Geräten suchen"
        self.bluetooth_scanning = "Suche..."
        self.bluetooth_power = "Bluetooth"
        self.bluetooth_available_devices = "Verfügbare Geräet"
        self.bluetooth_tooltip_refresh = "Nach Geräten suchen"
        self.bluetooth_connect_failed = "Gerät konnte nicht verbunden werden"
        self.bluetooth_disconnect_failed = "Gerät konnte nicht getrennt werden"
        self.bluetooth_try_again = "Bitte versuche es später erneut"

        # Display tab translations
        self.display_title = "Bildschirm Einstellungen"
        self.display_brightness = "Bildschirmhelligkeit"
        self.display_blue_light = "Blaulichtfilter"
        self.display_orientation = "Ausrichtung"
        self.display_default = "Standard"
        self.display_left = "Links"
        self.display_right = "Rechts"
        self.display_inverted = "Invertiert"

        self.display_rotation = "Rotationseinstellungen"
        self.display_simple_rotation = "Schnellrotation"
        self.display_specific_orientation = "Spezifische Orientierung"
        self.display_flip_controls = "Display drehung"
        self.display_rotate_cw = "Im Uhrzeigersinn drehen"
        self.display_rotate_ccw = "Gegen den Uhrzeigersinn drehen"
        self.display_rotation_help = "Die Einstellungen werden automatisch übernommen und nach 10 Sekunden zurückgesetzt sollten sie nicht bestätigt werden."

        # Power tab translations
        self.power_title = "Energieoptionen"
        self.power_tooltip_menu = "Energieoptionen Anpassen"
        self.power_menu_buttons = "Knöpfe"
        self.power_menu_commands = "Befehle"
        self.power_menu_colors = "Farben"
        self.power_menu_show_hide_buttons = "Knöpfe Einblenden / Ausblenden"
        self.power_menu_shortcuts_tab_label = "Tastenkombinationen"
        self.power_menu_visibility = "Knöpfe"
        self.power_menu_keyboard_shortcut = "Tastenkombinationen"
        self.power_menu_show_keyboard_shortcut = "Tastenkombinationen anzeigen"
        self.power_menu_lock = "Sperern"
        self.power_menu_logout = "Abmelden"
        self.power_menu_suspend = "Bereitschaft"
        self.power_menu_hibernate = "Ruhezustand"
        self.power_menu_reboot = "Neustarten"
        self.power_menu_shutdown = "Herunterfahren"
        self.power_menu_apply = "Anwenden"
        self.power_menu_tooltip_lock = "Bildschirm sperren"
        self.power_menu_tooltip_logout = "Sitzung Abmelden"
        self.power_menu_tooltip_suspend = "Das Gerät in den Bereitschaftsmodus setzen"
        self.power_menu_tooltip_hibernate = "Das Gerät in den Ruhezustand versetzen"
        self.power_menu_tooltip_reboot = "Das Gerät neustarten"
        self.power_menu_tooltip_shutdown = "Das Gerät Herunterfahren"

        # Volume tab translations
        self.volume_title = "Lautstärke Einstellungen"
        self.volume_speakers = "Ausgabegeräte"
        self.volume_tab_tooltip = "Geräte"
        self.volume_output_device = "Ausgabegeräte"
        self.volume_device = "Gerät"
        self.volume_output = "Ausgabe"
        self.volume_speaker_volume = "Ausgabelautstärke"
        self.volume_mute_speaker = "Lautsprecher Stummschalten"
        self.volume_unmute_speaker = "Stummschaltung aufheben"
        self.volume_quick_presets = "Schnelleinstellungen"
        self.volume_output_combo_tooltip = "Ausgabegerät für die Anwendung auswählen"

        # Volume tab microphone translations
        self.microphone_tab_microphone = "Eingabegeräte"
        self.microphone_tab_input_device = "Eingabegerät"
        self.microphone_tab_volume = "Aufnahmelautstärke"
        self.microphone_tab_mute_microphone = "Mikrofon Stummschalten"
        self.microphone_tab_unmute_microphone = "Stummschaltung aufheben"
        self.microphone_tab_tooltip = "Geräte"

        # Volume tab App output translations
        self.app_output_title = "App Ausgabe"
        self.app_output_volume = "Anwendungs Lautstärke"
        self.app_output_mute = "Stummschalten"
        self.app_output_unmute = "Stummschaltung aufheben"
        self.app_output_tab_tooltip = "Anwendungs Lautstärke Einstellungen"
        self.app_output_no_apps = "Keine Anwendungen die Ton wiedergeben"
        self.app_output_dropdown_tooltip = "Ausgabegerät für die Anwenung auswählen"

        # Volume tab App input translations
        self.app_input_title = "App Aufnahme"
        self.app_input_volume = "Anwendungs Aufnahmelautstärke"
        self.app_input_mute = "Mikrofon für diese Anwenung Stummschalten"
        self.app_input_unmute = "Stummschaltung des Mikrofons für diese Anwendung aufheben"
        self.app_input_tab_tooltip = "Anwenungsaufnahme Einstellungen"
        self.app_input_no_apps = "Keine Anwenungen die Ton aufzeichenen"

        # WiFi tab translations
        self.wifi_title = "WLAN Netzwerke"
        self.wifi_refresh_tooltip = "Nach neuen Netzwerken suchen"
        self.wifi_power = "WLAN"
        self.wifi_speed = "Verbindungsgeschwindigkeit"
        self.wifi_download = "Downloaden"
        self.wifi_upload = "Hochladen"
        self.wifi_available = "Verfügbare Netzwerke"
        self.wifi_forget = "Vergessen"
        self.wifi_share_title = "Netzwerk teilen"
        self.wifi_share_scan = "Scan to connect"
        self.wifi_network_name = "Netzwerkname"
        self.wifi_password = "Passwort"
        self.wifi_loading_networks = "Lade Netzwerke..."

        # Settings tab translations
        self.settings_title = "Einstellungen"
        self.settings_tab_settings = "Tab Einstellungen"
        self.settings_language = "Sprache"
        self.settings_language_changed_restart = "Bitte starte die Anwenung neu damit die Spracheinstellungen übernommen werden"
        self.settings_language_changed = "Sprache geändert"


class Italian:
    """Italian language translation for the application"""

    def __init__(self):
        # app description
        self.msg_desc = "Un pannello di controllo elegante e basato su GTK per Linux."

        # USB notifications
        self.usb_connected = "{device} connesso."
        self.usb_disconnected = "{device} disconnesso."
        self.permission_allowed = "Permessi USB concessi"
        self.permission_blocked = "Permessi USB bloccati"
        self.msg_app_url = "https://github.com/quantumvoid0/better-control"
        self.msg_usage = "Utilizzo"

        # for args
        self.msg_args_help = "Mostra questo messaggio"
        self.msg_args_autostart = "Avvia con la scheda dell'avvio automatico aperta"
        self.msg_args_battery = "Avvia con la scheda della batteria aperta"
        self.msg_args_bluetooth = "Avvia con la scheda del bluetooth aperta"
        self.msg_args_display = "Avvia con la scheda dello schermo aperta"
        self.msg_args_force = "Fà si che l'applicazione richieda forzatamente tutte le dipendenze installate"
        self.msg_args_power = "Avvia con la scheda dell'alimentazione aperta"
        self.msg_args_volume = "Avvia con la scheda del volume aperta"
        self.msg_args_volume_v = "Avvia con anche la scheda del volume aperta"
        self.msg_args_wifi = "Avvia con la scheda del wifi aperta"

        self.msg_args_log = "Il programma creerà un log se gli viene fornito un percorso,\n altrimenti invierà l'output su stdout in base al livello di log, con un valore compreso tra 0 e 3."
        self.msg_args_redact = "Elimina le informazioni sensibili dai registri (reti, ID dei device, etc.)"
        self.msg_args_size = "Imposta una dimensione personalizzata della finestra"

        # commonly used
        self.connect = "Connetti"
        self.connected = "Connesso"
        self.connecting = "Connessione..."
        self.disconnect = "Disconnetti"
        self.disconnected = "Disconnesso"
        self.disconnecting = "Disconnessione..."
        self.enable = "Attiva"
        self.disable = "Disattiva"
        self.close = "Chiudi"
        self.show = "Mostra"
        self.loading = "Caricamento..."
        self.loading_tabs = "Caricamento schede..."

        # for tabs
        self.msg_tab_autostart = "Avvio automatico"
        self.msg_tab_usbguard = "USBGuard"
        self.usbguard_title = "Controllo dei dispositivi USB"
        self.refresh = "Ricarica"
        self.allow = "Permetti"
        self.block = "Blocca"
        self.allowed = "Permesso"
        self.blocked = "Bloccato"
        self.rejected = "Respinto"
        self.policy = "Vedi la Policy"
        self.usbguard_error = "Errore durante l'accesso a USBGuard"
        self.usbguard_not_installed = "USBGuard non installato"
        self.usbguard_not_running = "Il servizio di USBGuard non è in esecuzione"
        self.no_devices = "Nessun dispositivo USB collegato"
        self.operation_failed = "Operazione fallita"
        self.policy_error = "Errore nel caricamento della policy"
        self.permanent_allow = "Permesso permanentemente"
        self.permanent_allow_tooltip = "Consenti permanentemente questo dispositivo (lo aggiunge alla policy)"
        self.msg_tab_battery = "Batteria"
        self.msg_tab_bluetooth = "Bluetooth"
        self.msg_tab_display = "Schermo"
        self.msg_tab_power = "Alimentazione"
        self.msg_tab_volume = "Volume"
        self.msg_tab_wifi = "Wi-Fi"

        # Autostart tab translations
        self.autostart_title = "Applicazioni lanciate all'avvio"
        self.autostart_session = "Sessione"
        self.autostart_show_system_apps = "Mostra le applicazioni di sistema lanciate all'avvio"
        self.autostart_configured_applications = "Applicazioni configurate"
        self.autostart_tooltip_rescan = "Scansiona nuovamente le applicazioni lanciate all'avvio"

        # Battery tab translations
        self.battery_title = "Pannello di controllo della batteria"
        self.battery_power_saving = "Risparmio energetico"
        self.battery_balanced = "Bilanciato"
        self.battery_performance = "Massime prestazioni"
        self.battery_batteries = "Batterie"
        self.battery_overview = "Panoramica"
        self.battery_details = "Dettagli"
        self.battery_tooltip_refresh = "Ricarica le informazioni della batteria"
        self.battery_no_batteries = "Nessuna batteria rilevata"

        # Bluetooth tab translations
        self.bluetooth_title = "Dispositivi bluetooth"
        self.bluetooth_scan_devices = "Scansiona per trovare dispositivi"
        self.bluetooth_scanning = "Scansiono..."
        self.bluetooth_power = "Bluetooth"
        self.bluetooth_available_devices = "Dispositivi disponibili"
        self.bluetooth_tooltip_refresh = "Scansiona per trovare dispositivi"
        self.bluetooth_connect_failed = "Errore durante la connessione al dispositivo"
        self.bluetooth_disconnect_failed = "Errore durante la disconnessione dal dispositivo"
        self.bluetooth_try_again = "Perfavore riprova."

        # Display tab translations
        self.display_title = "Impostazioni schermo"
        self.display_brightness = "Luminosità"
        self.display_blue_light = "Luce blu"
        self.display_orientation = "Orientamento"
        self.display_default = "Predefinito"
        self.display_left = "Sinistra"
        self.display_right = "Destra"
        self.display_inverted = "Invertito"

        self.display_rotation = "Opzioni della rotazione"
        self.display_simple_rotation = "Rotazione veloce"
        self.display_specific_orientation = "Orientamento spefico"
        self.display_flip_controls = "Capovolgimento dello schermo"
        self.display_rotate_cw = "Ruota in senso orario"
        self.display_rotate_ccw = "Ruota in senso antiorario"
        self.display_rotation_help = "La rotazione verrà applicata subito. In caso di mancata conferma entro 10 secondi verrà ripristinata."

        # Power tab translations
        self.power_title = "Gestione dell'alimentazione"
        self.power_tooltip_menu = "Configura il menu di alimentazione"
        self.power_menu_buttons = "Pulsanti"
        self.power_menu_commands = "Comandi"
        self.power_menu_colors = "Colori"
        self.power_menu_show_hide_buttons = "Mostra/nascondi pulsanti"
        self.power_menu_shortcuts_tab_label = "Scorciatoie"
        self.power_menu_visibility = "Pulsanti"
        self.power_menu_keyboard_shortcut = "Scorciatoie da tastiera"
        self.power_menu_show_keyboard_shortcut = "Mostra le scorciatoie da tastiera"
        self.power_menu_lock = "Blocca"
        self.power_menu_logout = "Disconnetti"
        self.power_menu_suspend = "Sospendi"
        self.power_menu_hibernate = "Iberna"
        self.power_menu_reboot = "Riavvia"
        self.power_menu_shutdown = "Spegni"
        self.power_menu_apply = "Applica"
        self.power_menu_tooltip_lock = "Blocca lo schermo"
        self.power_menu_tooltip_logout = "Chiudi la sessione corrente"
        self.power_menu_tooltip_suspend = "Sospendi il sistema"
        self.power_menu_tooltip_hibernate = "Iberna il sistema"
        self.power_menu_tooltip_reboot = "Riavvia lo schermo"
        self.power_menu_tooltip_shutdown = "Spegni lo schermo"

        # Volume tab translations
        self.volume_title = "Impostazione volume"
        self.volume_speakers = "Altoparlanti"
        self.volume_tab_tooltip = "Impostazioni altoparlanti"
        self.volume_output_device = "Dispostivo d'uscita"
        self.volume_device = "Dispositivo"
        self.volume_output = "Uscita"
        self.volume_speaker_volume = "Volume altoparlanti"
        self.volume_mute_speaker = "Muta altoparlanti"
        self.volume_unmute_speaker = "Smuta altoparlanti"
        self.volume_quick_presets = "Impostazioni rapide"
        self.volume_output_combo_tooltip = "Seleziona il dispositivo d'uscita per questa applicazione"

        # Volume tab microphone translations
        self.microphone_tab_microphone = "Microfono"
        self.microphone_tab_input_device = "Dispositivo di input"
        self.microphone_tab_volume = "Volume del microfono"
        self.microphone_tab_mute_microphone = "Muta microfono"
        self.microphone_tab_unmute_microphone = "Smuta microfono"
        self.microphone_tab_tooltip = "Impostazioni microfono"

        # Volume tab App output translations
        self.app_output_title = "Output dell'app"
        self.app_output_volume = "Volume output dell'app"
        self.app_output_mute = "Muta"
        self.app_output_unmute = "Smuta"
        self.app_output_tab_tooltip = "Impostazioni dell'output dell'app"
        self.app_output_no_apps = "Nessuna applicazione sta riproducendo audio"
        self.app_output_dropdown_tooltip = "Seleziona il dispositivo d'uscita di questa applicazione"

        # Volume tab App input translations
        self.app_input_title = "Ingresso app"
        self.app_input_volume = "Volume d'ingresso dell'app"
        self.app_input_mute = "Muta il microfono per questa applicazione"
        self.app_input_unmute = "Smuta il microfono per questa applicazione"
        self.app_input_tab_tooltip = "Impostazioni del microfono dell'app"
        self.app_input_no_apps = "Nessun applicazione sta usando il microfono"

        # WiFi tab translations
        self.wifi_title = "Reti Wi-Fi"
        self.wifi_refresh_tooltip = "Ricarica reti"
        self.wifi_power = "Wi-Fi"
        self.wifi_speed = "Velocità di connessione"
        self.wifi_download = "Download"
        self.wifi_upload = "Upload"
        self.wifi_available = "Reti disponibili"
        self.wifi_forget = "Dimentica"
        self.wifi_share_title = "Condividi rete"
        self.wifi_share_scan = "Scansiona per connetterti"
        self.wifi_network_name = "Nome della rete"
        self.wifi_password = "Password"
        self.wifi_loading_networks = "Carico le reti..."

        # Settings tab translations
        self.settings_title = "Impostazioni"
        self.settings_tab_settings = "Impostazioni delle schede"
        self.settings_language = "Lingua"
        self.settings_language_changed_restart = "Perfavore riavvia l'applicazione affinchè venga ricaricata la lingua."
        self.settings_language_changed = "Lingua cambiata"


class Spanish:
    """Spanish language translation for the application"""

    def __init__(self):
        # app description
        self.msg_desc = "Un elegante panel de control con tema GTK para Linux."
        self.msg_app_url = "https://github.com/quantumvoid0/better-control"
        self.msg_usage = "Uso"

        # for args
        self.msg_args_help = "Muestra este mensaje"
        self.msg_args_autostart = "Inicia con la pestaña de inicio automático abierta"
        self.msg_args_battery = "Inicia con la pestaña de batería abierta"
        self.msg_args_bluetooth = "Inicia con la pestaña de bluetooth abierta"
        self.msg_args_display = "Inicia con la pestaña de pantalla abierta"
        self.msg_args_force = "Fuerza la aplicación a iniciar sin todas las dependencias"
        self.msg_args_power = "Inicia con la pestaña de energía abierta"
        self.msg_args_volume = "Inicia con la pestaña de volumen abierta"
        self.msg_args_volume_v = "También inicia con la pestaña de volumen abierta"
        self.msg_args_wifi = "Inicia con la pestaña de wifi abierta"

        self.msg_args_log = "El programa registrará en un archivo si se proporciona una ruta,\n o mostrará en stdout según el nivel de registro si se da un valor entre 0 y 3."
        self.msg_args_redact = "Oculta información sensible de los registros (nombres de red, IDs de dispositivos, etc.)"
        self.msg_args_size = "Establece un tamaño de ventana personalizado"

        # commonly used
        self.connect = "Conectar"
        self.connected = "Conectado"
        self.connecting = "Conectando..."
        self.disconnect = "Desconectar"
        self.disconnected = "Desconectado"
        self.disconnecting = "Desconectando..."
        self.disable = "Deshabilitar"
        self.enable = "Habilitar"
        self.close = "Cerrar"
        self.show = "Mostrar"
        self.loading = "Cargando..."
        self.loading_tabs = "Cargando pestañas..."

        # for tabs
        self.msg_tab_autostart = "Inicio Automático"
        self.msg_tab_usbguard = "USBGuard"
        self.usbguard_title = "Control de Dispositivos USB"
        self.refresh = "Actualizar"
        self.allow = "Permitir"
        self.block = "Bloquear"
        self.policy = "Ver Política"
        self.usbguard_error = "Error al acceder a USBGuard"
        self.usbguard_not_installed = "USBGuard no está instalado"
        self.usbguard_not_running = "Servicio USBGuard no está en ejecución"
        self.no_devices = "No hay dispositivos USB conectados"
        self.operation_failed = "Operación fallida"
        self.policy_error = "Error al cargar la política"
        self.msg_tab_battery = "Batería"
        self.msg_tab_bluetooth = "Bluetooth"
        self.msg_tab_display = "Pantalla"
        self.msg_tab_power = "Energía"
        self.msg_tab_volume = "Volumen"
        self.msg_tab_wifi = "Wi-Fi"

        # Autostart tab translations
        self.autostart_title = "Aplicaciones de Inicio Automático"
        self.autostart_session = "Sesión"
        self.autostart_show_system_apps = "Mostrar aplicaciones del sistema"
        self.autostart_configured_applications = "Aplicaciones Configuradas"
        self.autostart_tooltip_rescan = "Volver a buscar aplicaciones"

        # Battery tab translations
        self.battery_title = "Panel de Batería"
        self.battery_power_saving = "Ahorro de Energía"
        self.battery_balanced = "Equilibrado"
        self.battery_performance = "Rendimiento"
        self.battery_batteries = "Baterías"
        self.battery_overview = "Resumen"
        self.battery_details = "Detalles"
        self.battery_tooltip_refresh = "Actualizar Información de Batería"
        self.battery_no_batteries = "No se detectó ninguna batería"

        # Bluetooth tab translations
        self.bluetooth_title = "Dispositivos Bluetooth"
        self.bluetooth_scan_devices = "Buscar dispositivos"
        self.bluetooth_scanning = "Buscando..."
        self.bluetooth_power = "Bluetooth"
        self.bluetooth_available_devices = "Dispositivos Disponibles"
        self.bluetooth_tooltip_refresh = "Buscar Dispositivos"
        self.bluetooth_connect_failed = "Error al conectar el dispositivo"
        self.bluetooth_disconnect_failed = "Error al desconectar el dispositivo"
        self.bluetooth_try_again = "Por favor, inténtelo de nuevo más tarde."

        # Display tab translations
        self.display_title = "Configuración de Pantalla"
        self.display_brightness = "Brillo de Pantalla"
        self.display_blue_light = "Luz Azul"
        self.display_orientation = "Orientación"
        self.display_default = "Predeterminado"
        self.display_left = "Izquierda"
        self.display_right = "Derecha"
        self.display_inverted = "Invertido"

        # Power tab translations
        self.power_title = "Gestión de Energía"
        self.power_tooltip_menu = "Configurar Menú de Energía"
        self.power_menu_buttons = "Botones"
        self.power_menu_commands = "Comandos"
        self.power_menu_colors = "Colores"
        self.power_menu_show_hide_buttons = "Mostrar/Ocultar Botones"
        self.power_menu_shortcuts_tab_label = "Atajos"
        self.power_menu_visibility = "Botones"
        self.power_menu_keyboard_shortcut = "Atajos de Teclado"
        self.power_menu_show_keyboard_shortcut = "Mostrar Atajos de Teclado"
        self.power_menu_lock = "Bloquear"
        self.power_menu_logout = "Cerrar Sesión"
        self.power_menu_suspend = "Suspender"
        self.power_menu_hibernate = "Hibernar"
        self.power_menu_reboot = "Reiniciar"
        self.power_menu_shutdown = "Apagar"
        self.power_menu_apply = "Aplicar"
        self.power_menu_tooltip_lock = "Bloquear la pantalla"
        self.power_menu_tooltip_logout = "Cerrar sesión de la sesión actual"
        self.power_menu_tooltip_suspend = "Suspender el sistema (sueño)"
        self.power_menu_tooltip_hibernate = "Hibernar el sistema"
        self.power_menu_tooltip_reboot = "Reiniciar la pantalla"
        self.power_menu_tooltip_shutdown = "Apagar la pantalla"

        # Volume tab translations
        self.volume_title = "Configuración de Volumen"
        self.volume_speakers = "Altavoces"
        self.volume_tab_tooltip = "Configuración de Altavoces"
        self.volume_output_device = "Dispositivo de Salida"
        self.volume_device = "Dispositivo"
        self.volume_output = "Salida"
        self.volume_speaker_volume = "Volumen de Altavoces"
        self.volume_mute_speaker = "Silenciar Altavoces"
        self.volume_unmute_speaker = "Activar Altavoces"
        self.volume_output_combo_tooltip = "Seleccionar dispositivo de salida para esta aplicación"
        self.volume_quick_presets = "Preajustes Rápidos"

        # Volume tab microphone translations
        self.microphone_tab_microphone = "Micrófono"
        self.microphone_tab_input_device = "Dispositivo de Entrada"
        self.microphone_tab_volume = "Volumen de Micrófono"
        self.microphone_tab_mute_microphone = "Silenciar Micrófono"
        self.microphone_tab_unmute_microphone = "Activar Micrófono"
        self.microphone_tab_tooltip = "Configuración de Micrófono"

        # Volume tab App output translations
        self.app_output_title = "Salida de Aplicaciones"
        self.app_output_volume = "Volumen de Salida de Aplicaciones"
        self.app_output_mute = "Silenciar"
        self.app_output_unmute = "Activar"
        self.app_output_tab_tooltip = "Configuración de Salida de Aplicaciones"
        self.app_output_no_apps = "No hay aplicaciones reproduciendo audio"
        self.app_output_dropdown_tooltip = "Seleccionar dispositivo de salida para esta aplicación"

        # Volume tab App input translations
        self.app_input_title = "Entrada de Aplicaciones"
        self.app_input_volume = "Volumen de Entrada de Aplicaciones"
        self.app_input_mute = "Silenciar Micrófono para esta aplicación"
        self.app_input_unmute = "Activar Micrófono para esta aplicación"
        self.app_input_tab_tooltip = "Configuración del Micrófono de Aplicaciones"
        self.app_input_no_apps = "No hay aplicaciones usando el micrófono"

        # WiFi tab translations
        self.wifi_title = "Redes Wi-Fi"
        self.wifi_refresh_tooltip = "Actualizar Redes"
        self.wifi_power = "Wi-Fi"
        self.wifi_speed = "Velocidad de Conexión"
        self.wifi_download = "Descarga"
        self.wifi_upload = "Subida"
        self.wifi_available = "Redes Disponibles"
        self.wifi_forget = "Olvidar"
        self.wifi_share_title = "Compartir Red"
        self.wifi_share_scan = "Escanear para conectar"
        self.wifi_network_name = "Nombre de Red"
        self.wifi_password = "Contraseña"
        self.wifi_loading_networks = "Cargando Redes..."

        # Settings tab translations
        self.settings_title = "Configuraciones"
        self.settings_tab_settings = "Configuraciones de Pestaña"
        self.settings_language = "Idioma"
        self.settings_language_changed_restart = "Por favor reinicie la aplicación para que el cambio de idioma tenga efecto."
        self.settings_language_changed = "Idioma cambiado"


class Portuguese:
    """Portuguese language translation for the application"""

    def __init__(self):
        # app description
        self.msg_desc = "Um elegante painel de controle com tema GTK para Linux."
        self.msg_app_url = "https://github.com/quantumvoid0/better-control"
        self.msg_usage = "Uso"

        # for args
        self.msg_args_help = "Mostra esta mensagem"
        self.msg_args_autostart = "Inicia com a aba de inicialização automática aberta"
        self.msg_args_battery = "Inicia com a aba de bateria aberta"
        self.msg_args_bluetooth = "Inicia com a aba de bluetooth aberta"
        self.msg_args_display = "Inicia com a aba de tela aberta"
        self.msg_args_force = "Força o aplicativo a iniciar sem todas as dependências"
        self.msg_args_power = "Inicia com a aba de energia aberta"
        self.msg_args_volume = "Inicia com a aba de volume aberta"
        self.msg_args_volume_v = "Também inicia com a aba de volume aberta"
        self.msg_args_wifi = "Inicia com a aba de wifi aberta"

        self.msg_args_log = "O programa registrará em um arquivo se fornecido um caminho,\n ou mostrará no stdout com base no nível de registro se fornecido um valor entre 0 e 3."
        self.msg_args_redact = "Oculta informações sensíveis dos registros (nomes de rede, IDs de dispositivos, etc.)"
        self.msg_args_size = "Define um tamanho de janela personalizado"

        # commonly used
        self.connect = "Conectar"
        self.connected = "Conectado"
        self.connecting = "Conectando..."
        self.disconnect = "Desconectar"
        self.disconnected = "Desconectado"
        self.disconnecting = "Desconectando..."
        self.enable = "Ativar"
        self.disable = "Desativar"
        self.close = "Fechar"
        self.show = "Mostrar"
        self.loading = "Carregando..."
        self.loading_tabs = "Carregando abas..."

        # for tabs
        self.msg_tab_autostart = "Inicialização"
        self.msg_tab_usbguard = "USBGuard"
        self.usbguard_title = "Controle de Dispositivos USB"
        self.refresh = "Atualizar"
        self.allow = "Permitir"
        self.block = "Bloquear"
        self.policy = "Ver Política"
        self.usbguard_error = "Erro ao acessar USBGuard"
        self.usbguard_not_installed = "USBGuard não instalado"
        self.usbguard_not_running = "Serviço USBGuard não está em execução"
        self.no_devices = "Nenhum dispositivo USB conectado"
        self.operation_failed = "Operação falhou"
        self.policy_error = "Falha ao carregar política"
        self.msg_tab_battery = "Bateria"
        self.msg_tab_bluetooth = "Bluetooth"
        self.msg_tab_display = "Tela"
        self.msg_tab_power = "Energia"
        self.msg_tab_volume = "Volume"
        self.msg_tab_wifi = "Wi-Fi"

        # Autostart tab translations
        self.autostart_title = "Aplicativos de Inicialização Automática"
        self.autostart_session = "Sessão"
        self.autostart_show_system_apps = "Mostrar aplicativos do sistema"
        self.autostart_configured_applications = "Aplicativos Configurados"
        self.autostart_tooltip_rescan = "Verificar aplicativos novamente"

        # Battery tab translations
        self.battery_title = "Painel da Bateria"
        self.battery_power_saving = "Economia de Energia"
        self.battery_balanced = "Equilibrado"
        self.battery_performance = "Desempenho"
        self.battery_batteries = "Baterias"
        self.battery_overview = "Visão Geral"
        self.battery_details = "Detalhes"
        self.battery_tooltip_refresh = "Atualizar Informações da Bateria"
        self.battery_no_batteries = "Nenhuma bateria detectada"

        # Bluetooth tab translations
        self.bluetooth_title = "Dispositivos Bluetooth"
        self.bluetooth_scan_devices = "Buscar Dispositivos"
        self.bluetooth_scanning = "Buscando..."
        self.bluetooth_power = "Bluetooth"
        self.bluetooth_available_devices = "Dispositivos Disponíveis"
        self.bluetooth_tooltip_refresh = "Buscar Dispositivos"
        self.bluetooth_connect_failed = "Falha ao conectar ao dispositivo"
        self.bluetooth_disconnect_failed = "Falha ao desconectar do dispositivo"
        self.bluetooth_try_again = "Por favor, tente novamente mais tarde."

        # Display tab translations
        self.display_title = "Configurações de Tela"
        self.display_brightness = "Brilho da Tela"
        self.display_blue_light = "Luz Azul"
        self.display_orientation = "Orientação"
        self.display_default = "Padrão"
        self.display_left = "Esquerda"
        self.display_right = "Direita"
        self.display_inverted = "Invertido"

        # Power tab translations
        self.power_title = "Gerenciamento de Energia"
        self.power_tooltip_menu = "Configurar Menu de Energia"
        self.power_menu_buttons = "Botões"
        self.power_menu_commands = "Comandos"
        self.power_menu_colors = "Cores"
        self.power_menu_show_hide_buttons = "Mostrar/Ocultar Botões"
        self.power_menu_shortcuts_tab_label = "Atalhos"
        self.power_menu_visibility = "Botões"
        self.power_menu_keyboard_shortcut = "Atalhos de Teclado"
        self.power_menu_show_keyboard_shortcut = "Mostrar Atalhos de Teclado"
        self.power_menu_lock = "Bloquear"
        self.power_menu_logout = "Sair"
        self.power_menu_suspend = "Suspender"
        self.power_menu_hibernate = "Hibernar"
        self.power_menu_reboot = "Reiniciar"
        self.power_menu_shutdown = "Desligar"
        self.power_menu_apply = "Aplicar"
        self.power_menu_tooltip_lock = "Bloquear a tela"
        self.power_menu_tooltip_logout = "Sair da sessão atual"
        self.power_menu_tooltip_suspend = "Suspender o sistema (dormir)"
        self.power_menu_tooltip_hibernate = "Hibernar o sistema"
        self.power_menu_tooltip_reboot = "Reiniciar a tela"
        self.power_menu_tooltip_shutdown = "Desligar a tela"

        # Volume tab translations
        self.volume_title = "Configurações de Volume"
        self.volume_speakers = "Alto-falantes"
        self.volume_tab_tooltip = "Configurações de Alto-falantes"
        self.volume_output_device = "Dispositivo de Saída"
        self.volume_device = "Dispositivo"
        self.volume_output = "Saída"
        self.volume_speaker_volume = "Volume dos Alto-falantes"
        self.volume_mute_speaker = "Silenciar Alto-falantes"
        self.volume_unmute_speaker = "Ativar Alto-falantes"
        self.volume_quick_presets = "Predefinições Rápidas"
        self.volume_output_combo_tooltip = "Selecionar dispositivo de saída para este aplicativo"

        # Volume tab microphone translations
        self.microphone_tab_microphone = "Microfone"
        self.microphone_tab_input_device = "Dispositivo de Entrada"
        self.microphone_tab_volume = "Volume do Microfone"
        self.microphone_tab_mute_microphone = "Silenciar Microfone"
        self.microphone_tab_unmute_microphone = "Ativar Microfone"
        self.microphone_tab_tooltip = "Configurações do Microfone"

        # Volume tab App output translations
        self.app_output_title = "Saída de Aplicativos"
        self.app_output_volume = "Volume de Saída de Aplicativos"
        self.app_output_mute = "Silenciar"
        self.app_output_unmute = "Ativar"
        self.app_output_tab_tooltip = "Configurações de Saída de Aplicativos"
        self.app_output_no_apps = "Nenhum aplicativo reproduzindo áudio"
        self.app_output_dropdown_tooltip = "Selecionar dispositivo de saída para este aplicativo"

        # Volume tab App input translations
        self.app_input_title = "Entrada de Aplicativos"
        self.app_input_volume = "Volume de Entrada de Aplicativos"
        self.app_input_mute = "Silenciar Microfone para este aplicativo"
        self.app_input_unmute = "Ativar Microfone para este aplicativo"
        self.app_input_tab_tooltip = "Configurações do Microfone de Aplicativos"
        self.app_input_no_apps = "Nenhum aplicativo usando o microfone"

        # WiFi tab translations
        self.wifi_title = "Redes Wi-Fi"
        self.wifi_refresh_tooltip = "Atualizar Redes"
        self.wifi_power = "Wi-Fi"
        self.wifi_speed = "Velocidade de Conexão"
        self.wifi_download = "Download"
        self.wifi_upload = "Upload"
        self.wifi_available = "Redes Disponíveis"
        self.wifi_forget = "Esquecer"
        self.wifi_share_title = "Compartilhar Rede"
        self.wifi_share_scan = "Escanear para conectar"
        self.wifi_network_name = "Nome da Rede"
        self.wifi_password = "Senha"
        self.wifi_loading_networks = "Carregando Redes..."

        # Settings tab translations
        self.settings_title = "Configurações"
        self.settings_tab_settings = "Configurações de Abas"
        self.settings_language = "Idioma"
        self.settings_language_changed_restart = "Por favor reinicie o aplicativo para que a mudança de idioma tenha efeito."
        self.settings_language_changed = "Idioma alterado"


class French:
    """French language translation for the application"""

    def __init__(self):
        # app description
        self.msg_desc = "Un panneau de contrôle élégant avec thème GTK pour Linux."
        self.msg_app_url = "https://github.com/quantumvoid0/better-control"
        self.msg_usage = "Utilisation"

        # for args
        self.msg_args_help = "Affiche ce message"
        self.msg_args_autostart = "Démarre avec l'onglet de démarrage automatique ouvert"
        self.msg_args_battery = "Démarre avec l'onglet de batterie ouvert"
        self.msg_args_bluetooth = "Démarre avec l'onglet bluetooth ouvert"
        self.msg_args_display = "Démarre avec l'onglet d'affichage ouvert"
        self.msg_args_force = "Force l'application à démarrer sans toutes les dépendances"
        self.msg_args_power = "Démarre avec l'onglet d'alimentation ouvert"
        self.msg_args_volume = "Démarre avec l'onglet de volume ouvert"
        self.msg_args_volume_v = "Démarre également avec l'onglet de volume ouvert"
        self.msg_args_wifi = "Démarre avec l'onglet Wi-Fi ouvert"

        self.msg_args_log = "Le programme enregistrera dans un fichier si un chemin est fourni,\n ou affichera sur stdout selon le niveau de journalisation si une valeur entre 0 et 3 est donnée."
        self.msg_args_redact = "Masque les informations sensibles des journaux (noms de réseau, identifiants d'appareils, etc.)"
        self.msg_args_size = "Définit une taille de fenêtre personnalisée"

        # commonly used
        self.connect = "Connecter"
        self.connected = "Connecté"
        self.connecting = "Connexion..."
        self.disconnect = "Déconnecter"
        self.disconnected = "Déconnecté"
        self.disconnecting = "Déconnexion..."
        self.enable = "Activer"
        self.disable = "Désactiver"
        self.close = "Fermer"
        self.show = "Afficher"
        self.loading = "Chargement..."
        self.loading_tabs = "Chargement des onglets..."

        # for tabs
        self.msg_tab_autostart = "Démarrage Auto"
        self.msg_tab_usbguard = "USBGuard"
        self.usbguard_title = "Contrôle des Périphériques USB"
        self.refresh = "Actualiser"
        self.allow = "Autoriser"
        self.block = "Bloquer"
        self.policy = "Voir la Politique"
        self.usbguard_error = "Erreur d'accès à USBGuard"
        self.usbguard_not_installed = "USBGuard non installé"
        self.usbguard_not_running = "Service USBGuard non démarré"
        self.no_devices = "Aucun périphérique USB connecté"
        self.operation_failed = "Échec de l'opération"
        self.policy_error = "Échec du chargement de la politique"
        self.msg_tab_battery = "Batterie"
        self.msg_tab_bluetooth = "Bluetooth"
        self.msg_tab_display = "Affichage"
        self.msg_tab_power = "Alimentation"
        self.msg_tab_volume = "Volume"
        self.msg_tab_wifi = "Wi-Fi"

        # Autostart tab translations
        self.autostart_title = "Applications au Démarrage"
        self.autostart_session = "Session"
        self.autostart_show_system_apps = "Afficher les applications système"
        self.autostart_configured_applications = "Applications Configurées"
        self.autostart_tooltip_rescan = "Rescanner les applications"

        # Battery tab translations
        self.battery_title = "Tableau de Bord de la Batterie"
        self.battery_power_saving = "Économie d'Énergie"
        self.battery_balanced = "Équilibré"
        self.battery_performance = "Performance"
        self.battery_batteries = "Batteries"
        self.battery_overview = "Aperçu"
        self.battery_details = "Détails"
        self.battery_tooltip_refresh = "Actualiser les Informations de la Batterie"
        self.battery_no_batteries = "Aucune batterie détectée"

        # Bluetooth tab translations
        self.bluetooth_title = "Appareils Bluetooth"
        self.bluetooth_scan_devices = "Rechercher des Appareils"
        self.bluetooth_scanning = "Recherche..."
        self.bluetooth_power = "Bluetooth"
        self.bluetooth_available_devices = "Appareils Disponibles"
        self.bluetooth_tooltip_refresh = "Rechercher des Appareils"
        self.bluetooth_connect_failed = "Échec de la connexion à l'appareil"
        self.bluetooth_disconnect_failed = "Échec de la déconnexion de l'appareil"
        self.bluetooth_try_again = "Veuillez réessayer plus tard."

        # Display tab translations
        self.display_title = "Paramètres d'Affichage"
        self.display_brightness = "Luminosité de l'Écran"
        self.display_blue_light = "Lumière Bleue"
        self.display_orientation = "Orientation"
        self.display_default = "Par défaut"
        self.display_left = "Gauche"
        self.display_right = "Droite"
        self.display_inverted = "Inversé"

        # Power tab translations
        self.power_title = "Gestion de l'Alimentation"
        self.power_tooltip_menu = "Configurer le Menu d'Alimentation"
        self.power_menu_buttons = "Boutons"
        self.power_menu_commands = "Commandes"
        self.power_menu_colors = "Couleurs"
        self.power_menu_show_hide_buttons = "Afficher/Masquer les Boutons"
        self.power_menu_shortcuts_tab_label = "Raccourcis"
        self.power_menu_visibility = "Boutons"
        self.power_menu_keyboard_shortcut = "Raccourcis Clavier"
        self.power_menu_show_keyboard_shortcut = "Afficher les Raccourcis Clavier"
        self.power_menu_lock = "Verrouiller"
        self.power_menu_logout = "Déconnexion"
        self.power_menu_suspend = "Mettre en Veille"
        self.power_menu_hibernate = "Hiberner"
        self.power_menu_reboot = "Redémarrer"
        self.power_menu_shutdown = "Éteindre"
        self.power_menu_apply = "Appliquer"
        self.power_menu_tooltip_lock = "Verrouiller l'écran"
        self.power_menu_tooltip_logout = "Se déconnecter de la session actuelle"
        self.power_menu_tooltip_suspend = "Mettre le système en veille"
        self.power_menu_tooltip_hibernate = "Hiberner le système"
        self.power_menu_tooltip_reboot = "Redémarrer l'écran"
        self.power_menu_tooltip_shutdown = "Éteindre l'écran"

        # Volume tab translations
        self.volume_title = "Paramètres de Volume"
        self.volume_speakers = "Haut-parleurs"
        self.volume_tab_tooltip = "Paramètres des Haut-parleurs"
        self.volume_output_device = "Périphérique de Sortie"
        self.volume_device = "Périphérique"
        self.volume_output = "Sortie"
        self.volume_speaker_volume = "Volume des Haut-parleurs"
        self.volume_mute_speaker = "Couper les Haut-parleurs"
        self.volume_unmute_speaker = "Activer les Haut-parleurs"
        self.volume_quick_presets = "Préréglages Rapides"
        self.volume_output_combo_tooltip = "Sélectionner le périphérique de sortie pour cette application"

        # Volume tab microphone translations
        self.microphone_tab_microphone = "Microphone"
        self.microphone_tab_input_device = "Périphérique d'Entrée"
        self.microphone_tab_volume = "Volume du Microphone"
        self.microphone_tab_mute_microphone = "Couper le Microphone"
        self.microphone_tab_unmute_microphone = "Activer le Microphone"
        self.microphone_tab_tooltip = "Paramètres du Microphone"

        # Volume tab App output translations
        self.app_output_title = "Sortie d'Applications"
        self.app_output_volume = "Volume de Sortie d'Applications"
        self.app_output_mute = "Couper"
        self.app_output_unmute = "Activer"
        self.app_output_tab_tooltip = "Paramètres de Sortie d'Applications"
        self.app_output_no_apps = "Aucune application ne joue de l'audio"
        self.app_output_dropdown_tooltip = "Sélectionner le périphérique de sortie pour cette application"

        # Volume tab App input translations
        self.app_input_title = "Entrée d'Applications"
        self.app_input_volume = "Volume d'Entrée d'Applications"
        self.app_input_mute = "Couper le Microphone pour cette application"
        self.app_input_unmute = "Activer le Microphone pour cette application"
        self.app_input_tab_tooltip = "Paramètres du Microphone d'Applications"
        self.app_input_no_apps = "Aucune application n'utilise le microphone"

        # WiFi tab translations
        self.wifi_title = "Réseaux Wi-Fi"
        self.wifi_refresh_tooltip = "Actualiser les Réseaux"
        self.wifi_power = "Wi-Fi"
        self.wifi_speed = "Vitesse de Connexion"
        self.wifi_download = "Téléchargement"
        self.wifi_upload = "Envoi"
        self.wifi_available = "Réseaux Disponibles"
        self.wifi_forget = "Oublier"
        self.wifi_share_title = "Partager le Réseau"
        self.wifi_share_scan = "Scanner pour se connecter"
        self.wifi_network_name = "Nom du Réseau"
        self.wifi_password = "Mot de passe"
        self.wifi_loading_networks = "Chargement des Réseaux..."

        # Settings tab translations
        self.settings_title = "Paramètres"
        self.settings_tab_settings = "Paramètres des Onglets"
        self.settings_language = "Langue"
        self.settings_language_changed_restart = "Veuillez redémarrer l'application pour que le changement de langue prenne effet."
        self.settings_language_changed = "Langue modifiée"


class Indonesian:
    """Indonesian language translation for the application"""

    def __init__(self):
        # app description
        self.msg_desc = "Panel kontrol GTK yang unik untuk Linux"
        self.msg_app_url = "https://github.com/quantumvoid0/better-control"
        self.msg_usage = "Penggunaan"

        # for args
        self.msg_args_help = "Mencetak pesan ini"
        self.msg_args_autostart = "Memulai aplikasi dengan tab Autostart terbuka"
        self.msg_args_battery = "Memulai aplikasi dengan tab Baterai terbuka"
        self.msg_args_bluetooth = "Memulai aplikasi dengan tab Blueetooth terbuka"
        self.msg_args_display = "Memulai aplikasi the tab Tampilan terbuka"
        self.msg_args_force = "Memaksa aplikasi untuk mengecek semua ketergantungan"
        self.msg_args_power = "Memulai aplikasi dengan tab Power terbuka"
        self.msg_args_volume = "Memulai aplikasi dengan tab Volume terbuka"
        self.msg_args_volume_v = "Juga memulai aplikasit dengan tab Volume terbuka"
        self.msg_args_wifi = "Memulai aplikasi dengan tab WiFI terbuka"

        self.msg_args_log = "Aplikasi akan mengeluarkan log ke sebuah file jika diberi sebuah file path,\n atau mengeluarkan output ke stdout jika diberikan nilai antara 0, dan 3."
        self.msg_args_redact = "Menyunting informasi sensitif dari log. (nama jaringan, ID perankat, dst.)"
        self.msg_args_size = "Menetapkan ukuran Window kustom"

        # commonly used
        self.connect = "Sambungkan"
        self.connected = "Tersambung"
        self.connecting = "Manyambungkan..."
        self.disconnect = "Putuskan sambungan"
        self.disconnected = "Tidak tersambung"
        self.disconnecting = "Memutuskan sambungan..."
        self.enable = "Aktifan"
        self.disable = "Nonaktifkan"
        self.close = "Tutup"
        self.show = "Tampilkan"
        self.loading = "Memuat..."
        self.loading_tabs = "Memuat tab..."

        # for tabs
        self.msg_tab_autostart = "Autostart"
        self.msg_tab_usbguard = "USBGuard"
        self.usbguard_title = "USB Device Control"
        self.refresh = "Perbarui"
        self.allow = "Izinkan"
        self.block = "Blokir"
        self.policy = "Lihat kebijakan"
        self.usbguard_error = "Error mengakses USBGuard"
        self.usbguard_not_installed = "USBGuard tidak terinstall"
        self.usbguard_not_running = "layanan USBGuard tidak berjalan"
        self.no_devices = "Tidak ada USB yang tersambung"
        self.operation_failed = "Operasi gagal"
        self.policy_error = "Gagal memuat kebijakan"
        self.msg_tab_battery = "Baterai"
        self.msg_tab_bluetooth = "Bluetooth"
        self.msg_tab_display = "Tampilan"
        self.msg_tab_power = "Power"
        self.msg_tab_volume = "Volume"
        self.msg_tab_wifi = "Wi-Fi"

        # Autostart tab translations
        self.autostart_title = "Aplikasi Autostart"
        self.autostart_session = "Sesi"
        self.autostart_show_system_apps = "Tunjukan aplikasi autostart sistem"
        self.autostart_configured_applications = "Aplikasi terkonfigurasi"
        self.autostart_tooltip_rescan = "Pindai ulang aplikasi autostart"

        # Battery tab translations
        self.battery_title = "Dasbor Baterai"
        self.battery_power_saving = "Hemat Daya"
        self.battery_balanced = "Seimbang"
        self.battery_performance = "Performa"
        self.battery_batteries = "Baterai"
        self.battery_overview = "Gambaran Umum"
        self.battery_details = "Detail"
        self.battery_tooltip_refresh = "Pindai ulang informasi baterai"
        self.battery_no_batteries = "Tidak ada baterai yang terdeteksi"

        # Bluetooth tab translations
        self.bluetooth_title = "Perangkat Bluetooth"
        self.bluetooth_scan_devices = "Pindai perangkat"
        self.bluetooth_scanning = "Memindai..."
        self.bluetooth_power = "Bluetooth"
        self.bluetooth_available_devices = "Perangkat yang tersedia"
        self.bluetooth_tooltip_refresh = "Pindai perangkat"
        self.bluetooth_connect_failed = "Gagal untuk menyambung ke perangkat"
        self.bluetooth_disconnect_failed = "Gagal untuk memutus sambungan ke perangkat"
        self.bluetooth_try_again = "Mohon coba lagi."

        # Display tab translations
        self.display_title = "Pengaturan Tampilan"
        self.display_brightness = "Kecerahan Layar"
        self.display_blue_light = "Anti Radiasi"
        self.display_orientation = "Orientasi"
        self.display_default = "Default"
        self.display_left = "Kiri"
        self.display_right = "Kanan"
        self.display_inverted = "Terbalik"

        # Power tab translations
        self.power_title = "Pengelolaan Daya"
        self.power_tooltip_menu = "Konfigurasi Menu Daya"
        self.power_menu_buttons = "Tombol"
        self.power_menu_commands = "Perintah"
        self.power_menu_colors = "Warna"
        self.power_menu_show_hide_buttons = "Tunjukkan/Sembunyikan Tombol"
        self.power_menu_shortcuts_tab_label = "Pintasan"
        self.power_menu_visibility = "Tombol"
        self.power_menu_keyboard_shortcut = "Pintasan Keyboard"
        self.power_menu_show_keyboard_shortcut = "Tunjukkan Pintasan Keyboard"
        self.power_menu_lock = "Kunci"
        self.power_menu_logout = "Logout"
        self.power_menu_suspend = "Tidur"
        self.power_menu_hibernate = "Hibernasi"
        self.power_menu_reboot = "Reboot"
        self.power_menu_shutdown = "Matikan"
        self.power_menu_apply = "Terapkan"
        self.power_menu_tooltip_lock = "Kunci layar"
        self.power_menu_tooltip_logout = "Keluar dari sesi saat ini"
        self.power_menu_tooltip_suspend = "Menidurkan sistem"
        self.power_menu_tooltip_hibernate = "Menghibernasikan sistem"
        self.power_menu_tooltip_reboot = "Merestart sistem"
        self.power_menu_tooltip_shutdown = "Mematikan perangkat"

        # Volume tab translations
        self.volume_title = "Pengaturan Volume"
        self.volume_speakers = "Speaker"
        self.volume_tab_tooltip = "Pengatures Speaker"
        self.volume_output_device = "Perangkat Output"
        self.volume_device = "Perangkat"
        self.volume_output = "Output"
        self.volume_speaker_volume = "Volume Speaker"
        self.volume_mute_speaker = "Bisukan Speaker"
        self.volume_unmute_speaker = "Menyalakan Speakers"
        self.volume_quick_presets = "Preset Cepat"
        self.volume_output_combo_tooltip = "Piling perangkat output untuk aplikasi ini"

        # Volume tab microphone translations
        self.microphone_tab_microphone = "Mikrofon"
        self.microphone_tab_input_device = "Perangkat Input"
        self.microphone_tab_volume = "Volume Mikrofon"
        self.microphone_tab_mute_microphone = "Bisukan Mikrofon"
        self.microphone_tab_unmute_microphone = "Nyalakn Microphone"
        self.microphone_tab_tooltip = "Pengaturan Mikrofon"

        # Volume tab App output translations
        self.app_output_title = "Output Aplikasi"
        self.app_output_volume = "Volume Output Aplikasi"
        self.app_output_mute = "Bisukan"
        self.app_output_unmute = "Nyalakan"
        self.app_output_tab_tooltip = "Pengaturan Output Aplikasi"
        self.app_output_no_apps = "Tidak ada aplikasi yang mengeluarkan suara"
        self.app_output_dropdown_tooltip = "Pilih perangkat output untuk aplikasi ini"

        # Volume tab App input translations
        self.app_input_title = "Input aplikasi"
        self.app_input_volume = "Volume Input Aplikasi"
        self.app_input_mute = "Bisukan Mikrofon untuk aplikasi ini"
        self.app_input_unmute = "Nyalakan Mikrofon untuk aplikasi ini"
        self.app_input_tab_tooltip = "Pengaturan Mikrofon Aplikasi"
        self.app_input_no_apps = "Tidak ada aplikasi yang menggunakan mikrofon"

        # WiFi tab translations
        self.wifi_title = "Jaringan Wi-Fi"
        self.wifi_refresh_tooltip = "Pindai Ulang Jaringan"
        self.wifi_power = "Wi-Fi"
        self.wifi_speed = "Kecepatan Koneksi"
        self.wifi_download = "Download"
        self.wifi_upload = "Upload"
        self.wifi_available = "Jaringan yang Tersedia"
        self.wifi_forget = "Lupakan"
        self.wifi_share_title = "Bagikan Jaringan"
        self.wifi_share_scan = "Pindai untuk menyambungkan"
        self.wifi_network_name = "Nama Jaringan"
        self.wifi_password = "Password"
        self.wifi_loading_networks = "Memuat Networks..."

        # Settings tab translations
        self.settings_title = "Pengaturan"
        self.settings_tab_settings = "Pengaturan Tab"
        self.settings_language = "Bahasa"
        self.settings_language_changed_restart = "Mulai ulang aplikasi agar perubahan bahasa diterapkan."
        self.settings_language_changed = "Bahasa telah diubah"


class Turkish:
    """Uygulama için Türkçe dil çevirisi"""

    def __init__(self):
        # app description
        self.msg_desc = "Linux için şık bir GTK temalı kontrol paneli."
        self.msg_app_url = "https://github.com/quantumvoid0/better-control"
        self.msg_usage = "Kullanım"

        # USB notifications
        self.usb_connected = "{device} bağlandı."
        self.usb_disconnected = "{device} bağlantısı kesildi."
        self.permission_allowed = "USB izni verildi"
        self.permission_blocked = "USB izni engellendi"

        # for args
        self.msg_args_help = "Bu mesajı yazdırır"
        self.msg_args_autostart = "Otomatik başlatma sekmesi açık olarak başlar"
        self.msg_args_battery = "Pil sekmesi açık olarak başlar"
        self.msg_args_bluetooth = "Bluetooth sekmesi açık olarak başlar"
        self.msg_args_display = "Ekran sekmesi açık olarak başlar"
        self.msg_args_force = "Tüm bağımlılıkların yüklü olmasını zorunlu kılar"
        self.msg_args_power = "Güç sekmesi açık olarak başlar"
        self.msg_args_volume = "Ses sekmesi açık olarak başlar"
        self.msg_args_volume_v = "Ayrıca ses sekmesi açık olarak başlar"
        self.msg_args_wifi = "Wi-Fi sekmesi açık olarak başlar"
        self.msg_args_log = "Program bir dosya yolu verilirse log dosyasına yazar,\n veya 0 ile 3 arasında bir değer verilirse stdout'a yazar."
        self.msg_args_redact = "Loglardan hassas bilgileri gizle (ağ adları, cihaz kimlikleri, vb.)"
        self.msg_args_size = "Özel bir pencere boyutu ayarlar"

        # commonly used
        self.connect = "Bağlan"
        self.connected = "Bağlı"
        self.connecting = "Bağlanıyor..."
        self.disconnect = "Bağlantıyı Kes"
        self.disconnected = "Bağlantı Kesildi"
        self.disconnecting = "Bağlantı Kesiliyor..."
        self.enable = "Etkinleştir"
        self.disable = "Devre Dışı Bırak"
        self.close = "Kapat"
        self.show = "Göster"
        self.loading = "Yükleniyor..."
        self.loading_tabs = "Sekmeler yükleniyor..."

        # for tabs
        self.msg_tab_autostart = "Otomatik Başlatma"
        self.msg_tab_usbguard = "USBGuard"
        self.usbguard_title = "USB Cihaz Kontrolü"
        self.refresh = "Yenile"
        self.allow = "İzin Ver"
        self.block = "Engelle"
        self.allowed = "İzin Verildi"
        self.blocked = "Engellendi"
        self.rejected = "Reddedildi"
        self.policy = "Politikayı Görüntüle"
        self.usbguard_error = "USBGuard'a erişim hatası"
        self.usbguard_not_installed = "USBGuard yüklü değil"
        self.usbguard_not_running = "USBGuard servisi çalışmıyor"
        self.no_devices = "Bağlı USB cihazı yok"
        self.operation_failed = "İşlem başarısız oldu"
        self.policy_error = "Politika yüklenemedi"
        self.permanent_allow = "Kalıcı İzin Ver"
        self.permanent_allow_tooltip = "Bu cihaza kalıcı olarak izin ver (politikaya eklenir)"
        self.msg_tab_battery = "Pil"
        self.msg_tab_bluetooth = "Bluetooth"
        self.msg_tab_display = "Ekran"
        self.msg_tab_power = "Güç"
        self.msg_tab_volume = "Ses"
        self.msg_tab_wifi = "Wi-Fi"

        # Autostart tab translations
        self.autostart_title = "Otomatik Başlatma Uygulamaları"
        self.autostart_session = "Oturum"
        self.autostart_show_system_apps = "Sistem otomatik başlatma uygulamalarını göster"
        self.autostart_configured_applications = "Yapılandırılmış Uygulamalar"
        self.autostart_tooltip_rescan = "Otomatik başlatma uygulamalarını yeniden tara"

        # Battery tab translations
        self.battery_title = "Pil Kontrol Paneli"
        self.battery_power_saving = "Güç Tasarrufu"
        self.battery_balanced = "Dengeli"
        self.battery_performance = "Performans"
        self.battery_batteries = "Piller"
        self.battery_overview = "Genel Bakış"
        self.battery_details = "Ayrıntılar"
        self.battery_tooltip_refresh = "Pil bilgilerini yenile"
        self.battery_no_batteries = "Pil algılanmadı"

        # Bluetooth tab translations
        self.bluetooth_title = "Bluetooth Cihazları"
        self.bluetooth_scan_devices = "Cihazları Tara"
        self.bluetooth_scanning = "Taranıyor..."
        self.bluetooth_power = "Bluetooth"
        self.bluetooth_available_devices = "Mevcut Cihazlar"
        self.bluetooth_tooltip_refresh = "Cihazları Tara"
        self.bluetooth_connect_failed = "Cihaza bağlanılamadı"
        self.bluetooth_disconnect_failed = "Cihaz bağlantısı kesilemedi"
        self.bluetooth_try_again = "Lütfen daha sonra tekrar deneyin."

        # Display tab translations
        self.display_title = "Ekran Ayarları"
        self.display_brightness = "Ekran Parlaklığı"
        self.display_blue_light = "Mavi Işık"
        self.display_orientation = "Yönlendirme"
        self.display_default = "Varsayılan"
        self.display_left = "Sol"
        self.display_right = "Sağ"
        self.display_inverted = "Ters"
        self.display_rotation = "Döndürme Seçenekleri"
        self.display_simple_rotation = "Hızlı Döndürme"
        self.display_specific_orientation = "Belirli Yön"
        self.display_flip_controls = "Ekran Çevirme"
        self.display_rotate_cw = "Saat yönünde döndür"
        self.display_rotate_ccw = "Saat yönünün tersine döndür"
        self.display_rotation_help = "Döndürme işlemi hemen uygulanır. Onaylamazsanız 10 saniye içinde eski haline döner."

        # Power tab translations
        self.power_title = "Güç Yönetimi"
        self.power_tooltip_menu = "Güç menüsünü yapılandır"
        self.power_menu_buttons = "Düğmeler"
        self.power_menu_commands = "Komutlar"
        self.power_menu_colors = "Renkler"
        self.power_menu_show_hide_buttons = "Düğmeleri Göster/Gizle"
        self.power_menu_shortcuts_tab_label = "Kısayollar"
        self.power_menu_visibility = "Düğmeler"
        self.power_menu_keyboard_shortcut = "Klavye Kısayolları"
        self.power_menu_show_keyboard_shortcut = "Klavye Kısayollarını Göster"
        self.power_menu_lock = "Kilitle"
        self.power_menu_logout = "Oturumu Kapat"
        self.power_menu_suspend = "Beklet"
        self.power_menu_hibernate = "Hazırda Beklet"
        self.power_menu_reboot = "Yeniden Başlat"
        self.power_menu_shutdown = "Kapat"
        self.power_menu_apply = "Uygula"
        self.power_menu_tooltip_lock = "Ekranı kilitle"
        self.power_menu_tooltip_logout = "Oturumu kapat"
        self.power_menu_tooltip_suspend = "Sistemi beklet"
        self.power_menu_tooltip_hibernate = "Sistemi hazırda beklet"
        self.power_menu_tooltip_reboot = "Sistemi yeniden başlat"
        self.power_menu_tooltip_shutdown = "Sistemi kapat"

        # Volume tab translations
        self.volume_title = "Ses Ayarları"
        self.volume_speakers = "Hoparlörler"
        self.volume_tab_tooltip = "Hoparlör Ayarları"
        self.volume_output_device = "Çıkış Aygıtı"
        self.volume_device = "Aygıt"
        self.volume_output = "Çıkış"
        self.volume_speaker_volume = "Hoparlör Sesi"
        self.volume_mute_speaker = "Hoparlörü Sessize Al"
        self.volume_unmute_speaker = "Hoparlörü Sesli Yap"
        self.volume_quick_presets = "Hızlı Ön Ayarlar"
        self.volume_output_combo_tooltip = "Bu uygulama için çıkış cihazını seçin"

        # Volume tab microphone translations
        self.microphone_tab_microphone = "Mikrofon"
        self.microphone_tab_input_device = "Giriş Aygıtı"
        self.microphone_tab_volume = "Mikrofon Sesi"
        self.microphone_tab_mute_microphone = "Mikrofonu Sessize Al"
        self.microphone_tab_unmute_microphone = "Mikrofonu Sesli Yap"
        self.microphone_tab_tooltip = "Mikrofon Ayarları"

        # Volume tab App output translations
        self.app_output_title = "Uygulama Çıkışı"
        self.app_output_volume = "Uygulama Ses Çıkış Seviyesi"
        self.app_output_mute = "Sessize Al"
        self.app_output_unmute = "Sesi Aç"
        self.app_output_tab_tooltip = "Uygulama Çıkış Ayarları"
        self.app_output_no_apps = "Ses çalan uygulama yok"
        self.app_output_dropdown_tooltip = "Bu uygulama için çıkış cihazını seçin"

        # Volume tab App input translations
        self.app_input_title = "Uygulama Girişi"
        self.app_input_volume = "Uygulama Mikrofon Giriş Seviyesi"
        self.app_input_mute = "Bu uygulama için mikrofonu sessize al"
        self.app_input_unmute = "Bu uygulama için mikrofonu aç"
        self.app_input_tab_tooltip = "Uygulama Mikrofon Ayarları"
        self.app_input_no_apps = "Mikrofon kullanan uygulama yok"

        # WiFi tab translations
        self.wifi_title = "Wi-Fi Ağları"
        self.wifi_refresh_tooltip = "Ağları Yenile"
        self.wifi_power = "Wi-Fi"
        self.wifi_speed = "Bağlantı Hızı"
        self.wifi_download = "İndirme"
        self.wifi_upload = "Yükleme"
        self.wifi_available = "Mevcut Ağlar"
        self.wifi_forget = "Unut"
        self.wifi_share_title = "Ağı Paylaş"
        self.wifi_share_scan = "Bağlanmak için tarayın"
        self.wifi_network_name = "Ağ Adı"
        self.wifi_password = "Parola"
        self.wifi_loading_networks = "Ağlar Yükleniyor..."

        # Settings tab translations
        self.settings_title = "Ayarlar"
        self.settings_tab_settings = "Sekme Ayarları"
        self.settings_language = "Dil"
        self.settings_language_changed_restart = "Dil değişikliği için lütfen uygulamayı yeniden başlatın."
        self.settings_language_changed = "Dil değiştirildi"


def _map_system_lang_to_code(system_lang: str, logger: Optional[Logger] = None) -> str:
    """Helper function to map system language to supported code and optionally log mapping"""
    if system_lang.startswith("es"):
        if logger:
            logger.log(
                LogLevel.Info, f"System language '{system_lang}' mapped to Spanish (es)")
        return "es"
    if system_lang.startswith("it"):
        if logger:
            logger.log(
                LogLevel.Info, f"System language '{system_lang}' mapped to Italian (it)")
        return "it"
    elif system_lang.startswith("pt"):
        if logger:
            logger.log(
                LogLevel.Info, f"System language '{system_lang}' mapped to Portuguese (pt)")
        return "pt"
    elif system_lang.startswith("fr"):
        if logger:
            logger.log(
                LogLevel.Info, f"System language '{system_lang}' mapped to French (fr)")
        return "fr"
    elif system_lang.startswith("id"):
        if logger:
            logger.log(
                LogLevel.Info, f"System language '{system_lang}' mapped to Indonesian (id)")
        return "id"
    elif system_lang.startswith("tr"):
        if logger:
            logger.log(
                LogLevel.Info, f"System language '{system_lang}' mapped to Turkish (tr)")
        return "tr"
    elif system_lang.startswith("de"):
        if logger:
            logger.log(
                LogLevel.Info, f"System language '{system_lang}' mapped to German (de)")
        return "de"
    else:
        if logger:
            logger.log(
                LogLevel.Info, f"System language '{system_lang}' not supported, falling back to English (en)")
        return "en"


def get_translations(logging: Optional[Logger] = None, lang: str = "en") -> Translation:
    """Load the language according to the selected language

    Args:
        lang (str): Language code ('en', 'es', 'it', 'pt', 'fr', 'id', 'tr', 'de', 'default')
                   'default' will use the system's $LANG environment variable

    Returns:
        Translation: Translation object for the selected language
    """
    # Handle 'default' option by checking system's LANG environment variable
    if lang == "default":
        env_lang = os.environ.get("LANG")
        if env_lang is None:
            # No LANG env var set, fall back to English immediately
            system_lang_code = "en"
            if logging:
                logging.log(
                    LogLevel.Info, "Environment variable LANG not set, falling back to English")
        else:
            # LANG env var exists
            parts = env_lang.split("_")
            system_lang_code = parts[0].lower()
            if logging:
                logging.log(
                    LogLevel.Info, f"Using system language: {system_lang_code} from $LANG={env_lang}")
        lang = _map_system_lang_to_code(system_lang_code, logging)

    if logging:
        logging.log(LogLevel.Info, f"Using language: {lang}")

    match lang:
        case "ru":
            return Russian()
        case "es":
            return Spanish()
        case "it":
            return Italian()
        case "pt":
            return Portuguese()
        case "fr":
            return French()
        case "id":
            return Indonesian()
        case "tr":
            return Turkish()
        case "de":
            return German()
        case _:
            return English()
