# nh — helper rebuild flake (chemin Fray, pas /etc/nixos GLF)
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
      description = "Shell aliases fray-switch / fray-build / fray-boot";
    };
  };

  config = lib.mkIf cfg.enable (
    let
      aliases = {
        fray-switch = "nh os switch ${lib.escapeShellArg cfg.flake} -H ${cfg.hostname}";
        fray-build = "nh os build ${lib.escapeShellArg cfg.flake} -H ${cfg.hostname}";
        fray-boot = "nh os boot ${lib.escapeShellArg cfg.flake} -H ${cfg.hostname}";
      };
    in
    {
      programs.nh = {
        enable = true;
        flake = cfg.flake;
      };

      environment.variables.NH_FLAKE = lib.mkDefault cfg.flake;

      # bash/zsh
      environment.shellAliases = lib.mkIf cfg.aliases aliases;
      # fish (shell user Fray)
      programs.fish.shellAliases = lib.mkIf cfg.aliases aliases;
    }
  );
}
