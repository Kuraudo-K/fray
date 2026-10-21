# ┌─────────────────────────────────────────────────────────────┐
# │ Fray — noyau + sysctl + scheduler gaming                    │
# │ GLF boot.nix + Nixerion perf-gaming + Bazzite split_lock    │
# │ CachyOS : ananicy-cpp + rules                               │
# └─────────────────────────────────────────────────────────────┘
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
    enable = lib.mkEnableOption "Fray gaming kernel tweaks";
    useLatest = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "linuxPackages_latest / latest kernel set";
    };
    # GLF : scx installé mais pas démarré ; Nixerion : scx_bpfland on
    # Option off par défaut (prudence GLF) / default off (GLF caution)
    enableScx = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Activer services.scx (scx_bpfland) — Nixerion/CachyOS style";
    };
  };

  config = lib.mkIf cfg.enable {
    boot.kernelPackages = lib.mkIf cfg.useLatest pkgs.linuxPackages_latest;
    boot.supportedFilesystems.zfs = lib.mkForce false;

    boot.kernelParams = [
      "preempt=full" # GLF boot.nix
    ];

    # ntsync : Wine/Proton (GLF + Nixerion)
    boot.kernelModules = [ "ntsync" ];

    # Sysctl gaming — GLF boot.nix + Bazzite split_lock_mitigate=0
    boot.kernel.sysctl = {
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

    # CachyOS-style process priorities
    services.ananicy = {
      enable = true;
      package = pkgs.ananicy-cpp;
      rulesProvider = pkgs.ananicy-rules-cachyos;
    };

    # scx : comme GLF (présent) ; démarrage seulement si enableScx
    services.scx = lib.mkIf cfg.enableScx {
      enable = true;
      scheduler = "scx_bpfland"; # Nixerion (lavd évité)
    };
  };
}
