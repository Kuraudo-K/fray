# customConfig — une ligne d'import par module
# Commenter une ligne = désactiver ce module
{ ... }:

{
  imports = [
    # desktop
    ./desktop/gnome/paperwm.nix
    ./desktop/gnome/extensions.nix
    ./desktop/niri/noctalia.nix
    ./desktop/kde/plasma.nix
    ./desktop/de-switch.nix

    # system
    ./system/zram-fstrim.nix
    ./system/security.nix

    # gaming
    ./gaming/launchers/steam.nix
    ./gaming/launchers/faugus.nix
    ./gaming/launchers/heroic.nix
    ./gaming/gamemode.nix
    ./gaming/gamescope.nix
    ./gaming/mangohud.nix
    ./gaming/proton.nix
    ./gaming/umu.nix

    # hardware
    ./hardware/amd.nix
    ./hardware/kernel-gaming.nix

    # apps
    ./apps/obs.nix
    ./apps/flatpak.nix
    ./apps/fhs-bwrap.nix
    ./apps/disk.nix
    ./apps/firefox.nix
    ./apps/terminal.nix
    ./apps/base.nix

    # services
    ./services/input-remapper.nix
    ./services/update-manager.nix
  ];
}
