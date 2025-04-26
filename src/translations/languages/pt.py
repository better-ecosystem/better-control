"""
Portuguese language translation for Better Control
"""

from translations.translation_manager import TranslationManager

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

# Register the language with the TranslationManager
TranslationManager.register_language("pt", Portuguese)