# fray-disk - viewer disques Rust hexagonal (+ GNOME Disks / Partition Manager)
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.apps.disk;
  src = ./disk;

  fray-disk = pkgs.rustPlatform.buildRustPackage {
    pname = "fray-disk";
    version = "0.1.0";
    src = lib.cleanSource src;
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

  desktopItem = pkgs.makeDesktopItem {
    name = "fray-disk";
    desktopName = "Fray Disk";
    comment = "Lister disques et ouvrir l'outil DE";
    exec = "fray-disk list";
    terminal = true;
    categories = [
      "System"
      "Filesystem"
    ];
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
      desktopItem
      pkgs.gnome-disk-utility
      pkgs.udisks
      pkgs.util-linux
    ];

    environment.shellAliases = {
      # compat éventuelle avec un ancien wrapper
      nix-disk = "fray-disk";
    };
  };
}
