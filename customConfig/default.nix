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
    ./desktop/mango
    ./desktop/de-switch.nix

    # boot
    ./boot/limine.nix
    ./boot/plymouth.nix
    ./boot/lanzaboote.nix

    # system
    ./system/zram-fstrim.nix
    ./system/security.nix
    ./system/nh.nix
    ./system/aliases.nix
    ./system/audio.nix
    ./system/firmware.nix
    ./system/nix-compat.nix

    # gaming
    ./gaming/launchers/steam.nix
    ./gaming/launchers/faugus.nix
    ./gaming/launchers/faugus-update.nix
    ./gaming/launchers/heroic.nix
    ./gaming/lutris.nix
    ./gaming/8bitdo.nix
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
    ./apps/discord.nix
    ./apps/matrix.nix
    ./apps/kdeconnect.nix
    ./apps/firefox.nix
    ./apps/terminal.nix
    ./apps/base.nix

    # services
    ./services/input-remapper.nix
    ./services/update-manager.nix
    ./services/auto-update.nix
    ./services/battery-notify.nix
  ];
}
