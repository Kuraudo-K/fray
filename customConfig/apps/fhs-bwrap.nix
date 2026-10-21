# ┌─────────────────────────────────────────────────────────────┐
# │ Fray — FHS + bubblewrap (compat jeux, pas sandbox sécu)     │
# └─────────────────────────────────────────────────────────────┘
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.apps.fhsBwrap;

  frayGameFhs = pkgs.buildFHSEnv {
    name = "fray-game-fhs";
    targetPkgs =
      p: with p; [
        steam-run
        vulkan-loader
        libglvnd
        alsa-lib
        pipewire
      ];
    multiPkgs =
      p: with p; [
        vulkan-loader
        libglvnd
      ];
    runScript = "bash";
  };
in
{
  options.fray.apps.fhsBwrap = {
    enable = lib.mkEnableOption "Fray FHS/bwrap helpers";
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [
      pkgs.steam-run
      frayGameFhs
      pkgs.bubblewrap
    ];
  };
}
