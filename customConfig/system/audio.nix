# PipeWire / WirePlumber (gaming + desktop) - low-latency + RNNoise optionnel (mona)
{
  config,
  lib,
  pkgs,
  options,
  ...
}:

let
  cfg = config.fray.system.audio;
  hasExtraLadspa = options.services.pipewire ? extraLadspaPackages;
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
    noiseSuppression = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "RNNoise filter-chain source (mona-style)";
    };
  };

  config = lib.mkIf cfg.enable {
    boot.kernelParams = [ "usbcore.autosuspend=-1" ];
    security.rtkit.enable = true;
    services.pulseaudio.enable = false;

    services.pipewire = {
      enable = true;
      jack.enable = true;
      pulse.enable = true;
      alsa = {
        enable = true;
        support32Bit = true;
      };

      extraConfig.pipewire = lib.mkMerge [
        (lib.mkIf cfg.lowLatency {
          "92-low-latency" = {
            "context.properties" = {
              "default.clock.rate" = 48000;
              "default.clock.quantum" = 256;
              "default.clock.min-quantum" = 256;
              "default.clock.max-quantum" = 256;
            };
          };
        })
        (lib.mkIf cfg.noiseSuppression {
          "99-noise-suppression" = {
            "context.modules" = [
              {
                name = "libpipewire-module-filter-chain";
                flags = [ "nofail" ];
                args = {
                  "node.description" = "Noise Canceling Source";
                  "media.name" = "Noise Canceling Source";
                  "filter.graph" = {
                    nodes = [
                      {
                        type = "ladspa";
                        name = "rnnoise";
                        plugin = "librnnoise_ladspa";
                        label = "noise_suppressor_stereo";
                        control."VAD Threshold (%)" = 50.0;
                      }
                    ];
                  };
                  "capture.props" = {
                    "node.name" = "effect_input.rnnoise";
                    "node.passive" = true;
                    "audio.rate" = 48000;
                  };
                  "playback.props" = {
                    "node.name" = "rnnoise_source";
                    "node.description" = "Noise Canceling Source";
                    "media.class" = "Audio/Source";
                    "audio.rate" = 48000;
                  };
                };
              }
            ];
          };
        })
      ];

      wireplumber.extraConfig = lib.mkIf cfg.disableLibcamera {
        "10-disable-camera" = {
          "wireplumber.profiles" = {
            main."monitor.libcamera" = "disabled";
          };
        };
      };

      extraLadspaPackages = lib.mkIf (cfg.noiseSuppression && hasExtraLadspa) [
        pkgs.rnnoise-plugin.ladspa
      ];
    };

    systemd.user.services.pipewire.environment = lib.mkIf (
      cfg.noiseSuppression && !hasExtraLadspa
    ) { LADSPA_PATH = "${pkgs.rnnoise-plugin.ladspa}/lib/ladspa"; };
  };
}
