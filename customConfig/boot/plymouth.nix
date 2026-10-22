# Splash Plymouth (quiet boot)
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.boot.plymouth;
in
{
  options.fray.boot.plymouth = {
    enable = lib.mkEnableOption "Plymouth boot splash";
    theme = lib.mkOption {
      type = lib.types.str;
      default = "breeze";
      description = "Plymouth theme name";
    };
  };

  config = lib.mkIf cfg.enable {
    boot.initrd.systemd.enable = lib.mkDefault true;

    boot.plymouth = {
      enable = true;
      theme = cfg.theme;
    };

    boot.consoleLogLevel = 3;
    boot.initrd.verbose = false;
    boot.kernelParams = [
      "quiet"
      "udev.log_level=3"
      "systemd.show_status=auto"
    ];
  };
}
