# Switcher de bureau (Rust + GUI GTK) - GNOME / Niri / Plasma / Mango
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
    version = "0.1.1";
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

  # Ecrit Session=/XSession= pour GDM (AccountsService). Appelé en sudo -n.
  fray-set-session = pkgs.writeShellScriptBin "fray-set-session" ''
    set -euo pipefail
    session="''${1:-}"
    user="''${2:-}"
    case "$session" in
      gnome|niri|plasma|mango) ;;
      *)
        echo "usage: fray-set-session <gnome|niri|plasma|mango> [user]" >&2
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
        BEGIN { sess=0; xsess=0 }
        /^Session=/ { print "Session=" s; sess=1; next }
        /^XSession=/ { print "XSession=" s; xsess=1; next }
        { print }
        END {
          if (!sess) print "Session=" s
          if (!xsess) print "XSession=" s
        }
      ' "$as_file" > "$tmp"
      mv "$tmp" "$as_file"
    else
      printf '%s\n' '[User]' "Session=$session" "XSession=$session" "SystemAccount=false" > "$as_file"
    fi
    chmod 644 "$as_file"
    # Copie durable : GNOME reecrit Session= avec le DE courant a la deconnexion.
    mkdir -p /var/lib/fray/preferred-session
    printf '%s\n' "$session" > "/var/lib/fray/preferred-session/$user"
    chmod 644 "/var/lib/fray/preferred-session/$user"
    # Prefetch GDM cache if present
    if [ -d /var/lib/gdm ]; then
      rm -f "/var/lib/gdm/.cache/accountsservice/users/$user" 2>/dev/null || true
    fi
    echo "[fray-set-session] $user -> $session ($as_file)"
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
        gnome|niri|plasma|mango)
          ${fray-set-session}/bin/fray-set-session "$session" "$user" || true
          ;;
      esac
    done
  '';

  pythonEnv = pkgs.python3.withPackages (ps: [ ps.pygobject3 ]);

  fray-de-switch-gui = pkgs.stdenv.mkDerivation {
    pname = "fray-de-switch-gui";
    version = "0.1.1";
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
Comment=Basculer GNOME / Niri / Plasma / Mango (profils persistants)
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

    # Defaut greeter initial (AccountsService ecrase apres fray-de-switch).
    # mkForce : plasma6 pose aussi defaultSession = plasma.
    services.displayManager.defaultSession = lib.mkForce "gnome";

    # Restaure Session= juste avant GDM (survit a la reecriture logout GNOME).
    systemd.services.fray-restore-session = {
      description = "Restore Fray preferred greeter session";
      wantedBy = [ "display-manager.service" ];
      before = [ "display-manager.service" ];
      after = [ "local-fs.target" "accounts-daemon.service" ];
      serviceConfig = {
        Type = "oneshot";
        ExecStart = "${fray-restore-session}/bin/fray-restore-session";
        RemainAfterExit = true;
      };
    };

    # Chemin store + symlink profil (sudo match sur chemin resolu ou invoque)
    security.sudo.extraRules = [
      {
        groups = [ "users" ];
        commands = [
          {
            command = "${fray-set-session}/bin/fray-set-session";
            options = [ "NOPASSWD" ];
          }
          {
            command = "/run/current-system/sw/bin/fray-set-session";
            options = [ "NOPASSWD" ];
          }
        ];
      }
    ];
  };
}
