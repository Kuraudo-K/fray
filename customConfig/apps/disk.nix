# fray-disk : GUI GTK4/libadwaita (ref nix-disk GLF) + CLI hexagonal optionnel
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.apps.disk;

  fray-disk = pkgs.callPackage ./disk/gtk { };

  cliSrc = ./disk/cli;
  rustCliSrc = lib.cleanSourceWith {
    src = cliSrc;
    filter =
      path: _type:
      let
        base = baseNameOf path;
      in
      !(base == "target" || base == "gui.py" || lib.hasSuffix ".pyc" base);
  };

  fray-disk-cli = pkgs.rustPlatform.buildRustPackage {
    pname = "fray-disk-cli";
    version = "0.1.0";
    src = rustCliSrc;
    cargoLock.lockFile = cliSrc + /Cargo.lock;
    nativeBuildInputs = [ pkgs.makeWrapper ];
    postInstall = ''
      mv $out/bin/fray-disk $out/bin/fray-disk-cli
      wrapProgram $out/bin/fray-disk-cli \
        --prefix PATH : ${
          lib.makeBinPath [
            pkgs.util-linux
            pkgs.udisks
            pkgs.gnome-disk-utility
          ]
        }
    '';
    meta = {
      description = "Fray disk CLI (list/mount/gen-nix)";
      mainProgram = "fray-disk-cli";
    };
  };
in
{
  options.fray.apps.disk = {
    enable = lib.mkEnableOption "Fray Disk (GTK4, ref nix-disk) + CLI";
  };

  config = lib.mkIf cfg.enable {
    services.udisks2.enable = true;

    environment.systemPackages = [
      fray-disk
      fray-disk-cli
      pkgs.gnome-disk-utility
      pkgs.udisks
      pkgs.util-linux
      pkgs.parted
      pkgs.e2fsprogs
    ];

    environment.shellAliases = {
      nix-disk = "fray-disk";
    };
  };
}
