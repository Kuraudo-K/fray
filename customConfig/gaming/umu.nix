# umu-launcher - lanceur unifié (Steam Linux Runtime) pour jeux Windows
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.gaming.umu;
in
{
  options.fray.gaming.umu = {
    enable = lib.mkEnableOption "umu-launcher for Windows games via Steam Runtime";
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [ pkgs.umu-launcher ];
  };
}
