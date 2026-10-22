# Terminal commun aux 3 DE — kitty (GPU, très customisable)
# GNOME/Plasma gardent aussi leurs terminaux natifs ; niri l’utilise déjà
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.apps.terminal;
in
{
  options.fray.apps.terminal = {
    enable = lib.mkEnableOption "Shared kitty terminal for all desktops";
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [ pkgs.kitty ];
  };
}
