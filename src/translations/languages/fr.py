"""
French language translation for Better Control
"""

from translations.translation_manager import TranslationManager

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

# Register the language with the TranslationManager
TranslationManager.register_language("fr", French)