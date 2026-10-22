# Mise à jour auto : Flatpak (system + user) + flake Fray
# Pas de rebuild de l'hôte GLF — VM/flake Fray seulement
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.services.autoUpdate;

  frayAutoUpdate = pkgs.writeShellApplication {
    name = "fray-auto-update";
    runtimeInputs = with pkgs; [
      coreutils
      bash
      flatpak
      util-linux
      networkmanager
      iputils
      gawk
      nix
      libnotify
    ];
    text = ''
      #!/usr/bin/env bash
      set -euo pipefail

      STATE_DIR="/var/lib/fray-auto-update"
      mkdir -p "$STATE_DIR"
      FLAKE_DIR="''${FRAY_FLAKE:-/home/kouro/Téléchargements/GLF pc/NIX/fray}"

      _notify() {
        local title="''${1:-Fray update}"
        local msg="''${2:-}"
        local urgency="''${3:-normal}"
        for path in /run/user/*; do
          [ -d "$path" ] || continue
          local uid user
          uid="$(basename "$path")"
          user="$(id -nu "$uid" 2>/dev/null || true)"
          [ -z "$user" ] && continue
          runuser -u "$user" -- env \
            XDG_RUNTIME_DIR="/run/user/$uid" \
            DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$uid/bus" \
            notify-send --urgency="$urgency" --app-name="Fray Update" \
              --icon="system-software-update" "$title" "$msg" || true
        done
      }

      _update_flatpaks() {
        local had_failure=0 user user_uid user_home
        echo "[INFO] Flatpak update (system)..." >&2
        flatpak update -y || had_failure=1
        while IFS=: read -r user _ user_uid _ _ user_home _; do
          if [ "$user_uid" -lt 1000 ] || [ "$user_uid" -ge 65534 ] \
              || [ ! -d "$user_home/.local/share/flatpak" ]; then
            continue
          fi
          echo "[INFO] Flatpak --user update ($user)..." >&2
          runuser -u "$user" -- env HOME="$user_home" \
            flatpak --user update -y || had_failure=1
        done < /etc/passwd
        return "$had_failure"
      }

      _cleanup_flatpaks() {
        flatpak uninstall --unused -y || true
        while IFS=: read -r user _ user_uid _ _ user_home _; do
          if [ "$user_uid" -lt 1000 ] || [ "$user_uid" -ge 65534 ] \
              || [ ! -d "$user_home/.local/share/flatpak" ]; then
            continue
          fi
          runuser -u "$user" -- env HOME="$user_home" \
            flatpak --user uninstall --unused -y || true
        done < /etc/passwd
      }

      echo "[INFO] Waiting for network..." >&2
      nm-online -q --timeout=60 || true
      until ping -c1 -W5 1.1.1.1 >/dev/null 2>&1; do sleep 5; done

      if _update_flatpaks; then
        echo "[INFO] Flatpak OK" >&2
      else
        _notify "Fray update — Flatpak" "Au moins une mise à jour Flatpak a échoué." normal
      fi
      _cleanup_flatpaks

      # Flake Fray : update lock seulement — JAMAIS rebuild hôte
      if [ -f "$FLAKE_DIR/flake.nix" ]; then
        echo "[INFO] nix flake update in $FLAKE_DIR" >&2
        if ( cd "$FLAKE_DIR" && nix flake update ); then
          echo "[INFO] flake.lock updated. Rebuild VM: nix build .#vm" >&2
          echo "flake-updated $(date -Iseconds)" > "$STATE_DIR/last-status"
          _notify "Fray update" "flake.lock à jour. Rebuild VM : nix build .#vm" normal
        else
          echo "[WARN] flake update failed" >&2
          echo "flake-failed $(date -Iseconds)" > "$STATE_DIR/last-status"
          _notify "Fray update — erreur" "nix flake update a échoué." critical
        fi
      else
        echo "[INFO] Pas de flake Fray ($FLAKE_DIR) — Flatpak only" >&2
        echo "flatpak-only $(date -Iseconds)" > "$STATE_DIR/last-status"
      fi
    '';
  };
in
{
  options.fray.services.autoUpdate = {
    enable = lib.mkEnableOption "Automatic Flatpak + Fray flake update timer";
    onCalendar = lib.mkOption {
      type = lib.types.str;
      default = "weekly";
      description = "systemd OnCalendar for the auto-update timer";
    };
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [ frayAutoUpdate ];

    nix.gc = {
      automatic = true;
      dates = "weekly";
      options = "--delete-older-than 14d";
    };
    nix.settings.auto-optimise-store = true;

    systemd.services.fray-auto-update = {
      description = "Fray Flatpak + flake update (no host rebuild)";
      after = [ "network-online.target" ];
      wants = [ "network-online.target" ];
      serviceConfig = {
        Type = "oneshot";
        ExecStart = "${frayAutoUpdate}/bin/fray-auto-update";
      };
    };

    systemd.timers.fray-auto-update = {
      description = "Timer for fray-auto-update";
      wantedBy = [ "timers.target" ];
      timerConfig = {
        OnCalendar = cfg.onCalendar;
        Persistent = true;
        RandomizedDelaySec = "30m";
      };
    };
  };
}
