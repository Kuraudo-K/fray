# ┌─────────────────────────────────────────────────────────────┐
# │ Fray — OBS + plugins (GLF streaming/obs.nix)                │
# └─────────────────────────────────────────────────────────────┘
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.apps.obs;
in
{
  options.fray.apps.obs = {
    enable = lib.mkEnableOption "Fray OBS Studio";
  };

  config = lib.mkIf cfg.enable {
    programs.obs-studio = {
      enable = true;
      plugins = with pkgs.obs-studio-plugins; [
        obs-vkcapture
        obs-pipewire-audio-capture
        obs-vaapi
        obs-move-transition
        obs-composite-blur
      ];
    };
  };
}
