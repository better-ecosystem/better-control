"""
Spanish language translation for Better Control
"""

from translations.translation_manager import TranslationManager

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

        #for tabs
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

# Register the language with the TranslationManager
TranslationManager.register_language("es", Spanish)