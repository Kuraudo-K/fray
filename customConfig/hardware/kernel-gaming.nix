# Noyau + sysctl + priorités processus (gaming)
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.hardware.kernelGaming;
in
{
  options.fray.hardware.kernelGaming = {
    enable = lib.mkEnableOption "Gaming kernel tweaks (sysctl, ntsync, ananicy)";
    useLatest = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Use the latest kernel package set";
    };
    enableScx = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Start the scx_bpfland CPU scheduler at boot (off by default)";
    };
  };

  config = lib.mkIf cfg.enable {
    boot.kernelPackages = lib.mkIf cfg.useLatest pkgs.linuxPackages_latest;
    boot.supportedFilesystems.zfs = lib.mkForce false;

    boot.kernelParams = [ "preempt=full" ];

    # Meilleure sync Wine/Proton / Better Wine/Proton sync
    boot.kernelModules = [ "ntsync" ];

    boot.kernel.sysctl = {
      # Jeux mal alignés : ne pas les ralentir volontairement
      # Misaligned games: do not intentionally slow them down
      "kernel.split_lock_mitigate" = 0;
      "vm.swappiness" = 60;
      "vm.vfs_cache_pressure" = 50;
      "vm.dirty_bytes" = 268435456;
      "vm.dirty_background_bytes" = 67108864;
      "vm.dirty_writeback_centisecs" = 1500;
      "vm.page-cluster" = 0;
      "vm.max_map_count" = 16777216;
      "kernel.nmi_watchdog" = 0;
      "fs.file-max" = 2097152;
    };

    services.ananicy = {
      enable = true;
      package = pkgs.ananicy-cpp;
      rulesProvider = pkgs.ananicy-rules-cachyos;
    };

    services.scx = lib.mkIf cfg.enableScx {
      enable = true;
      scheduler = "scx_bpfland";
    };
  };
}
