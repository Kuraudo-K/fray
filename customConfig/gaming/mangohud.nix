# ┌─────────────────────────────────────────────────────────────┐
# │ Fray — MangoHud (paquet ; pas programs.mangohud partout)    │
# └─────────────────────────────────────────────────────────────┘
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
    enable = lib.mkEnableOption "Fray MangoHud";
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = with pkgs; [
      mangohud
      goverlay
    ];
  };
}
