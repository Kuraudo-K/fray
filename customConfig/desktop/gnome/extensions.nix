# Extensions GNOME — uniquement celles activées chez kouro (interrupteurs orange)
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.desktop.gnomeExtensions;

  # Paquets + UUID (ordre = liste user)
  extPkgs = with pkgs.gnomeExtensions; [
    open-bar
    pip-on-top
    appindicator
    blur-my-shell
    brightness-control-using-ddcutil
    caffeine
    dash-to-dock
    paperwm
    quick-settings-audio-panel
    vitals
  ];

  extUuids = map (e: e.extensionUuid) extPkgs;
in
{
  options.fray.desktop.gnomeExtensions = {
    enable = lib.mkEnableOption "GNOME Shell extensions enabled on kouro's desktop";
  };

  config = lib.mkIf cfg.enable {
    programs.dconf.enable = true;

    environment.systemPackages = extPkgs ++ [
      pkgs.ddcutil # requis par Brightness control using ddcutil
    ];

    # Accès I2C pour ddcutil / I2C access for ddcutil
    hardware.i2c.enable = true;
    users.groups.i2c.members = [ "kouro" ];

    # Active les extensions pour le profil user (session GNOME)
    # Enable extensions for the user dconf profile (GNOME session)
    programs.dconf.profiles.user.databases = [
      {
        settings = {
          "org/gnome/shell" = {
            disable-user-extensions = false;
            enabled-extensions = extUuids;
          };
        };
      }
    ];
  };
}
