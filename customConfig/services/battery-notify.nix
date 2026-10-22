# Notifs batterie manettes / souris (upower hidpp) - NixOS user services
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.services.batteryNotify;

  script = pkgs.writeShellApplication {
    name = "fray-battery-check";
    runtimeInputs = with pkgs; [
      upower
      libnotify
      gnugrep
      gawk
      coreutils
    ];
    text = ''
      set -euo pipefail
      tier_of() {
        local pct="$1"
        if   [ "$pct" -le 40 ]; then echo "faible"
        elif [ "$pct" -le 60 ]; then echo "moyenne"
        elif [ "$pct" -le 80 ]; then echo "haute"
        else echo "pleine"
        fi
      }
      icon_of() {
        case "$1" in
          faible)  echo "battery-caution" ;;
          moyenne) echo "battery-low" ;;
          haute)   echo "battery-good" ;;
          pleine)  echo "battery-full-charged" ;;
        esac
      }
      urgency_of() {
        case "$1" in
          faible) echo "critical" ;;
          *)      echo "normal" ;;
        esac
      }
      for dev in $(upower -e | grep -i 'battery_hidpp' || true); do
        info=$(upower -i "$dev" 2>/dev/null || true)
        [ -z "$info" ] && continue
        name=$(echo "$info" | grep -i "model:" | head -1 | sed 's/.*model:[[:space:]]*//')
        [ -z "$name" ] && name="Périphérique"
        percentage=$(echo "$info" | grep -oP 'percentage:[[:space:]]*\K[0-9]+' || true)
        [ -z "$percentage" ] && continue
        dev_id=$(basename "$dev")
        STATE_FILE="/tmp/.fray-battery-tier-''${dev_id}"
        tier=$(tier_of "$percentage")
        last_tier=""
        [ -f "$STATE_FILE" ] && last_tier=$(cat "$STATE_FILE")
        if [ "$tier" != "$last_tier" ]; then
          notify-send -u "$(urgency_of "$tier")" -i "$(icon_of "$tier")" \
            "Batterie ''${tier}" "''${name} : ''${percentage}%"
          echo "$tier" > "$STATE_FILE"
        fi
      done
    '';
  };
in
{
  options.fray.services.batteryNotify = {
    enable = lib.mkEnableOption "Controller/mouse battery notifications via upower";
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [
      script
      pkgs.upower
      pkgs.libnotify
    ];

    systemd.user.services.fray-battery-check = {
      description = "Fray battery check (controllers / mice)";
      serviceConfig = {
        Type = "oneshot";
        ExecStart = "${script}/bin/fray-battery-check";
      };
    };

    systemd.user.timers.fray-battery-check = {
      description = "Timer Fray battery check";
      wantedBy = [ "timers.target" ];
      timerConfig = {
        OnBootSec = "30s";
        OnUnitActiveSec = "20min";
        Persistent = true;
      };
    };
  };
}
