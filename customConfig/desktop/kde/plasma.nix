# KDE Plasma 6 (Wayland)
# Greeter : GDM (déjà activé par le module GNOME) - pas de SDDM en parallèle
# Branding : icône / wallpaper Fray via fray.branding (logo 10)
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.desktop.plasma;
in
{
  options.fray.desktop.plasma = {
    enable = lib.mkEnableOption "KDE Plasma 6 desktop (Wayland session)";
  };

  config = lib.mkIf cfg.enable {
    services.xserver.enable = true;
    services.desktopManager.plasma6.enable = true;

    # Éviter un second greeter si un autre module le propose
    # Avoid a second greeter if another module suggests one
    services.displayManager.sddm.enable = lib.mkDefault false;

    # GNOME (seahorse) + Plasma : une seule askPassword
    # GNOME (seahorse) + Plasma: only one askPassword
    programs.ssh.askPassword = lib.mkForce (lib.getExe pkgs.kdePackages.ksshaskpass);

    environment.systemPackages = with pkgs; [
      kdePackages.dolphin
      kdePackages.konsole
      kdePackages.spectacle
    ];

    # Entrée menu « À propos » / applications : icône Fray si branding pack présent
    environment.etc."xdg/plasma-workspace/env/fray-plasma-branding.sh".text = ''
      # Hint for Fray wallpaper tool / branding
      export FRAY_WALLPAPERS="''${FRAY_BRANDING:-}/share/wallpapers"
    '';
  };
}

