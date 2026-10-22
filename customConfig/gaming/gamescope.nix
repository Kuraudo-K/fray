# Gamescope
{
  config,
  lib,
  ...
}:

let
  cfg = config.fray.gaming.gamescope;
in
{
  options.fray.gaming.gamescope = {
    enable = lib.mkEnableOption "Gamescope compositor for games";
  };

  config = lib.mkIf cfg.enable {
    programs.gamescope = {
      enable = true;
      # false : évite bwrap setuid / pressure-vessel
      # false: avoid setuid bwrap / pressure-vessel issues
      capSysNice = false;
    };
  };
}
