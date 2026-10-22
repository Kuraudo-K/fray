# PipeWire / WirePlumber (gaming + desktop)
{
  config,
  lib,
  ...
}:

let
  cfg = config.fray.system.audio;
in
{
  options.fray.system.audio = {
    enable = lib.mkEnableOption "PipeWire with low-latency defaults";
    lowLatency = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Fixed 48 kHz / 256 quantum (GLF-style)";
    };
    disableLibcamera = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Disable WirePlumber libcamera monitor (fewer webcam quirks)";
    };
  };

  config = lib.mkIf cfg.enable {
    boot.kernelParams = [ "usbcore.autosuspend=-1" ];
    security.rtkit.enable = true;

    services.pipewire = {
      enable = true;
      jack.enable = true;
      pulse.enable = true;
      alsa = {
        enable = true;
        support32Bit = true;
      };

      extraConfig.pipewire = lib.mkIf cfg.lowLatency {
        "92-low-latency" = {
          "context.properties" = {
            "default.clock.rate" = 48000;
            "default.clock.quantum" = 256;
            "default.clock.min-quantum" = 256;
            "default.clock.max-quantum" = 256;
          };
        };
      };

      wireplumber.extraConfig = lib.mkIf cfg.disableLibcamera {
        "10-disable-camera" = {
          "wireplumber.profiles" = {
            main."monitor.libcamera" = "disabled";
          };
        };
      };
    };
  };
}
