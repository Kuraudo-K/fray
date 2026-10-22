# Flatpak déclaratif (module nix-flatpak)
{
  config,
  lib,
  ...
}:

let
  cfg = config.fray.apps.flatpak;
in
{
  options.fray.apps.flatpak = {
    enable = lib.mkEnableOption "Declarative Flatpak with Flathub";
    officeApps = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Install basic Flathub office apps (LibreOffice, Evince, etc.)";
    };
  };

  config = lib.mkIf cfg.enable {
    services.flatpak.enable = true;
    xdg.portal.enable = true;

    services.flatpak.packages = lib.mkIf cfg.officeApps [
      "org.libreoffice.LibreOffice"
      "org.gnome.Evince"
      "org.gnome.Calculator"
      "org.gnome.TextEditor"
    ];

    services.flatpak.update.auto = {
      enable = true;
      onCalendar = "weekly";
    };
  };
}
