# GNOME + GDM + tweaks (O-Tiling / extensions : extensions.nix)
# Option historique fray.desktop.gnomePaperwm (nom conservé pour compat hosts).
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
    enable = lib.mkEnableOption "GNOME desktop (use gnomeExtensions for O-Tiling and friends)";
  };

  config = lib.mkIf cfg.enable {
    services.xserver.enable = true;
    services.displayManager.gdm.enable = true;
    services.desktopManager.gnome.enable = true;

    environment.systemPackages = with pkgs; [ gnome-tweaks ];

    programs.dconf.enable = true;
  };
}
