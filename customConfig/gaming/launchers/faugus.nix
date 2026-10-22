# Faugus Launcher (overlay flake — absent de nixpkgs)
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
    enable = lib.mkEnableOption "Faugus game launcher";
  };

  config = lib.mkIf cfg.enable {
    assertions = [
      {
        assertion = has;
        message = "fray.gaming.faugus : pkgs.faugus-launcher manquant (overlay flake requis)";
      }
    ];
    environment.systemPackages = lib.optional has pkgs.faugus-launcher;
  };
}
