# MangoHud + GOverlay + vkBasalt
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
    vkbasalt = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Install vkBasalt (used by GOverlay)";
    };
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages =
      with pkgs;
      [
        mangohud
        goverlay
      ]
      ++ lib.optional cfg.vkbasalt vkbasalt;
  };
}
