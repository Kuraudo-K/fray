# CLI fray-update + GUI Rust Fray Update Manager (ref GLF update-manager)
# Refuse tout rebuild sur hôte GLF (exit 2)
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.services.updateManager;
  guiCfg = config.fray.services.updateManagerGui;
  nhCfg = config.fray.system.nh or { };
  defaultFlake = nhCfg.flake or "/etc/nixos";
  defaultHost = nhCfg.hostname or "fray";
  stateDir = "/var/lib/fray-update-manager";
  prefsFile = "/etc/nixos/customConfig/services/fray-update-manager-prefs.nix";

  weekdayOk = lib.elem guiCfg.schedule.weekday [
    "Mon"
    "Tue"
    "Wed"
    "Thu"
    "Fri"
    "Sat"
    "Sun"
  ];

  calendar =
    let
      hh = lib.fixedWidthString 2 "0" (toString guiCfg.schedule.hour);
      mm = lib.fixedWidthString 2 "0" (toString guiCfg.schedule.minute);
    in
    "${guiCfg.schedule.weekday} *-*-* ${hh}:${mm}:00";

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
      NOTIFY=0

      usage() {
        cat <<'EOF'
fray-update - mise a jour Fray (pas l'hote GLF)

  fray-update              flake update + Flatpak (pas de switch)
  fray-update --switch     nh os switch  (systeme Fray seulement)
  fray-update --build      nh os build
  fray-update --boot       nh os boot
  fray-update --notify     notifications desktop
  fray-update --help

Variables : FRAY_FLAKE, FRAY_HOST (defaut /etc/nixos #fray)
EOF
      }

      while [ "$#" -gt 0 ]; do
        case "$1" in
          --switch) MODE="switch" ;;
          --build) MODE="build" ;;
          --boot) MODE="boot" ;;
          --notify) NOTIFY=1 ;;
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
          echo "[Fray] Rebuild hote GLF interdit via fray-update (exit 2)." >&2
          echo "[Fray] Sur l'hote : glf-switch / glf-update. Pour Fray : VM ou systeme Fray." >&2
          exit 2
        fi
      }

      _notify() {
        [ "$NOTIFY" = 1 ] || return 0
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
        if ! command -v flatpak >/dev/null 2>&1; then
          echo "[INFO] Flatpak absent - skip" >&2
          return 0
        fi
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
        command -v flatpak >/dev/null 2>&1 || return 0
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
          _notify "Fray update - Flatpak" "Au moins une mise a jour Flatpak a echoue." normal
        fi
        _cleanup_flatpaks

        if [ -f "$FLAKE_DIR/flake.nix" ]; then
          echo "[INFO] nix flake update in $FLAKE_DIR" >&2
          if ( cd "$FLAKE_DIR" && nix flake update ); then
            echo "[INFO] flake.lock a jour. Switch Fray : fray-update --switch" >&2
            _notify "Fray update" "flake.lock a jour. Ensuite : fray-update --switch" normal
          else
            echo "[WARN] flake update failed" >&2
            _notify "Fray update - erreur" "nix flake update a echoue." critical
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

  frayUpdatePowered = pkgs.writeShellApplication {
    name = "fray-update-powered";
    runtimeInputs = with pkgs; [
      coreutils
      util-linux
      systemd
    ];
    text = ''
      set -euo pipefail
      STATE="${stateDir}/power-mode"
      MODE="standard"
      UPDATE_BIN="${frayUpdate}/bin/fray-update"
      if [ -r "$STATE" ]; then
        MODE=$(tr -d '[:space:]' < "$STATE" || true)
      fi
      case "$MODE" in
        standard|eco) ;;
        *) MODE="standard" ;;
      esac

      echo "[INFO] Fray Update Manager - mode: $MODE" >&2

      case "$MODE" in
        eco)
          CORES=$(nproc 2>/dev/null || echo 1)
          HALF=$(( CORES / 2 ))
          if [ "$HALF" -lt 1 ]; then HALF=1; fi
          QUOTA=$(( HALF * 100 ))
          echo "[INFO] Eco - $HALF/$CORES coeurs (CPUQuota=$QUOTA%)" >&2
          if command -v systemd-run >/dev/null 2>&1; then
            exec systemd-run --quiet --collect --scope \
              -p "CPUQuota=$QUOTA%" \
              -p CPUWeight=20 \
              nice -n 15 ionice -c 3 "$UPDATE_BIN" "$@"
          fi
          exec nice -n 15 ionice -c 3 "$UPDATE_BIN" "$@"
          ;;
        *)
          exec "$UPDATE_BIN" "$@"
          ;;
      esac
    '';
  };

  umRoot = ../apps/update-manager;
  managerSrc = lib.cleanSourceWith {
    src = umRoot;
    filter =
      path: _type:
      let
        base = baseNameOf path;
      in
      !(base == "target" || lib.hasSuffix ".pyc" base);
  };

  frayUpdateManagerBin = pkgs.rustPlatform.buildRustPackage {
    pname = "fray-update-manager";
    version = "1.0.0";
    src = managerSrc;
    cargoLock.lockFile = umRoot + /Cargo.lock;
    nativeBuildInputs = [ pkgs.pkg-config ];
    buildInputs = with pkgs; [
      gtk3
      glib
      cairo
      pango
      gdk-pixbuf
      atk
    ];
  };

  kdialogPkg =
    if pkgs.kdePackages ? kdialog then
      pkgs.kdePackages.kdialog
    else if pkgs ? kdialog then
      pkgs.kdialog
    else
      null;

  iconSvg = pkgs.writeText "fray-update-manager.svg" ''
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
      <rect width="256" height="256" rx="48" fill="#1a1a1a"/>
      <path fill="none" stroke="#c41e3a" stroke-width="16" stroke-linecap="round"
            d="M196 128a68 68 0 1 1-20-48"/>
      <path fill="#c41e3a" d="M176 58l34 34h-20v40h-28V92h-20z"/>
    </svg>
  '';

  frayUpdateManager = pkgs.stdenvNoCC.mkDerivation {
    pname = "fray-update-manager";
    version = "1.0";
    dontUnpack = true;
    nativeBuildInputs = with pkgs; [
      wrapGAppsHook3
      gobject-introspection
      makeWrapper
      librsvg
      gtk3
    ];
    buildInputs = with pkgs; [
      gtk3
      glib
      pango
      gdk-pixbuf
      atk
      adw-gtk3
    ];
    installPhase = ''
      runHook preInstall
      mkdir -p $out/bin $out/share/applications \
        $out/share/icons/hicolor/scalable/apps \
        $out/share/icons/hicolor/48x48/apps \
        $out/share/icons/hicolor/128x128/apps \
        $out/share/icons/hicolor/256x256/apps

      cp ${iconSvg} $out/share/icons/hicolor/scalable/apps/fray-update-manager.svg
      ${pkgs.librsvg}/bin/rsvg-convert -w 48 -h 48 \
        -o $out/share/icons/hicolor/48x48/apps/fray-update-manager.png ${iconSvg}
      ${pkgs.librsvg}/bin/rsvg-convert -w 128 -h 128 \
        -o $out/share/icons/hicolor/128x128/apps/fray-update-manager.png ${iconSvg}
      ${pkgs.librsvg}/bin/rsvg-convert -w 256 -h 256 \
        -o $out/share/icons/hicolor/256x256/apps/fray-update-manager.png ${iconSvg}

      iconPath="$out/share/icons/hicolor/256x256/apps/fray-update-manager.png"

      makeWrapper ${frayUpdateManagerBin}/bin/fray-update-manager $out/bin/fray-update-manager \
        --set FRAY_UM_STATE_DIR ${lib.escapeShellArg stateDir} \
        --set FRAY_UM_PREFS_FILE ${lib.escapeShellArg prefsFile} \
        --set FRAY_UM_ICON "$iconPath" \
        --prefix PATH : ${frayUpdatePowered}/bin \
        ${lib.optionalString (kdialogPkg != null) "--prefix PATH : ${kdialogPkg}/bin \\"}
        --prefix PATH : ${pkgs.zenity}/bin \
        --prefix PATH : /run/wrappers/bin \
        --prefix PATH : /run/current-system/sw/bin \
        --prefix XDG_DATA_DIRS : ${pkgs.adw-gtk3}/share \
        --prefix XDG_DATA_DIRS : /run/current-system/sw/share

      cat > $out/share/applications/fray-update-manager.desktop <<EOF
[Desktop Entry]
Type=Application
Name=Fray Update Manager
Name[fr]=Mises a jour Fray
Comment=Planifier et lancer les mises a jour Fray
Comment[fr]=Activer/desactiver l'auto-maj, planifier et choisir la puissance
Exec=fray-update-manager
Icon=$iconPath
Terminal=false
Categories=System;Settings;
Keywords=update;fray;nixos;upgrade;
StartupWMClass=fray-update-manager
EOF
      ${pkgs.gtk3}/bin/gtk-update-icon-cache -f -t $out/share/icons/hicolor 2>/dev/null || true
      runHook postInstall
    '';
    meta.mainProgram = "fray-update-manager";
  };

  # autoUpgrade GUI true + schedule off = timer boot/periodique via auto-update.nix
  effectiveAutoUpgrade = if guiCfg.schedule.enable then false else guiCfg.autoUpgrade;

  prefsDefault = ''
    {
      fray.services.updateManagerGui = {
        autoUpgrade = true;
        schedule = {
          enable = false;
          weekday = "Sat";
          hour = 16;
          minute = 0;
        };
        powerMode = "standard";
      };
    }
  '';
