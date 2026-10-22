# Heroic Games Launcher
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.gaming.heroic;
in
{
  options.fray.gaming.heroic = {
    enable = lib.mkEnableOption "Heroic Games Launcher";
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [ pkgs.heroic ];
  };
}
