#!/usr/bin/env sh
# A simple script to install or uninstall Better Control on your OS
clear
printf '\033[32mBetter Control Manager\033[0m\n'
printf 'your version : \033[34m6.12.2\033[0m\n'
echo " "
printf 'This script is still under development to improve it if you find any errors head over to \033[31m\033[1mhttps://github.com/better-ecosystem/better-control/issues\033[0m and open an issue on it\n'
echo " "

set -e

install_arch() {
  cd "$HOME"
  rm -rf ~/better-control-git
  git clone https://aur.archlinux.org/better-control-git.git
  clear
  cd better-control-git
  makepkg -si --noconfirm
  cd "$HOME"
  rm -rf ~/better-control-git
  clear
  printf '\033[1m\033[4m✅ Installation complete. You can run Better Control using the command '\''control'\'' or open the better-control app.\033[0m\n'
}

install_debian() {
  echo "⬇️Installing dependencies for Debian-based systems..."
  sudo apt update
  sudo apt install -y libgtk-3-dev network-manager bluez bluez-tools pulseaudio-utils brightnessctl python3-gi python3-dbus python3 power-profiles-daemon gammastep python3-requests python3-qrcode python3-setproctitle python3-pil usbguard

  clear
  cd "$HOME"
  rm -rf ~/better-control
  git clone https://github.com/better-ecosystem/better-control.git
  cd better-control
  sudo make install
  cd "$HOME"
  rm -rf ~/better-control
  clear
  printf '\033[1m4m✅ Installation complete. You can run Better Control using the command '\''control'\'' or open the better-control app.\033[0m\n'
}

install_fedora() {
  echo "⬇️Installing dependencies for Fedora-based systems..."
  sudo dnf install -y gtk3 NetworkManager bluez pulseaudio-utils \
    python3-gobject python3-dbus python3 power-profiles-daemon \
    gammastep python3-requests python3-qrcode python3-setproctitle \
    python3-pillow usbguard brightnessctl make --allowerasing
  clear
  cd "$HOME"
  rm -rf ~/better-control
  git clone https://github.com/better-ecosystem/better-control.git
  cd better-control
  sudo make install
  cd "$HOME"
  rm -rf ~/better-control
  clear
  printf '\033[1m4m✅ Installation complete. You can run Better Control using the command '\''control'\'' or open the better-control app.\033[0m\n'
}

install_void() {
  echo "⬇️Installing dependencies for Void Linux..."
  sudo xbps-install -Sy NetworkManager pulseaudio-utils brightnessctl python3-gobject python3-dbus python3 power-profiles-daemon gammastep python3-requests python3-qrcode gtk+3 bluez python3-Pillow usbguard python3-pip python3-setproctitle
  clear
  cd "$HOME"
  rm -rf ~/better-control
  git clone https://github.com/better-ecosystem/better-control.git
  cd better-control
  sudo make install
  cd "$HOME"
  rm -rf ~/better-control
  clear
  printf '\033[1m4m✅ Installation complete. You can run Better Control using the command '\''control'\'' or open the better-control app.\033[0m\n'
}

install_alpine() {
  echo "⬇️Installing dependencies for Alpine Linux..."
  sudo apk add gtk3 networkmanager bluez bluez-utils pulseaudio-utils brightnessctl py3-gobject py3-dbus python3 power-profiles-daemon gammastep py3-requests py3-qrcode py3-pip py3-setuptools gcc musl-dev python3-dev py3-pillow
  pip install setproctitle
  clear
  cd "$HOME"
  rm -rf ~/better-control
  git clone https://github.com/better-ecosystem/better-control.git
  cd better-control
  sudo make install
  cd "$HOME"
  rm -rf ~/better-control
  clear
  printf '\033[1m4m✅ Installation complete. You can run Better Control using the command '\''control'\'' or open the better-control app.\033[0m\n'
}

install_opensuse() {
  echo "⬇️Installing dependencies for openSUSE Tumbleweed..."
  sudo zypper --non-interactive install -y gtk3-devel NetworkManager bluez pulseaudio-utils \
    brightnessctl python3-gobject python3-dbus-python python3 power-profiles-daemon \
    gammastep python3-requests python3-qrcode python3-setproctitle \
    python3-Pillow usbguard make

  clear
  cd "$HOME"
  rm -rf ~/better-control
  git clone https://github.com/better-ecosystem/better-control.git
  cd better-control
  sudo make install
  cd "$HOME"
  rm -rf ~/better-control
  clear
  printf '\033[1m4m✅ Installation complete. You can run Better Control using the command '\''control'\'' or open the better-control app.\033[0m\n'
}

uninstall_arch() {
  echo "Uninstalling better-control-git on Arch Linux..."
  sudo pacman -R --noconfirm better-control-git
  clear
  printf '\033[1m4m✅ Uninstallation complete.\033[0m\n'
}

uninstall_others() {
  echo "Uninstalling better-control on other distros..."
  cd "$HOME"
  rm -rf ~/better-control
  git clone https://github.com/better-ecosystem/better-control
  cd better-control
  sudo make uninstall
  cd "$HOME"
  rm -rf ~/better-control
  clear
  printf '\033[1m4m✅ Uninstallation complete.\033[0m\n'
}

detect_os() {
  if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "$ID"
  else
    echo "unknown"
  fi
}

confirm() {
  # Prompt for yes/no confirmation
  while true; do
    printf '%s [y/n]: ' "$1"
    read -r yn
    case $yn in
    [Yy]*) return 0 ;;
    [Nn]*) return 1 ;;
    *) echo "Please answer yes or no. (Y for yes and N for no)" ;;
    esac
  done
}

printf '\033[1mDo you want to install or uninstall or update Better Control?\0330\n'
printf '\033[32m 0) Install\033[0m\n'
printf '\033[32m 1) Uninstall\033[0m\n'
printf '\033[32m 2) Update\033[0m\n'
printf '\033[3myour answer:\0330\n'
read -r choice

case "$choice" in
0 | i | I | install)
  echo "Starting installation..."
  detect_os_id=$(detect_os)
  case "$detect_os_id" in
  arch | endeavouros | manjaro | garuda | cachyos | archarm | omarchy)
    install_arch
    ;;
  debian | ubuntu | linuxmint | pop)
    install_debian
    ;;
  fedora | rhel)
    install_fedora
    ;;
  void)
    install_void
    ;;
  alpine)
    install_alpine
    ;;
  opensuse-tumbleweed | opensuse | opensuse-leap | suse | sles)
    install_opensuse
    ;;
  nixos)
    echo "❄️ Detected NixOS. This package has an unofficial flake here:"
    echo "https://github.com/Rishabh5321/better-control-flake"
    ;;
  *)
    echo "❌ Unsupported distro: $detect_os_id please open an issue on the GitHub repository on this and well add your distro."
    exit 1
    ;;
  esac
  ;;
