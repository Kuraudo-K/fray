# ┌─────────────────────────────────────────────────────────────┐
# │ Fray — Heroic (nixpkgs → flake.lock)                        │
# └─────────────────────────────────────────────────────────────┘
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.gaming.heroic;
in
{
  options.fray.gaming.heroic = {
    enable = lib.mkEnableOption "Fray Heroic";
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [ pkgs.heroic ];
  };
}
