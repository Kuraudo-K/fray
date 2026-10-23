# Switcher de bureau (Rust + GUI GTK) - GNOME / Plasma
# Persistance greeter : AccountsService via fray-set-session (pas seulement ~/.dmrc)
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.desktop.deSwitch;

  src = ./../apps/de-switch;

  rustSrc = lib.cleanSourceWith {
    src = src;
    filter =
      path: _type:
      let
        base = baseNameOf path;
      in
      !(base == "target" || base == "gui.py" || lib.hasSuffix ".pyc" base);
  };

  fray-de-switch = pkgs.rustPlatform.buildRustPackage {
    pname = "fray-de-switch";
    version = "0.2.0";
    src = rustSrc;
    cargoLock.lockFile = src + /Cargo.lock;
    nativeBuildInputs = [ pkgs.makeWrapper ];
    postInstall = ''
      wrapProgram $out/bin/fray-de-switch \
        --set FRAY_SET_SESSION_BIN ${fray-set-session}/bin/fray-set-session \
        --set FRAY_SUDO_BIN /run/wrappers/bin/sudo \
        --prefix PATH : /run/wrappers/bin:${lib.makeBinPath [ fray-set-session ]}
    '';
    meta = {
      description = "Desktop switcher with per-DE config persistence";
      mainProgram = "fray-de-switch";
    };
  };

  # Ecrit Session= pour GDM via fichier + D-Bus AccountsService (sudo -n).
  # Le fichier seul ne suffit pas si accounts-daemon a deja la valeur en memoire.
  fray-set-session = pkgs.writeShellScriptBin "fray-set-session" ''
    set -uo pipefail
    session="''${1:-}"
    user="''${2:-}"
    # Anciens niri/mango → gnome (DE retires)
    case "$session" in
      niri|mango|dms) session=gnome ;;
    esac
    case "$session" in
      gnome|plasma) ;;
      *)
        echo "usage: fray-set-session <gnome|plasma> [user]" >&2
        exit 2
        ;;
    esac
    if [ -z "$user" ]; then
      if [ -n "''${SUDO_USER:-}" ]; then
        user="$SUDO_USER"
      else
        user="$(id -un)"
      fi
    fi
    as_dir=/var/lib/AccountsService/users
    as_file="$as_dir/$user"
    mkdir -p "$as_dir"
    if [ -f "$as_file" ]; then
      tmp="$(mktemp)"
      ${pkgs.gawk}/bin/awk -v s="$session" '
        BEGIN { sess=0; xsess=0; stype=0 }
        /^Session=/ { print "Session=" s; sess=1; next }
        /^XSession=/ { print "XSession=" s; xsess=1; next }
        /^SessionType=/ { print "SessionType=wayland"; stype=1; next }
        { print }
        END {
          if (!sess) print "Session=" s
          if (!xsess) print "XSession=" s
          if (!stype) print "SessionType=wayland"
        }
      ' "$as_file" > "$tmp"
      mv "$tmp" "$as_file"
    else
      printf '%s\n' '[User]' "Session=$session" "XSession=$session" "SessionType=wayland" "SystemAccount=false" > "$as_file"
    fi
    chmod 644 "$as_file" || true
    # Copie durable : GNOME reecrit Session= avec le DE courant a la deconnexion.
    mkdir -p /var/lib/fray/preferred-session
    printf '%s\n' "$session" > "/var/lib/fray/preferred-session/$user"
    chmod 644 "/var/lib/fray/preferred-session/$user" || true
    # Prefetch GDM cache if present
    if [ -d /var/lib/gdm ]; then
      rm -f "/var/lib/gdm/.cache/accountsservice/users/$user" 2>/dev/null || true
    fi
    # D-Bus : ce que GDM lit vraiment au login (pas seulement le fichier).
    uid="$(id -u "$user" 2>/dev/null || true)"
    if [ -n "''${uid:-}" ] && command -v ${pkgs.glib}/bin/gdbus >/dev/null 2>&1; then
      path="$(
        ${pkgs.glib}/bin/gdbus call --system \
          --dest org.freedesktop.Accounts \
          --object-path /org/freedesktop/Accounts \
          --method org.freedesktop.Accounts.FindUserById "int64:$uid" \
          2>/dev/null | ${pkgs.gnused}/bin/sed -n "s/.*'\\([^']*\\)'.*/\\1/p" | head -1
      )" || path=""
      if [ -n "''${path:-}" ]; then
        ${pkgs.glib}/bin/gdbus call --system --dest org.freedesktop.Accounts \
          --object-path "$path" --method org.freedesktop.Accounts.User.SetSession "$session" >/dev/null 2>&1 || true
        ${pkgs.glib}/bin/gdbus call --system --dest org.freedesktop.Accounts \
          --object-path "$path" --method org.freedesktop.Accounts.User.SetXSession "$session" >/dev/null 2>&1 || true
        ${pkgs.glib}/bin/gdbus call --system --dest org.freedesktop.Accounts \
          --object-path "$path" --method org.freedesktop.Accounts.User.SetSessionType wayland >/dev/null 2>&1 || true
      fi
    fi
    echo "[fray-set-session] $user -> $session ($as_file)"
    exit 0
  '';

  fray-restore-session = pkgs.writeShellScriptBin "fray-restore-session" ''
    set -euo pipefail
    root=/var/lib/fray/preferred-session
    [ -d "$root" ] || exit 0
    for f in "$root"/*; do
      [ -f "$f" ] || continue
      user="$(basename "$f")"
      session="$(tr -d '[:space:]' < "$f")"
      case "$session" in
        gnome|plasma|niri|mango|dms)
          ${fray-set-session}/bin/fray-set-session "$session" "$user" || true
          ;;
      esac
    done
  '';

  pythonEnv = pkgs.python3.withPackages (ps: [ ps.pygobject3 ]);

  fray-de-switch-gui = pkgs.stdenv.mkDerivation {
    pname = "fray-de-switch-gui";
    version = "0.2.0";
    dontUnpack = true;
    nativeBuildInputs = with pkgs; [
      wrapGAppsHook3
      gobject-introspection
      makeWrapper
    ];
    buildInputs = with pkgs; [
      gtk3
      glib
      pango
      gdk-pixbuf
      atk
      pythonEnv
    ];
    installPhase = ''
      runHook preInstall
      mkdir -p $out/bin $out/share/fray-de-switch $out/share/applications
      install -m 644 ${src}/gui.py $out/share/fray-de-switch/gui.py
      makeWrapper ${pythonEnv}/bin/python3 $out/bin/fray-de-switch-gui \
        --add-flags "$out/share/fray-de-switch/gui.py" \
        --set FRAY_DE_SWITCH_BIN ${fray-de-switch}/bin/fray-de-switch \
        --set FRAY_SET_SESSION_BIN ${fray-set-session}/bin/fray-set-session \
        --set FRAY_SUDO_BIN /run/wrappers/bin/sudo \
        --set-default FRAY_ICON /run/current-system/sw/share/icons/hicolor/256x256/apps/fray-de-switch.png \
        --prefix PATH : ${
          lib.makeBinPath [
            fray-de-switch
            fray-set-session
            pkgs.systemd
          ]
        }
      cat > $out/share/applications/fray-de-switch.desktop <<'DESKTOP'
[Desktop Entry]
Name=Fray Switch
Comment=Basculer GNOME / Plasma (profils persistants)
Exec=fray-de-switch-gui
Icon=fray-de-switch
Terminal=false
Type=Application
Categories=Settings;System;
Keywords=fray;de;switch;desktop;
StartupWMClass=fray-de-switch
DESKTOP
      runHook postInstall
    '';
  };
in
{
  options.fray.desktop.deSwitch = {
    enable = lib.mkEnableOption "Rust desktop switcher with per-DE config profiles";
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [
      fray-de-switch
      fray-de-switch-gui
      fray-set-session
      fray-restore-session
    ];

    # CRITIQUE : ne PAS poser defaultSession.
    # NixOS injecte alors `set-session <de>` dans display-manager PreStart, ce qui
    # ecrase AccountsService a chaque boot (ignore l'historique / Fray Switch).
    # mkForce null : annule aussi le defaultSession=plasma de plasma6.
    services.displayManager.defaultSession = lib.mkForce null;

    # Restaure Session= avant GDM, et encore dans PreStart (apres set-session si present).
    systemd.services.fray-restore-session = {
      description = "Restore Fray preferred greeter session (pre-GDM)";
      wantedBy = [ "display-manager.service" ];
      before = [ "display-manager.service" ];
      after = [ "local-fs.target" "accounts-daemon.service" ];
      serviceConfig = {
        Type = "oneshot";
        ExecStart = "${fray-restore-session}/bin/fray-restore-session";
        RemainAfterExit = true;
      };
    };
    systemd.services.display-manager = {
      serviceConfig.ExecStartPre = lib.mkAfter [
        "${fray-restore-session}/bin/fray-restore-session"
      ];
    };
    systemd.services.fray-restore-session-post = {
      description = "Restore Fray preferred greeter session (post-GDM)";
      wantedBy = [ "graphical.target" ];
      after = [
        "display-manager.service"
        "accounts-daemon.service"
        "fray-restore-session.service"
      ];
      serviceConfig = {
        Type = "oneshot";
        ExecStart = "${fray-restore-session}/bin/fray-restore-session";
        RemainAfterExit = true;
      };
    };

    # Apres logout, GNOME reecrit Session=gnome dans AccountsService.
    # Des qu'un fichier users/ change, on reapplique preferred-session.
    systemd.paths.fray-session-guard = {
      description = "Watch AccountsService for Fray session restore";
      wantedBy = [ "multi-user.target" ];
      pathConfig = {
        PathModified = "/var/lib/AccountsService/users";
        Unit = "fray-session-guard.service";
      };
    };
    systemd.services.fray-session-guard = {
      description = "Re-apply Fray preferred session after AccountsService change";
      after = [ "accounts-daemon.service" ];
      serviceConfig = {
        Type = "oneshot";
        ExecStart = "${fray-restore-session}/bin/fray-restore-session";
      };
    };

    # wheel+users : la regle %wheel ALL (mot de passe) ne doit pas gagner
    # sur le helper. NOPASSWD explicite + !authenticate via extraConfig.
    security.sudo.extraRules = [
      {
        groups = [
          "wheel"
          "users"
        ];
        commands = [
          {
            command = "${fray-set-session}/bin/fray-set-session";
            options = [
              "NOPASSWD"
              "SETENV"
            ];
          }
          {
            command = "/run/current-system/sw/bin/fray-set-session";
            options = [
              "NOPASSWD"
              "SETENV"
            ];
          }
        ];
      }
    ];
    security.sudo.extraConfig = ''
      Defaults!${fray-set-session}/bin/fray-set-session !authenticate
      Defaults!/run/current-system/sw/bin/fray-set-session !authenticate
    '';
  };
}
