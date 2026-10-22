# Système installé (cible Calamares --flake …#fray)
# Profil de base : GNOME + outils Fray. Gaming / flatpak via fray-apply ensuite.
# hardware-configuration.nix + calamares-generated.nix sont écrits à l'install.
{
  lib,
  ...
}:

{
  imports = [
    ../customConfig
  ]
  ++ lib.optional (builtins.pathExists ../hardware-configuration.nix) ../hardware-configuration.nix
  ++ lib.optional (builtins.pathExists ../calamares-generated.nix) ../calamares-generated.nix;

  fray.branding.enable = true;

  fray.desktop.gnomePaperwm.enable = true;
  fray.desktop.gnomeExtensions.enable = true;
  fray.desktop.niriNoctalia.enable = false;
  fray.desktop.plasma.enable = false;
  fray.desktop.mangoDms.enable = false;
  fray.desktop.deSwitch.enable = true;

  # Launcher lourds : off à l'install (cache / temps). Activer avec fray-apply.
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
  fray.hardware.kernelGaming.enable = true;

  fray.system.zramFstrim.enable = true;
  fray.system.security.enable = true;
  fray.system.nh.enable = true;
  fray.system.nh.flake = "/etc/nixos";
  fray.system.nh.hostname = "fray";
  fray.system.aliases.enable = true;
  fray.system.audio.enable = true;
  fray.system.firmware.enable = true;
  fray.system.nixCompat.enable = true;
  fray.system.loginLanguage.enable = true;

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
  fray.apps.apply.enable = true;

  fray.services.inputRemapper.enable = false;
  fray.services.updateManager.enable = true;
  fray.services.autoUpdate.enable = false;

  fray.boot.limine.enable = false;
  fray.boot.plymouth.enable = true;

  nixpkgs.config.allowUnfree = true;
  system.stateVersion = "25.11";

  nix.settings.experimental-features = [
    "nix-command"
    "flakes"
  ];

  networking.networkmanager.enable = true;
}
