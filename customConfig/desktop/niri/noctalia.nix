# Niri + Noctalia
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.desktop.niriNoctalia;

  # Config de base : lance Noctalia au démarrage
  # Base config: start Noctalia at startup
  niriConfig = pkgs.writeTextDir "niri/config.kdl" ''
    // Fray - config niri par défaut
    // Customs utilisateur : ~/.config/niri (profils fray-de-switch)

    spawn-at-startup "noctalia"

    input {
      keyboard {
        xkb {
          layout "us"
          variant "alt-intl"
        }
      }
    }

    binds {
      Mod+Shift+E { quit; }
      Mod+T { spawn "kitty"; }
      Mod+D { spawn "noctalia" "ipc" "call" "launcher" "toggle"; }
    }
  '';
in
{
  options.fray.desktop.niriNoctalia = {
    enable = lib.mkEnableOption "Niri compositor with Noctalia shell";
  };

  config = lib.mkIf cfg.enable {
    programs.niri = {
      enable = true;
      package = pkgs.niri;
      useNautilus = true;
    };

    programs.noctalia = {
      enable = true;
      package = pkgs.noctalia;
      # Pas de service global : démarré par niri
      # No global service: started by niri
      systemd.enable = false;
      recommendedServices.enable = true;
    };

    # kitty fourni par fray.apps.terminal (terminal unique)
    environment.systemPackages = with pkgs; [
      xwayland-satellite
      fuzzel
    ];

    environment.etc."xdg/niri/config.kdl".source = "${niriConfig}/niri/config.kdl";

    xdg.portal = {
      enable = true;
      extraPortals = [ pkgs.xdg-desktop-portal-gnome ];
      config.niri = {
        "org.freedesktop.impl.portal.FileChooser" = [ "gtk" ];
      };
    };

    environment.sessionVariables.NIXOS_OZONE_WL = "1";
  };
}
