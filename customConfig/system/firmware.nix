# Firmware redistribuable (Wi‑Fi, GPU, etc.)
{
  config,
  lib,
  ...
}:

let
  cfg = config.fray.system.firmware;
in
{
  options.fray.system.firmware = {
    enable = lib.mkEnableOption "Redistributable firmware (and optional full set)";
    allFirmware = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Also enable hardware.enableAllFirmware (pulls more unfree blobs)";
    };
  };

  config = lib.mkIf cfg.enable {
    hardware.enableRedistributableFirmware = true;
    hardware.enableAllFirmware = lib.mkIf cfg.allFirmware true;
  };
}
