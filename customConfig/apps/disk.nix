# Outil disque (GNOME Disks)
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
    enable = lib.mkEnableOption "GNOME Disks and udisks2";
  };

  config = lib.mkIf cfg.enable {
    services.udisks2.enable = true;
    environment.systemPackages = with pkgs; [
      gnome-disk-utility
      udisks
    ];
  };
}
