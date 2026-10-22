# CLI unifiée fray-update (flake/flatpak ; --switch/--build/--boot via nh)
# Refuse tout rebuild sur hôte GLF (exit 2)
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.services.updateManager;
  nhCfg = config.fray.system.nh or { };
  defaultFlake =
    nhCfg.flake or "/home/kouro/Téléchargements/GLF pc/NIX/fray";
  defaultHost = nhCfg.hostname or "fray-iso";

  frayUpdate = pkgs.writeShellApplication {
    name = "fray-update";
    runtimeInputs = with pkgs; [
      coreutils
      bash
      nix
      nh
      flatpak
      util-linux
      networkmanager
      iputils
      gawk
      libnotify
    ];
    text = ''
      #!/usr/bin/env bash
      set -euo pipefail

      FLAKE_DIR="''${FRAY_FLAKE:-${defaultFlake}}"
      HOST="''${FRAY_HOST:-${defaultHost}}"
      MODE="update" # update | switch | build | boot

      usage() {
        cat <<'EOF'
fray-update - mise à jour Fray (pas l'hôte GLF)

  fray-update              flake update + Flatpak (pas de switch)
  fray-update --switch     nh os switch  (système Fray seulement)
  fray-update --build      nh os build
  fray-update --boot       nh os boot
  fray-update --help

Variables : FRAY_FLAKE, FRAY_HOST (défaut fray-iso)
EOF
      }

      while [ "$#" -gt 0 ]; do
        case "$1" in
          --switch) MODE="switch" ;;
          --build) MODE="build" ;;
          --boot) MODE="boot" ;;
          --help|-h) usage; exit 0 ;;
          --host|-H)
            shift
            HOST="''${1:-}"
            [ -n "$HOST" ] || { echo "[Fray] --host attend une valeur" >&2; exit 1; }
            ;;
          --flake)
            shift
            FLAKE_DIR="''${1:-}"
            [ -n "$FLAKE_DIR" ] || { echo "[Fray] --flake attend un chemin" >&2; exit 1; }
            ;;
          *)
            echo "[Fray] Option inconnue: $1" >&2
            usage >&2
            exit 1
            ;;
        esac
        shift
      done

      _is_glf_host() {
        [ -x /run/current-system/sw/bin/glf-update ] \
          || command -v glf-switch >/dev/null 2>&1 \
          || command -v glf-update >/dev/null 2>&1
      }

      _refuse_glf_rebuild() {
        if _is_glf_host; then
          echo "[Fray] Rebuild hôte GLF interdit via fray-update (exit 2)." >&2
          echo "[Fray] Sur l'hôte : glf-switch / glf-update. Pour Fray : VM ou système Fray." >&2
          exit 2
        fi
      }

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

      _do_update() {
        echo "[INFO] Waiting for network..." >&2
        nm-online -q --timeout=60 || true
        until ping -c1 -W5 1.1.1.1 >/dev/null 2>&1; do sleep 5; done

        if _update_flatpaks; then
          echo "[INFO] Flatpak OK" >&2
        else
          _notify "Fray update - Flatpak" "Au moins une mise à jour Flatpak a échoué." normal
        fi
        _cleanup_flatpaks

        if [ -f "$FLAKE_DIR/flake.nix" ]; then
          echo "[INFO] nix flake update in $FLAKE_DIR" >&2
          if ( cd "$FLAKE_DIR" && nix flake update ); then
            echo "[INFO] flake.lock à jour. Switch Fray : fray-update --switch" >&2
            _notify "Fray update" "flake.lock à jour. Ensuite : fray-update --switch" normal
          else
            echo "[WARN] flake update failed" >&2
            _notify "Fray update - erreur" "nix flake update a échoué." critical
            return 1
          fi
        else
          echo "[INFO] Pas de flake Fray ($FLAKE_DIR) - Flatpak only" >&2
        fi
      }

      _do_nh() {
        local action="$1"
        _refuse_glf_rebuild
        if [ ! -f "$FLAKE_DIR/flake.nix" ]; then
          echo "[Fray] Flake introuvable: $FLAKE_DIR (exporte FRAY_FLAKE=…)" >&2
          exit 1
        fi
        echo "[Fray] nh os $action $FLAKE_DIR -H $HOST" >&2
        exec nh os "$action" "$FLAKE_DIR" -H "$HOST"
      }

      case "$MODE" in
        update) _do_update ;;
        switch) _do_nh switch ;;
        build) _do_nh build ;;
        boot) _do_nh boot ;;
      esac
    '';
  };
in
{
  options.fray.services.updateManager = {
    enable = lib.mkEnableOption "fray-update CLI (update / --switch / --build / --boot)";
    package = lib.mkOption {
      type = lib.types.package;
      readOnly = true;
      default = frayUpdate;
      description = "Derivation fray-update (CLI unifiée)";
    };
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [ frayUpdate ];
    environment.variables.FRAY_FLAKE = lib.mkDefault defaultFlake;
    environment.variables.FRAY_HOST = lib.mkDefault defaultHost;
  };
}
