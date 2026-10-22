# ISO Fray (optionnelle, plus légère que la VM)
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
  fray.desktop.niriNoctalia.enable = false;
  fray.desktop.plasma.enable = false;
  fray.desktop.mangoDms.enable = false;
  fray.desktop.deSwitch.enable = false;

  fray.gaming.steam.enable = false;
  fray.gaming.heroic.enable = false;
  fray.gaming.gamemode.enable = true;
  fray.gaming.gamescope.enable = false;
  fray.gaming.mangohud.enable = false;
  fray.gaming.proton.enable = false;
  fray.gaming.faugus.enable = false;
  fray.gaming.faugusUpdate.enable = false;
  fray.gaming.lutris.enable = false;
  # kdeconnect / battery-notify / lanzaboote : fichiers gardés, imports commentés

  fray.hardware.amd.enable = true;
  fray.hardware.amd.overdrive = false;
  fray.hardware.kernelGaming.enable = true;

  fray.system.zramFstrim.enable = true;
  fray.system.nh.enable = false;
  fray.system.aliases.enable = false;
  fray.system.audio.enable = true;
  fray.system.firmware.enable = true;
  fray.system.nixCompat.enable = false;
  fray.apps.flatpak.enable = false;
  fray.apps.fhsBwrap.enable = false;
  fray.apps.obs.enable = false;
  fray.apps.disk.enable = true;
  fray.apps.base.enable = true;
  fray.services.inputRemapper.enable = false;
  fray.services.updateManager.enable = true;
  fray.services.autoUpdate.enable = false;

  # Boot ISO / install réelle (pas QEMU)
  fray.boot.limine.enable = true;
  fray.boot.plymouth.enable = true;

  networking.hostName = "fray-iso";
  nixpkgs.config.allowUnfree = true;
  system.stateVersion = "25.11";

  # ZFS souvent cassé avec un noyau trop récent
  boot.supportedFilesystems.zfs = lib.mkForce false;
}