in
{
  imports = lib.optional (builtins.pathExists ./fray-update-manager-prefs.nix) ./fray-update-manager-prefs.nix;

  options.fray.services.updateManager = {
    enable = lib.mkEnableOption "fray-update CLI (update / --switch / --build / --boot)";
    package = lib.mkOption {
      type = lib.types.package;
      readOnly = true;
      default = frayUpdate;
      description = "Derivation fray-update (CLI unifiee)";
    };
    poweredPackage = lib.mkOption {
      type = lib.types.package;
      readOnly = true;
      default = frayUpdatePowered;
      description = "fray-update-powered (eco/standard)";
    };
    gui = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Installer la GUI Rust Fray Update Manager";
    };
  };

  options.fray.services.updateManagerGui = {
    autoUpgrade = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Mises a jour auto (timer Fray)";
    };
    schedule = {
      enable = lib.mkOption {
        type = lib.types.bool;
        default = false;
        description = "Planification hebdomadaire";
      };
      weekday = lib.mkOption {
        type = lib.types.str;
        default = "Sat";
        description = "Mon Tue Wed Thu Fri Sat Sun";
      };
      hour = lib.mkOption {
        type = lib.types.ints.between 0 23;
        default = 16;
      };
      minute = lib.mkOption {
        type = lib.types.ints.between 0 59;
        default = 0;
      };
    };
    powerMode = lib.mkOption {
      type = lib.types.str;
      default = "standard";
      apply = v: if v == "eco" then "eco" else "standard";
    };
  };

  config = lib.mkIf cfg.enable (
    lib.mkMerge [
      {
        assertions = [
          {
            assertion = weekdayOk;
            message = "fray.services.updateManagerGui.schedule.weekday doit etre Mon|Tue|Wed|Thu|Fri|Sat|Sun";
          }
        ];

        # Miroir option (sans definir le timer ici si false)
        fray.services.autoUpdate.enable = lib.mkDefault effectiveAutoUpgrade;

        environment.systemPackages = [
          frayUpdate
          frayUpdatePowered
        ]
        ++ lib.optionals cfg.gui [
          frayUpdateManager
          pkgs.zenity
        ]
        ++ lib.optionals (cfg.gui && kdialogPkg != null) [ kdialogPkg ];

        environment.variables.FRAY_FLAKE = lib.mkDefault defaultFlake;
        environment.variables.FRAY_HOST = lib.mkDefault defaultHost;

        systemd.tmpfiles.rules = [
          "d ${stateDir} 0775 root wheel -"
          "Z ${stateDir} 0775 root wheel -"
          "f ${stateDir}/power-mode 0664 root wheel - ${guiCfg.powerMode}"
          "z ${stateDir}/power-mode 0664 root wheel -"
        ];

        system.activationScripts.frayUpdateManagerPrefs = lib.stringAfter [ "etc" ] ''
          if [ ! -f ${prefsFile} ]; then
            mkdir -p "$(dirname ${prefsFile})"
            cat > ${prefsFile} <<'EOF'
${prefsDefault}EOF
            chmod 664 ${prefsFile} 2>/dev/null || true
          fi
        '';
      }

      # Timer auto (boot + periodique) - defini ici, pas dans auto-update.nix
      (lib.mkIf effectiveAutoUpgrade {
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
            ExecStart = "${frayUpdatePowered}/bin/fray-update-powered --notify";
          };
        };

        systemd.timers.fray-auto-update = {
          description = "Timer for fray-update (auto)";
          wantedBy = [ "timers.target" ];
          timerConfig = {
            OnBootSec = config.fray.services.autoUpdate.onBootSec;
            OnCalendar = config.fray.services.autoUpdate.onCalendar;
            Persistent = true;
            RandomizedDelaySec = "30m";
          };
        };
      })

      (lib.mkIf guiCfg.schedule.enable {
        systemd.services.fray-auto-update = {
          description = "Fray Flatpak + flake update (no host rebuild)";
          after = [ "network-online.target" ];
          wants = [ "network-online.target" ];
          serviceConfig = {
            Type = "oneshot";
            ExecStart = "${frayUpdatePowered}/bin/fray-update-powered --notify";
          };
        };
        systemd.timers."fray-auto-update-calendar" = {
          description = "Fray scheduled update (${calendar})";
          wantedBy = [ "timers.target" ];
          timerConfig = {
            OnCalendar = calendar;
            Persistent = true;
            Unit = "fray-auto-update.service";
          };
        };
      })
    ]
  );
}
