# Timer auto : appelle fray-update (flake + Flatpak, sans switch)
{
  config,
  lib,
  ...
}:

let
  cfg = config.fray.services.autoUpdate;
in
{
  options.fray.services.autoUpdate = {
    enable = lib.mkEnableOption "Automatic Flatpak + Fray flake update timer";
    onCalendar = lib.mkOption {
      type = lib.types.str;
      default = "weekly";
      description = "systemd OnCalendar for the auto-update timer";
    };
  };

  config = lib.mkIf cfg.enable {
    # Dépend du CLI unifié
    fray.services.updateManager.enable = true;

    nix.gc = {
      automatic = true;
      dates = "weekly";
      options = "--delete-older-than 14d";
    };
    nix.settings.auto-optimise-store = true;

    systemd.services.fray-auto-update = {
      description = "Fray Flatpak + flake update (no host rebuild)";
      after = [ "network-online.target" ];
      wants = [ "network-online.target" ];
      serviceConfig = {
        Type = "oneshot";
        ExecStart = "${config.fray.services.updateManager.package}/bin/fray-update";
      };
    };

    systemd.timers.fray-auto-update = {
      description = "Timer for fray-update (auto)";
      wantedBy = [ "timers.target" ];
      timerConfig = {
        OnCalendar = cfg.onCalendar;
        Persistent = true;
        RandomizedDelaySec = "30m";
      };
    };
  };
}
