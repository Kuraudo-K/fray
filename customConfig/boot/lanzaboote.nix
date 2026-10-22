# Secure Boot via lanzaboote (optionnel — clés dans /var/lib/sbctl)
# Off par défaut. Ne jamais enroll-keys depuis Fray.
# Module flake importé dans flake.nix (inputs.lanzaboote).
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.boot.lanzaboote;
in
{
  options.fray.boot.lanzaboote = {
    enable = lib.mkEnableOption "Lanzaboote Secure Boot (keys in pkiBundle; off by default)";
    pkiBundle = lib.mkOption {
      type = lib.types.str;
      default = "/var/lib/sbctl";
      description = "sbctl PKI bundle path (import keys; do not enroll from Fray)";
    };
  };

  config = lib.mkIf cfg.enable {
    assertions = [
      {
        assertion = !(config.fray.boot.limine.enable or false);
        message = "fray.boot.lanzaboote and fray.boot.limine cannot both be enabled";
      }
    ];

    environment.systemPackages = [ pkgs.sbctl ];

    boot.loader.systemd-boot.enable = lib.mkForce false;
    boot.loader.grub.enable = lib.mkForce false;

    boot.lanzaboote = {
      enable = true;
      pkiBundle = cfg.pkiBundle;
    };
  };
}
