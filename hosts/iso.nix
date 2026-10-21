# ┌─────────────────────────────────────────────────────────────┐
# │ Fray — ISO installateur (optionnel)                         │
# └─────────────────────────────────────────────────────────────┘
{
  modulesPath,
  lib,
  ...
}:

{
  imports = [
    (modulesPath + "/installer/cd-dvd/installation-cd-graphical-gnome.nix")
    ../customConfig
  ];

  fray.desktop.gnomePaperwm.enable = true;
  fray.desktop.niriNoctalia.enable = false; # ISO légère
  fray.desktop.deSwitch.enable = false;

  fray.gaming.steam.enable = false;
  fray.gaming.heroic.enable = false;
  fray.gaming.gamemode.enable = true;
  fray.gaming.gamescope.enable = false;
  fray.gaming.mangohud.enable = false;
  fray.gaming.proton.enable = false;
  fray.gaming.faugus.enable = false;

  fray.hardware.amd.enable = true;
  fray.hardware.amd.overdrive = false;
  fray.hardware.kernelGaming.enable = true;

  fray.system.zramFstrim.enable = true;
  fray.apps.flatpak.enable = false;
  fray.apps.fhsBwrap.enable = false;
  fray.apps.obs.enable = false;
  fray.apps.disk.enable = true;
  fray.services.inputRemapper.enable = false;
  fray.services.updateManager.enable = true;

  networking.hostName = "fray-iso";
  nixpkgs.config.allowUnfree = true;
  system.stateVersion = "25.11";

  # ISO : pas de ZFS avec latest kernel
  boot.supportedFilesystems.zfs = lib.mkForce false;
}
