# Selecteur de langue session
# Live ISO : dialogue au 1er demarrage (autologin saute le menu GDM).
# Systeme installe (Calamares) : PAS de dialogue - respecte i18n.defaultLocale.
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.system.loginLanguage;

  locales = [
    "C.UTF-8/UTF-8"
    "en_US.UTF-8/UTF-8"
    "fr_FR.UTF-8/UTF-8"
    "de_DE.UTF-8/UTF-8"
    "es_ES.UTF-8/UTF-8"
    "it_IT.UTF-8/UTF-8"
    "pt_BR.UTF-8/UTF-8"
  ];

  fray-lang-select = pkgs.writeShellApplication {
    name = "fray-lang-select";
    runtimeInputs = with pkgs; [
      zenity
      glib
      dbus
    ];
    text = ''
      set -euo pipefail

      marker="''${XDG_CONFIG_HOME:-$HOME/.config}/fray/lang-selected"
      mkdir -p "$(dirname "$marker")"

      force=0
      if [[ "''${1:-}" == "--force" ]]; then
        force=1
      fi

      if [[ "$force" != 1 && -f "$marker" ]]; then
        exit 0
      fi

      # Systeme installe (Calamares) : ne jamais re-proposer (ecrase le choix install).
      # Live ISO : /iso present ou hostname fray-iso.
      if [[ "$force" != 1 ]]; then
        if [[ -f /etc/calamares-generated.nix ]] \
          || { [[ ! -d /iso ]] && [[ "$(hostname 2>/dev/null || true)" != "fray-iso" ]]; }; then
          date -Iseconds > "$marker"
          echo "skipped-installed" >> "$marker"
          exit 0
        fi
      fi

      choice="$(
        zenity --list \
          --title="Fray - langue / language" \
          --text="Choisir la langue de la session\nChoose the session language" \
          --column="Code" --column="Langue" \
          --width=420 --height=320 \
          "fr_FR.UTF-8" "Francais" \
          "en_US.UTF-8" "English" \
          "de_DE.UTF-8" "Deutsch" \
          "es_ES.UTF-8" "Espanol" \
          "it_IT.UTF-8" "Italiano" \
          "pt_BR.UTF-8" "Portugues (Brasil)" \
          || true
      )"

      if [[ -z "''${choice:-}" ]]; then
        exit 0
      fi

      case "$choice" in
        fr_FR.UTF-8) xkb="fr" ;;
        de_DE.UTF-8) xkb="de" ;;
        es_ES.UTF-8) xkb="es" ;;
        it_IT.UTF-8) xkb="it" ;;
        pt_BR.UTF-8) xkb="br" ;;
        *) xkb="us" ;;
      esac

      printf 'LANG=%s\n' "$choice" > "''${XDG_CONFIG_HOME:-$HOME/.config}/locale.conf"

      if uid="$(id -u)" && [[ -n "$uid" ]]; then
        user_path="$(
          dbus-send --system --print-reply --dest=org.freedesktop.Accounts \
            /org/freedesktop/Accounts org.freedesktop.Accounts.FindUserById "int64:$uid" \
            2>/dev/null | awk '/object path/ { gsub(/"/,"",$3); print $3; exit }' || true
        )"
        if [[ -n "''${user_path:-}" ]]; then
          dbus-send --system --print-reply --dest=org.freedesktop.Accounts \
            "$user_path" org.freedesktop.Accounts.User.SetLanguage "string:$choice" \
            >/dev/null 2>&1 || true
        fi
      fi

      if command -v gsettings >/dev/null 2>&1; then
        gsettings set org.gnome.desktop.input-sources sources "[('xkb', '$xkb')]" || true
        gsettings set org.gnome.system.locale region "$choice" || true
      fi

      export LANG="$choice"
      export LC_ALL="$choice"

      date -Iseconds > "$marker"
      echo "$choice" >> "$marker"

      zenity --info --title="Fray" --width=360 \
        --text="Langue reglee : $choice\nClavier : $xkb\n\nReconnecte-toi (ou reboot) pour appliquer partout.\nLog out (or reboot) to apply everywhere." \
        || true
    '';
  };

  autostart = pkgs.writeTextFile {
    name = "fray-lang-select-autostart";
    destination = "/etc/xdg/autostart/fray-lang-select.desktop";
    text = ''
      [Desktop Entry]
      Type=Application
      Name=Fray language
      Comment=Choose session language on first login (live ISO only)
      Exec=${fray-lang-select}/bin/fray-lang-select
      OnlyShowIn=GNOME;KDE;X-Cinnamon;Unity;
      X-GNOME-Autostart-enabled=true
      NoDisplay=true
    '';
  };
in
{
  options.fray.system.loginLanguage = {
    enable = lib.mkEnableOption "Language picker (first session + GDM-ready locales)";

    extraLocales = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = locales;
      description = "Locales glibc limitees (evite rebuild massif, alimente le selecteur).";
    };

    firstSessionDialog = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Dialogue zenity au 1er login. True sur ISO live seulement.";
    };

    unsetSessionLang = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Force LANG=null (menu GDM). Eviter sur systeme installe Calamares.";
    };
  };

  config = lib.mkIf cfg.enable {
    i18n.extraLocales = cfg.extraLocales;

    environment.sessionVariables.LANG = lib.mkIf cfg.unsetSessionLang (lib.mkForce null);

    services.xserver.xkb.layout = lib.mkDefault "fr,us";
    services.xserver.xkb.options = lib.mkDefault "grp:alt_shift_toggle";

    environment.systemPackages = [ fray-lang-select ] ++ lib.optional cfg.firstSessionDialog pkgs.zenity;

    environment.etc = lib.mkIf cfg.firstSessionDialog {
      "xdg/autostart/fray-lang-select.desktop".source =
        "${autostart}/etc/xdg/autostart/fray-lang-select.desktop";
    };
  };
}
