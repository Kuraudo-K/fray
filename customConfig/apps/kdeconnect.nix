# KDE Connect (Plasma / GNOME) — import commenté dans default.nix
{
  config,
  lib,
  ...
}:

let
  cfg = config.fray.apps.kdeconnect;
in
{
  options.fray.apps.kdeconnect = {
    enable = lib.mkEnableOption "KDE Connect phone pairing";
  };

  config = lib.mkIf cfg.enable {
    programs.kdeconnect.enable = true;
  };
}
