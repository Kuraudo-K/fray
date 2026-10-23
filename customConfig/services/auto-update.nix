# Options maj auto (timer reel dans update-manager.nix pour eviter recursion)
{
  lib,
  ...
}:

{
  options.fray.services.autoUpdate = {
    enable = lib.mkEnableOption "Automatic Flatpak + Fray flake update timer";
    onCalendar = lib.mkOption {
      type = lib.types.str;
      default = "*-*-* 00/12:00:00";
      description = "systemd OnCalendar for the auto-update timer";
    };
    onBootSec = lib.mkOption {
      type = lib.types.str;
      default = "5min";
      description = "Delay after boot before first auto-update";
    };
  };
}
