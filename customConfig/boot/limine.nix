# Bootloader Limine (ISO / install réelle - pas utilisé par QEMU build-vm)
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.boot.limine;
in
{
  options.fray.boot.limine = {
    enable = lib.mkEnableOption "Limine UEFI bootloader (for ISO/real installs, not QEMU VMs)";
    secureBoot = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Sign Limine with sbctl at each rebuild (keys must already be enrolled)";
    };
    maxGenerations = lib.mkOption {
      type = lib.types.int;
      default = 10;
      description = "How many NixOS generations to show in the Limine menu";
    };
  };

  config = lib.mkIf cfg.enable {
    boot.loader.systemd-boot.enable = lib.mkForce false;
    boot.loader.grub.enable = lib.mkForce false;

    boot.loader.limine = {
      enable = true;
      maxGenerations = cfg.maxGenerations;
      secureBoot.enable = cfg.secureBoot;
    };

    environment.systemPackages = lib.optional cfg.secureBoot pkgs.sbctl;
  };
}
