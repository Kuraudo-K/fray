# ┌─────────────────────────────────────────────────────────────┐
# │ Fray — Faugus (overlay GLF → flake.lock)                    │
# │ Adapté de GLF launchers.nix                                 │
# └─────────────────────────────────────────────────────────────┘
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.gaming.faugus;
  has = pkgs ? faugus-launcher;
in
{
  options.fray.gaming.faugus = {
    enable = lib.mkEnableOption "Fray Faugus Launcher";
  };

  config = lib.mkIf cfg.enable {
    assertions = [
      {
        assertion = has;
        message = "fray.gaming.faugus : overlay faugus-launcher requis (input flake)";
      }
    ];
    environment.systemPackages = lib.optional has pkgs.faugus-launcher;
  };
}
