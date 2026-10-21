# ┌─────────────────────────────────────────────────────────────┐
# │ Fray — Flatpak déclaratif (input nix-flatpak → flake.lock)  │
# │ Inspiré Nixerion flatpak.nix                                │
# └─────────────────────────────────────────────────────────────┘
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
    enable = lib.mkEnableOption "Fray Flatpak (nix-flatpak)";
    officeApps = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Apps bureautique Flathub de base";
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
