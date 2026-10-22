# ==============================================================================
# Fray — Module 8BitDo Ultimate Software V2
# ==============================================================================
#
# INSTALLATION
# ─────────────
# 1. Ajouter l'import dans configuration.nix :
#      imports = [ ./Modules/8bitdo.nix ];
#
# 2. Rebuild :
#      fray-switch   (ou sudo nixos-rebuild switch)
#
# 3. Premier lancement — télécharge et installe l'appli automatiquement :
#      fray-8bitdo
#
# MISE À JOUR
# ───────────
# Le script vérifie la dernière version à chaque lancement et propose
# de mettre à jour si une nouvelle version est disponible.
#
# DÉSINSTALLATION
# ───────────────
# Retirer l'import dans configuration.nix puis rebuild supprime :
#   ✅ Les paquets Nix  (wineWow64Packages.staging, winetricks, etc.)
#   ✅ La commande      fray-8bitdo
#   ✅ Les règles udev  (accès manette sans root)
#
# Ce qui reste à supprimer manuellement si voulu :
#   ❕ ~/.wine-8bitdo                                   (WINEPREFIX)
#   ❕ ~/.local/share/8BitDo_Ultimate_Software_V2/      (appli + .exe)
#   ❕ ~/.local/share/applications/fray-8bitdo.desktop   (raccourci menu)
#   ❕ ~/.local/share/icons/hicolor/256x256/apps/8bitdo.png
#
#   Commande pour tout nettoyer d'un coup :
#     rm -rf ~/.wine-8bitdo \
#            ~/.local/share/8BitDo_Ultimate_Software_V2 \
#            ~/.local/share/applications/fray-8bitdo.desktop \
#            ~/.local/share/icons/hicolor/256x256/apps/8bitdo.png
#
# BUGS CORRIGÉS (GLF-OS 26.05)
# ────────────────────────────
# ✅ Fenêtre transparente  → force XWayland + registre Wine DWM/WPF
# ✅ Transparente après réduction → DisableComposition + DisableHWAcceleration
# ✅ 2 popups d'erreur     → liés à l'échec d'init WPF en mode Wayland ; corrigés
#                            par le même unset + WINEDLLOVERRIDES Vulkan
# ✅ Winetricks à chaque lancement → .deps_installed flag ajouté
# ✅ Terminal reste ouvert → wine ... & disown ; exit 0 (au lieu de exec wine)
# ✅ Icône vide GNOME      → logo PNG intégré en base64 + réinstall si vide/absent
# ✅ Version bloquée 1.32   → détection via app.8bitdo.com + support.8bitdo.com
# ✅ Popups permission/file → arborescence data/ préservée à l'extraction
#
# ==============================================================================

{ config, pkgs, lib, ... }:

with lib;

