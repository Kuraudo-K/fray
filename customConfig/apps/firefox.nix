# Firefox
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.apps.firefox;
in
{
  options.fray.apps.firefox = {
    enable = lib.mkEnableOption "Firefox web browser";
  };

  config = lib.mkIf cfg.enable {
    programs.firefox.enable = true;
    environment.systemPackages = [ pkgs.firefox ];
  };
}
