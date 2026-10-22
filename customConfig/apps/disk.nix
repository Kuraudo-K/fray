# fray-disk - viewer disques Rust hexagonal + GUI GTK
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.apps.disk;
  src = ./disk;

  rustSrc = lib.cleanSourceWith {
    src = src;
    filter =
      path: _type:
      let
        base = baseNameOf path;
      in
      !(base == "target" || base == "gui.py" || lib.hasSuffix ".pyc" base);
  };

  fray-disk = pkgs.rustPlatform.buildRustPackage {
    pname = "fray-disk";
    version = "0.1.0";
    src = rustSrc;
    cargoLock.lockFile = src + /Cargo.lock;
    nativeBuildInputs = [ pkgs.makeWrapper ];
    postInstall = ''
      wrapProgram $out/bin/fray-disk \
        --prefix PATH : ${
          lib.makeBinPath [
            pkgs.util-linux
            pkgs.udisks
            pkgs.gnome-disk-utility
          ]
        }
    '';
    meta = {
      description = "Simple disk/partition viewer (hexagonal)";
      mainProgram = "fray-disk";
    };
  };

  pythonEnv = pkgs.python3.withPackages (ps: [ ps.pygobject3 ]);

  fray-disk-gui = pkgs.stdenv.mkDerivation {
    pname = "fray-disk-gui";
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
      mkdir -p $out/bin $out/share/fray-disk $out/share/applications
      install -m 644 ${src}/gui.py $out/share/fray-disk/gui.py
      makeWrapper ${pythonEnv}/bin/python3 $out/bin/fray-disk-gui \
        --add-flags "$out/share/fray-disk/gui.py" \
        --set FRAY_DISK_BIN ${fray-disk}/bin/fray-disk \
        --set-default FRAY_ICON /run/current-system/sw/share/icons/hicolor/256x256/apps/fray-disk.png \
        --prefix PATH : ${lib.makeBinPath [ fray-disk pkgs.udisks pkgs.util-linux ]}
      cat > $out/share/applications/fray-disk.desktop <<'DESKTOP'
[Desktop Entry]
Name=Fray Disk
Comment=Disques, montages et génération Nix
Exec=fray-disk-gui
Icon=fray-disk
Terminal=false
Type=Application
Categories=System;Filesystem;
Keywords=fray;disk;mount;nix;
StartupWMClass=fray-disk
DESKTOP
      runHook postInstall
    '';
  };
in
{
  options.fray.apps.disk = {
    enable = lib.mkEnableOption "fray-disk (Rust) plus GNOME Disks / udisks2";
  };

  config = lib.mkIf cfg.enable {
    services.udisks2.enable = true;

    environment.systemPackages = [
      fray-disk
      fray-disk-gui
      pkgs.gnome-disk-utility
      pkgs.udisks
      pkgs.util-linux
    ];

    environment.shellAliases = {
      nix-disk = "fray-disk";
    };
  };
}
