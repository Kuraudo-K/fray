# Switcher de bureau (Rust + GUI GTK) - GNOME / Niri / Plasma / Mango
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
    version = "0.1.0";
    src = rustSrc;
    cargoLock.lockFile = src + /Cargo.lock;
    meta = {
      description = "Desktop switcher with per-DE config persistence";
      mainProgram = "fray-de-switch";
    };
  };

  pythonEnv = pkgs.python3.withPackages (ps: [ ps.pygobject3 ]);

  fray-de-switch-gui = pkgs.stdenv.mkDerivation {
    pname = "fray-de-switch-gui";
    version = "0.1.0";
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
        --set-default FRAY_ICON /run/current-system/sw/share/pixmaps/fray.png \
        --prefix PATH : ${lib.makeBinPath [ fray-de-switch pkgs.systemd ]}
      cat > $out/share/applications/fray-de-switch.desktop <<'DESKTOP'
[Desktop Entry]
Name=Fray Switch
Comment=Basculer GNOME / Niri / Plasma / Mango (profils persistants)
Exec=fray-de-switch-gui
Icon=fray
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
    ];
  };
}
