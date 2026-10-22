# GNOME + PaperWM
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
    enable = lib.mkEnableOption "GNOME with PaperWM tiling";
  };

  config = lib.mkIf cfg.enable {
    services.xserver.enable = true;
    services.displayManager.gdm.enable = true;
    services.desktopManager.gnome.enable = true;

    environment.systemPackages = with pkgs; [
      gnomeExtensions.paperwm
      gnome-tweaks
    ];

    programs.dconf.enable = true;
  };
}
