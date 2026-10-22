# input-remapper + autoload après login
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.services.inputRemapper;
in
{
  options.fray.services.inputRemapper = {
    enable = lib.mkEnableOption "input-remapper with autoload on graphical session";
  };

  config = lib.mkIf cfg.enable {
    services.input-remapper = {
      enable = true;
      enableUdevRules = true;
    };

    security.polkit.extraConfig = ''
      polkit.addRule(function(action, subject) {
        if (action.id == "inputremapper" && subject.isInGroup("users")) {
          return polkit.Result.YES;
        }
      });
    '';

    systemd.user.services.fray-input-remapper-autoload = {
      description = "Autoload input-remapper presets";
      wantedBy = [ "graphical-session.target" ];
      after = [ "graphical-session.target" ];
      serviceConfig = {
        Type = "oneshot";
        RemainAfterExit = true;
        ExecStartPre = "${pkgs.coreutils}/bin/sleep 3";
        ExecStart = "${pkgs.input-remapper}/bin/input-remapper-control --command autoload";
      };
    };
  };
}
