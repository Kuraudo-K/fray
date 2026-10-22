# nh — helper rebuild flake (chemin Fray, pas /etc/nixos GLF)
# Alias courts → fray-update --… (CLI unifiée)
{
  config,
  lib,
  ...
}:

let
  cfg = config.fray.system.nh;
in
{
  options.fray.system.nh = {
    enable = lib.mkEnableOption "nh helper pointed at the Fray flake";
    flake = lib.mkOption {
      type = lib.types.str;
      default = "/home/kouro/Téléchargements/GLF pc/NIX/fray";
      description = "Absolute path to the Fray flake (never /etc/nixos)";
    };
    hostname = lib.mkOption {
      type = lib.types.str;
      default = "fray-vm";
      description = "nixosConfigurations attr for nh -H (fray-vm | fray-iso)";
    };
    aliases = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Compat aliases → fray-update --switch|--build|--boot";
    };
  };

  config = lib.mkIf cfg.enable (
    let
      # Compat courte ; préférer fray-update --switch
      aliases = {
        fray-switch = "fray-update --switch";
        fray-build = "fray-update --build";
        fray-boot = "fray-update --boot";
      };
    in
    {
      programs.nh = {
        enable = true;
        flake = cfg.flake;
      };

      environment.variables.NH_FLAKE = lib.mkDefault cfg.flake;
      environment.variables.FRAY_FLAKE = lib.mkDefault cfg.flake;
      environment.variables.FRAY_HOST = lib.mkDefault cfg.hostname;

      environment.shellAliases = lib.mkIf cfg.aliases aliases;
      programs.fish.shellAliases = lib.mkIf cfg.aliases aliases;
    }
  );
}
