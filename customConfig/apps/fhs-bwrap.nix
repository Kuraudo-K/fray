# Helpers FHS / bubblewrap pour jeux (compat, pas une sandbox sécu)
# Inclut steam-run, umu si activé, libs Vulkan/audio courantes
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.apps.fhsBwrap;
  umuOn = config.fray.gaming.umu.enable or false;

  frayGameFhs = pkgs.buildFHSEnv {
    name = "fray-game-fhs";
    targetPkgs =
      p:
      with p;
      [
        steam-run
        bubblewrap
        vulkan-loader
        libglvnd
        alsa-lib
        pipewire
        gamemode
      ]
      ++ lib.optional umuOn umu-launcher;
    multiPkgs =
      p: with p; [
        vulkan-loader
        libglvnd
        gamemode
      ];
    runScript = "bash";
  };
in
{
  options.fray.apps.fhsBwrap = {
    enable = lib.mkEnableOption "steam-run, bubblewrap, and a small FHS env for games";
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [
      pkgs.steam-run
      frayGameFhs
      pkgs.bubblewrap
    ];
  };
}
