# ┌─────────────────────────────────────────────────────────────┐
# │ Fray — Gamescope (capSysNice=false, justification GLF)      │
# └─────────────────────────────────────────────────────────────┘
{
  config,
  lib,
  ...
}:

let
  cfg = config.fray.gaming.gamescope;
in
{
  options.fray.gaming.gamescope = {
    enable = lib.mkEnableOption "Fray Gamescope";
  };

  config = lib.mkIf cfg.enable {
    programs.gamescope = {
      enable = true;
      capSysNice = false;
    };
  };
}
