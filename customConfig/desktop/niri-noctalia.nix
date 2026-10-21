# ┌─────────────────────────────────────────────────────────────┐
# │ Fray — DE B : Niri + Noctalia                               │
# │ Paquets nixpkgs (pinés via flake.lock)                      │
# │ Sources : wiki NixOS Niri/Noctalia + rapport recherche      │
# └─────────────────────────────────────────────────────────────┘
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.desktop.niriNoctalia;

  # Config niri minimale : lance Noctalia au démarrage
  # Minimal niri config: spawn Noctalia at startup
  niriConfig = pkgs.writeTextDir "niri/config.kdl" ''
    // Fray — config niri par défaut / default niri config
    // Les customs user vivent dans ~/.config/niri (profils fray-de-switch)
    // User customs live in ~/.config/niri (fray-de-switch profiles)

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
    enable = lib.mkEnableOption "Fray DE B — Niri + Noctalia";
  };

  config = lib.mkIf cfg.enable {
    programs.niri = {
      enable = true;
      package = pkgs.niri;
      # GNOME aussi présent : ne pas forcer nautilus-only
      useNautilus = true;
    };

    programs.noctalia = {
      enable = true;
      package = pkgs.noctalia;
      # Pas de service global : démarré par niri spawn-at-startup
      # No global service: started by niri spawn-at-startup
      systemd.enable = false;
      recommendedServices.enable = true;
    };

    # XWayland pour jeux / Steam (wiki NixOS Niri)
    environment.systemPackages = with pkgs; [
      xwayland-satellite
      kitty
      fuzzel
    ];

    # Seed config système lisible ; l'user peut overlay via ~/.config/niri
    # System seed config; user overlays via ~/.config/niri
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