1 | u | U | uninstall)
  echo "You chose to uninstall Better Control."
  if confirm "Are you sure you want to uninstall? Y for yes , N for no"; then
    detect_os_id=$(detect_os)
    case "$detect_os_id" in
    arch | endeavouros | manjaro | garuda)
      uninstall_arch
      ;;
    *)
      uninstall_others
      ;;
    esac
  else
    echo "❌ Uninstallation cancelled."
  fi
  ;;

2 | update | Update)
  echo "Starting update (uninstall and reinstall)..."
  detect_os_id=$(detect_os)
  case "$detect_os_id" in
  arch | endeavouros | manjaro | garuda)
    echo "Uninstalling on Arch-based distro..."
    uninstall_arch
    echo "Installing on Arch-based distro..."
    install_arch
    ;;
  debian | ubuntu | linuxmint | pop)
    echo "Uninstalling on Debian-based distro..."
    uninstall_others
    echo "Installing on Debian-based distro..."
    install_debian
    ;;
  fedora | rhel)
    echo "Uninstalling on Fedora-based distro..."
    uninstall_others
    echo "Installing on Fedora-based distro..."
    install_fedora
    ;;
  void)
    echo "Uninstalling on Void Linux..."
    uninstall_others
    echo "Installing on Void Linux..."
    install_void
    ;;
  alpine)
    echo "Uninstalling on Alpine Linux..."
    uninstall_others
    echo "Installing on Alpine Linux..."
    install_alpine
    ;;
  opensuse-tumbleweed | opensuse | opensuse-leap | suse | sles)
    echo "Uninstalling on openSUSE..."
    uninstall_others
    echo "Installing on openSUSE..."
    install_opensuse
    ;;
  nixos)
    echo "❄️ Detected NixOS. This package has an unofficial flake here:"
    echo "https://github.com/Rishabh5321/better-control-flake"
    ;;
  *)
    echo "❌ Unsupported distro: $detect_os_id please open an issue on the GitHub repository on this and well add your distro."
    exit 1
    ;;
  esac
  echo "✅ Update complete."
  ;;

*)
  echo "Invalid choice. Please run the script again and choose 'install' or 'uninstall'."
  exit 1
  ;;
esac
