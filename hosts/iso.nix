# ISO Fray installable (Calamares + branding logo 10)
{
  config,
  modulesPath,
  lib,
  pkgs,
  ...
}:

{
  imports = [
    (modulesPath + "/installer/cd-dvd/installation-cd-graphical-calamares-gnome.nix")
    ../customConfig
    ../iso-cfg/calamares.nix
  ];

  fray.branding.enable = true;

  fray.desktop.gnomePaperwm.enable = true;
  fray.desktop.gnomeExtensions.enable = false;
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
  fray.gaming.umu.enable = false;

  fray.hardware.amd.enable = true;
  fray.hardware.amd.overdrive = false;
  fray.hardware.kernelGaming.enable = true;
  fray.hardware.kernelGaming.enableScx = false;

  fray.system.zramFstrim.enable = true;
  fray.system.security.enable = true;
  fray.system.nh.enable = false;
  fray.system.aliases.enable = false;
  fray.system.audio.enable = true;
  fray.system.firmware.enable = true;
  fray.system.nixCompat.enable = false;

  fray.apps.flatpak.enable = false;
  fray.apps.fhsBwrap.enable = false;
  fray.apps.obs.enable = false;
  fray.apps.disk.enable = true;
  fray.apps.wallpaper.enable = true;
  fray.apps.discord.enable = false;
  fray.apps.matrix.enable = false;
  fray.apps.firefox.enable = true;
  fray.apps.terminal.enable = true;
  fray.apps.base.enable = true;
  fray.apps.apply.enable = false;

  fray.services.inputRemapper.enable = false;
  fray.services.updateManager.enable = true;
  fray.services.autoUpdate.enable = false;

  # Live ISO : pas de Limine (conflit isoImage) ; Plymouth Fray OK
  fray.boot.limine.enable = false;
  fray.boot.plymouth.enable = true;

  networking.hostName = "fray-iso";
  nixpkgs.config.allowUnfree = true;
  system.stateVersion = "25.11";

  nix.settings.experimental-features = [
    "nix-command"
    "flakes"
  ];

  # ZFS souvent cassé avec un noyau trop récent
  boot.supportedFilesystems.zfs = lib.mkForce false;

  isoImage = {
    isoName = lib.mkForce "fray-${config.system.nixos.release or "unstable"}-x86_64-linux.iso";
    volumeID = lib.mkForce "FRAY_ISO";
    edition = lib.mkForce "fray";
  };

  environment.systemPackages = with pkgs; [
    gparted
  ];
}
