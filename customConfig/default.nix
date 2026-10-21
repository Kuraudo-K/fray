# ┌─────────────────────────────────────────────────────────────┐
# │ Fray — customConfig/default.nix                             │
# │ 1 ligne / module ; commenter = désactiver                   │
# │ One import line per module; comment = disable               │
# └─────────────────────────────────────────────────────────────┘
{ ... }:

{
  imports = [
    # ── desktop/ (DE A, DE B, switcher) ───────────────────────
    ./desktop/gnome-paperwm.nix
    ./desktop/niri-noctalia.nix
    ./desktop/de-switch.nix

    # ── system/ ───────────────────────────────────────────────
    ./system/zram-fstrim.nix

    # ── gaming/ ───────────────────────────────────────────────
    ./gaming/steam.nix
    ./gaming/faugus.nix
    ./gaming/heroic.nix
    ./gaming/gamemode.nix
    ./gaming/gamescope.nix
    ./gaming/mangohud.nix
    ./gaming/proton.nix

    # ── hardware/ ─────────────────────────────────────────────
    ./hardware/amd.nix
    ./hardware/kernel-gaming.nix

    # ── apps/ ─────────────────────────────────────────────────
    ./apps/obs.nix
    ./apps/flatpak.nix
    ./apps/fhs-bwrap.nix
    ./apps/disk.nix

    # ── services/ ─────────────────────────────────────────────
    ./services/input-remapper.nix
    ./services/update-manager.nix
  ];
}
