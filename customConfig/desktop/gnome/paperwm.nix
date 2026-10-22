# GNOME + tweaks (PaperWM est dans extensions.nix)
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.desktop.gnomePaperwm;
in
{
  options.fray.desktop.gnomePaperwm = {
    enable = lib.mkEnableOption "GNOME desktop (use gnomeExtensions for PaperWM and friends)";
  };

  config = lib.mkIf cfg.enable {
    services.xserver.enable = true;
    services.displayManager.gdm.enable = true;
    services.desktopManager.gnome.enable = true;

    environment.systemPackages = with pkgs; [ gnome-tweaks ];

    programs.dconf.enable = true;
  };
}
