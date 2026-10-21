# ┌─────────────────────────────────────────────────────────────┐
# │ Fray — zram + fstrim (Nixerion perf-gaming + GLF system)    │
# └─────────────────────────────────────────────────────────────┘
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
    enable = lib.mkEnableOption "Fray zram zstd + fstrim";
    memoryPercent = lib.mkOption {
      type = lib.types.int;
      default = 30;
      description = "zram % RAM (Nixerion 30 ; GLF 50)";
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
