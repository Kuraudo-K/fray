# MangoHud (+ GOverlay)
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.gaming.mangohud;
in
{
  options.fray.gaming.mangohud = {
    enable = lib.mkEnableOption "MangoHud performance overlay";
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = with pkgs; [
      mangohud
      goverlay
    ];
  };
}
