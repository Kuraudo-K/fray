# customConfig — une ligne d'import par module
# Commenter une ligne = désactiver ce module
# One import line per module; comment out to disable
{ ... }:

{
  imports = [
    # desktop
    ./desktop/gnome/paperwm.nix
    ./desktop/niri/noctalia.nix
    ./desktop/de-switch.nix

    # system
    ./system/zram-fstrim.nix

    # gaming
    ./gaming/launchers/steam.nix
    ./gaming/launchers/faugus.nix
    ./gaming/launchers/heroic.nix
    ./gaming/gamemode.nix
    ./gaming/gamescope.nix
    ./gaming/mangohud.nix
    ./gaming/proton.nix

    # hardware
    ./hardware/amd.nix
    ./hardware/kernel-gaming.nix

    # apps
    ./apps/obs.nix
    ./apps/flatpak.nix
    ./apps/fhs-bwrap.nix
    ./apps/disk.nix

    # services
    ./services/input-remapper.nix
    ./services/update-manager.nix
  ];
}
