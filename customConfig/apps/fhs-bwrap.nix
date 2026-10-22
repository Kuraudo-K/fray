# Helpers FHS / bubblewrap pour jeux (compat, pas une sandbox sécu)
# Socle commun : Steam, Heroic, Faugus (+ umu si activé)
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.apps.fhsBwrap;
  umuOn = config.fray.gaming.umu.enable or false;
  heroicOn = config.fray.gaming.heroic.enable or false;
  faugusOn = config.fray.gaming.faugus.enable or false;

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
      ++ lib.optional umuOn umu-launcher
      ++ lib.optional heroicOn heroic
      ++ lib.optional (faugusOn && (p ? faugus-launcher)) faugus-launcher;
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
    enable = lib.mkEnableOption "FHS/bwrap env shared by Steam, Heroic, Faugus and umu";
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [
      pkgs.steam-run
      frayGameFhs
      pkgs.bubblewrap
    ];
  };
}
