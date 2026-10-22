# Splash Plymouth (quiet boot) — thème Fray (logo 10) si branding actif
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.boot.plymouth;
  plymouth-fray = pkgs.callPackage ../branding/plymouth { };
in
{
  options.fray.boot.plymouth = {
    enable = lib.mkEnableOption "Plymouth boot splash";
    theme = lib.mkOption {
      type = lib.types.str;
      default = "fray";
      description = "Plymouth theme name (default: fray)";
    };
  };

  config = lib.mkIf cfg.enable {
    boot.initrd.systemd.enable = lib.mkDefault true;

    boot.plymouth = {
      enable = true;
      theme = cfg.theme;
      themePackages = lib.mkDefault [ plymouth-fray ];
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