let
  cfg = config.fray.gaming.eightBitDo;
  # Logo intégré (256×256 PNG, base64 — fichier unique, pas de 8bitdo.png externe)
  iconBase64 = "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";

  # writeText + base64 -d : ''${iconBase64} dans runCommand ne résout pas la var Nix
  iconB64File = pkgs.writeText "8bitdo-icon.b64" iconBase64;

  iconPng = pkgs.runCommand "8bitdo.png" {
    nativeBuildInputs = [ pkgs.coreutils ];
  } ''
    ${pkgs.coreutils}/bin/base64 -d ${iconB64File} > $out
  '';

  eightBitDoScript = pkgs.writeShellScriptBin "fray-8bitdo" ''
    #!${pkgs.bash}/bin/bash
    set -euo pipefail

    # Chemins
    WINEPREFIX="$HOME/.wine-8bitdo"
    APPDIR="$HOME/.local/share/8BitDo_Ultimate_Software_V2"
    ORIGINAL_EXE="8BitDo Ultimate Software V2.exe"
    RENAMED_EXE="8BitDo_Ultimate_Software_V2.exe"
    VERSION_FILE="$APPDIR/.version"
    DEPS_FLAG="$APPDIR/.deps_installed"
    ZIP_FILE="/tmp/8BitDo_Ultimate_Software_V2.zip"
    DESKTOP_FILE="$HOME/.local/share/applications/fray-8bitdo.desktop"
    ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
    ICON_FILE="$ICON_DIR/8bitdo.png"
    EMBEDDED_ICON="${iconPng}"

    export WINEPREFIX
    export WINEARCH="win64"
    export WINEESYNC=1
    export WINEDEBUG=-all

    mkdir -p "$WINEPREFIX" "$APPDIR" "$ICON_DIR" "$(dirname "$DESKTOP_FILE")"

    # ── Détection de la dernière version disponible ──────────────────────────
    # 8BitDo a migré les versions récentes (≥1.34) vers support.8bitdo.com ;
    # les anciennes (≤1.32) restent sur download.8bitdo.com.
    get_download_url() {
      local ver="$1"
      local candidates=(
        "https://support.8bitdo.com/bd-uploads/files/ultimate_soft/8BitDo_Ultimate_Software_V2_Windows_V''${ver}.zip"
        "https://download.8bitdo.com/Ultimate-Software/8BitDo_Ultimate_Software_V2_Windows_V''${ver}.zip"
      )
      local url status
      for url in "''${candidates[@]}"; do
        status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 8 --head "$url" 2>/dev/null)
        if [ "$status" = "200" ] || [ "$status" = "302" ]; then
          echo "$url"
          return 0
        fi
      done
      return 1
    }

    get_latest_version() {
      local page_ver
      page_ver=$(curl -sL --max-time 10 "https://app.8bitdo.com/Ultimate-Software-V2/" 2>/dev/null \
        | grep -oE '8BitDo_Ultimate_Software_V2_Windows_V[0-9]+\.[0-9]+\.zip' \
        | grep -oE 'V[0-9]+\.[0-9]+' | tr -d 'V' | sort -V | tail -1)
      if [ -n "$page_ver" ]; then
        echo "$page_ver"
        return
      fi

      local found=""
      local minor ver
      for minor in $(seq 31 60); do
        ver="1.''${minor}"
        if get_download_url "$ver" >/dev/null 2>&1; then
          found="$ver"
        fi
      done
      echo "''${found:-1.31}"
    }

    install_app() {
      local ver="$1"
      local url extract_dir src_dir
      url=$(get_download_url "$ver") || true
      if [ -z "$url" ]; then
        echo "❌ Erreur : URL de téléchargement introuvable pour V''${ver}."
        exit 1
      fi

      echo "⬇️  Téléchargement de 8BitDo Ultimate Software V2 (V''${ver})..."
      if command -v curl &> /dev/null; then
        curl -L -o "$ZIP_FILE" "$url" --progress-bar
      elif command -v wget &> /dev/null; then
        wget -O "$ZIP_FILE" "$url" --show-progress
      else
        echo "❌ Erreur : ni 'curl' ni 'wget' n'est installé."
        exit 1
      fi

      if ! head -c 2 "$ZIP_FILE" | grep -q "^PK"; then
        echo "❌ Erreur : Le fichier téléchargé n'est pas un ZIP valide."
        rm -f "$ZIP_FILE"
        exit 1
      fi

      echo "📦 Extraction dans $APPDIR..."
      extract_dir=$(mktemp -d)
      unzip -o -q "$ZIP_FILE" -d "$extract_dir"
      rm -f "$ZIP_FILE"

      src_dir=$(find "$extract_dir" -mindepth 1 -maxdepth 1 -type d | head -1)
      if [ -z "$src_dir" ] || [ ! -f "$src_dir/$ORIGINAL_EXE" ]; then
        echo "❌ Erreur : '$ORIGINAL_EXE' introuvable après extraction."
        rm -rf "$extract_dir"
        exit 1
      fi

      # Conserver l'arborescence (data/, etc.) — ne pas aplatir les sous-dossiers
      rm -rf "$APPDIR"
      mkdir -p "$APPDIR"
      cp -a "$src_dir"/. "$APPDIR/"
      rm -rf "$extract_dir"

      if [ -f "$APPDIR/$ORIGINAL_EXE" ]; then
        mv -f "$APPDIR/$ORIGINAL_EXE" "$APPDIR/$RENAMED_EXE"
      fi
      find "$APPDIR" -name "*.exe" -exec chmod +x {} \;

      echo "$ver" > "$VERSION_FILE"
      echo "✅ Application installée (V''${ver}) !"

      # Réinitialiser le flag des dépendances après une mise à jour
      rm -f "$DEPS_FLAG"
    }

    # ── Vérification de mise à jour ──────────────────────────────────────────
    check_update() {
      echo "🔍 Vérification des mises à jour..."
      local latest
      latest=$(get_latest_version)

      if [ -z "$latest" ]; then
        echo "⚠️  Impossible de vérifier la version en ligne (pas de réseau ?). On continue."
        return
      fi

      local installed="inconnu"
      [ -f "$VERSION_FILE" ] && installed=$(cat "$VERSION_FILE")

      if [ "$installed" = "$latest" ]; then
        echo "✅ Version à jour (V''${latest})"
      else
        echo "🆕 Nouvelle version disponible : V''${latest} (installée : V''${installed})"
        read -p "   Mettre à jour maintenant ? [O/n] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[OoYy]$ ]]; then
          install_app "$latest"
        else
          echo "⏭️  Mise à jour ignorée."
        fi
      fi
    }

    create_shortcut() {
      mkdir -p "$ICON_DIR"

      if [ ! -s "$EMBEDDED_ICON" ]; then
        echo "⚠️  Icône embarquée vide dans le store Nix — relancez fray-switch."
      elif [ ! -f "$ICON_FILE" ] || [ ! -s "$ICON_FILE" ] || ! cmp -s "$EMBEDDED_ICON" "$ICON_FILE"; then
        echo "🖼️  Installation de l'icône..."
        cp "$EMBEDDED_ICON" "$ICON_FILE"
        chmod 644 "$ICON_FILE"
        if [ ! -s "$ICON_FILE" ]; then
          echo "❌ Erreur : l'icône n'a pas pu être copiée."
          rm -f "$ICON_FILE"
        else
          # Rafraîchir le cache icônes GNOME (indispensable sous Wayland)
          ${pkgs.gtk3}/bin/gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor/" 2>/dev/null || true
        fi
      fi

      if [ ! -f "$DESKTOP_FILE" ]; then
        echo "📄 Création du raccourci menu..."
        cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Name=8BitDo Ultimate Software V2
Comment=Configurer les manettes 8BitDo (filaire/sans-fil)
Exec=fray-8bitdo
Icon=8bitdo
Terminal=false
Type=Application
Categories=Game;Utility;HardwareSettings;
StartupWMClass=8BitDo_Ultimate_Software_V2
EOF
        ${pkgs.desktop-file-utils}/bin/update-desktop-database "$(dirname "$DESKTOP_FILE")" 2>/dev/null || true
        echo "✅ Raccourci menu créé !"
      fi
    }

    # ── Installation ou mise à jour ──────────────────────────────────────────
    if [ ! -f "$APPDIR/$RENAMED_EXE" ]; then
      echo "🔍 Recherche de la dernière version disponible..."
      LATEST=$(get_latest_version)
      if [ -z "$LATEST" ]; then
        LATEST="1.31"
        echo "⚠️  Pas de réseau, fallback sur la version V''${LATEST}."
      fi
      read -p "8BitDo Ultimate Software V2 (V''${LATEST}) n'est pas installé. Télécharger ? [O/n] " -n 1 -r
      echo
      if [[ $REPLY =~ ^[OoYy]$ ]]; then
        install_app "$LATEST"
      else
        echo "❌ Annulé. Téléchargez manuellement depuis : https://www.8bitdo.com/ultimate-software-v2/"
        exit 1
      fi
    else
      check_update
    fi

    create_shortcut

    # ── Correctifs registre Wine/WPF (idempotent, rapide) ───────────────────
    # Nécessaire même si les dépendances sont déjà installées (mise à jour GLF).
    wine reg add 'HKCU\Software\Wine\Drivers' /v Graphics /d 'x11' /f >/dev/null 2>&1 || true
    wine reg add 'HKCU\Software\Wine\DWM' /v DisableComposition /d Y /f >/dev/null 2>&1 || true
    wine reg add 'HKCU\Software\Microsoft\Avalon.Graphics' /v DisableHWAcceleration /t REG_DWORD /d 1 /f >/dev/null 2>&1 || true

    # ── Dépendances Windows (une seule fois) ────────────────────────────────
    if [ ! -f "$DEPS_FLAG" ]; then
      echo "🔧 Installation des dépendances Windows (première fois, ~2-5 min)..."
      winetricks -q corefonts vcrun2019 dotnet48 2>/dev/null || true
      touch "$DEPS_FLAG"
      echo "✅ Dépendances installées !"
    fi

    # ── Permissions ─────────────────────────────────────────────────────────
    chmod -R u+rwX,go+rX "$APPDIR"
    find "$APPDIR" -type f -exec chmod 644 {} \;
    find "$APPDIR" -name "*.exe" -exec chmod 755 {} \;
    chmod 755 "$WINEPREFIX" 2>/dev/null || true

    # ── Lancement ───────────────────────────────────────────────────────────
    cd "$APPDIR"
    export DOTNET_SYSTEM_GLOBALIZATION_USENLS=1
    export MONO_THREADS_SUSPEND=preemptive

    # Désactiver le backend Vulkan cassé sous NixOS (runpath manquant, issue #461890)
    export WINEDLLOVERRIDES="winevulkan=d;winebus.sys=b;winewayland,d=d"
    export MESA_VK_DEVICE_SELECT_FORCE_DEFAULT_DEVICE=1
    export WINEFSYNC=1

    # !! FIX FENÊTRE TRANSPARENTE (GLF-OS 26.05 / Wine 9.22+) !!
    # Wine 9.22+ utilise le backend Wayland natif par défaut quand WAYLAND_DISPLAY
    # est présent. Ce backend échoue silencieusement avec les apps WPF/.NET →
    # fenêtre transparente + popups d'erreur, surtout après réduction.
    # Solution : forcer XWayland (X11) via variables d'environnement + registre.
    unset WAYLAND_DISPLAY
    export WINE_DISABLE_WAYLAND=1
    export GDK_BACKEND=x11
    export SDL_VIDEODRIVER=x11
    export QT_QPA_PLATFORM=xcb

    # Lancer en arrière-plan et rendre la main au terminal immédiatement
    wine "$RENAMED_EXE" > /tmp/8bitdo-wine.log 2>&1 &
    WINE_PID=$!
    echo "✅ 8BitDo lancé (PID: $WINE_PID)"
    echo "   Log disponible : /tmp/8bitdo-wine.log"
    disown $WINE_PID
    exit 0
  '';
