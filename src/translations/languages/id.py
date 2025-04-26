"""
English language translation for Better Control
"""

from translations.translation_manager import TranslationManager

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

# Register the language with the TranslationManager
TranslationManager.register_language("id", Indonesian)