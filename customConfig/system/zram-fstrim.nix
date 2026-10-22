# zram (swap compressé) + TRIM périodique des SSD
{
  config,
  lib,
  ...
}:

let
  cfg = config.fray.system.zramFstrim;
in
{
  options.fray.system.zramFstrim = {
    enable = lib.mkEnableOption "zram swap (zstd) and periodic fstrim";
    memoryPercent = lib.mkOption {
      type = lib.types.int;
      default = 30;
      description = "Percent of RAM reserved for compressed zram swap";
    };
  };

  config = lib.mkIf cfg.enable {
    zramSwap = {
      enable = true;
      algorithm = "zstd";
      memoryPercent = cfg.memoryPercent;
    };
    services.fstrim.enable = true;
  };
}