in
{
  options.fray.gaming.eightBitDo = {
    enable = lib.mkEnableOption "8BitDo Ultimate Software V2 via Wine (heavy; off by default)";
  };

  config = lib.mkIf cfg.enable {

  environment.systemPackages = with pkgs; [
    wineWow64Packages.staging
    winetricks
    unzip
    curl
    wget
    gtk3            # pour gtk-update-icon-cache
    eightBitDoScript
    desktop-file-utils
  ];

  # ── Règles udev (une règle par ligne) ──────────────────────────────────────
  services.udev.extraRules = ''
    SUBSYSTEM=="usb", ATTRS{idVendor}=="2dc8", ATTRS{idProduct}=="6012", MODE="0666", GROUP="users", TAG+="uaccess"
    SUBSYSTEM=="usb", ATTRS{idVendor}=="2dc8", ATTRS{idProduct}=="6013", MODE="0666", GROUP="users", TAG+="uaccess"
    SUBSYSTEM=="usb", ATTRS{idVendor}=="2dc8", ATTRS{idProduct}=="310b", MODE="0666", GROUP="users", TAG+="uaccess"
    SUBSYSTEM=="usb", ATTRS{idVendor}=="2dc8", ATTRS{idProduct}=="3106", MODE="0666", GROUP="users", TAG+="uaccess"
    SUBSYSTEM=="usb", ATTRS{idVendor}=="2dc8", ATTRS{idProduct}=="3208", MODE="0666", GROUP="users", TAG+="uaccess"
    SUBSYSTEM=="hidraw", ATTRS{idVendor}=="2dc8", MODE="0666", GROUP="users", TAG+="uaccess"
  '';

  system.activationScripts.reloadUdev8BitDo = ''
    ${pkgs.systemd}/bin/udevadm control --reload-rules
    ${pkgs.systemd}/bin/udevadm trigger --subsystem-match=usb    --action=add
    ${pkgs.systemd}/bin/udevadm trigger --subsystem-match=hidraw --action=add
  '';

  };
}
