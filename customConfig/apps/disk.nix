# ┌─────────────────────────────────────────────────────────────┐
# │ Fray — outil disque simple (nixpkgs → flake.lock)           │
# └─────────────────────────────────────────────────────────────┘
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.apps.disk;
in
{
  options.fray.apps.disk = {
    enable = lib.mkEnableOption "Fray disk utility (GNOME Disks)";
  };

  config = lib.mkIf cfg.enable {
    services.udisks2.enable = true;
    environment.systemPackages = with pkgs; [
      gnome-disk-utility
      udisks
    ];
  };
}
