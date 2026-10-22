# VM de test Fray (QEMU) — pas d'activation sur la machine réelle
{
  lib,
  pkgs,
  modulesPath,
  ...
}:

{
  imports = [
    (modulesPath + "/virtualisation/qemu-vm.nix")
    ../customConfig
  ];

  # --- Desktop (4 DE) ---
  fray.desktop.gnomePaperwm.enable = true;
  fray.desktop.gnomeExtensions.enable = true;
  fray.desktop.niriNoctalia.enable = true;
  fray.desktop.plasma.enable = true;
  fray.desktop.mangoDms.enable = true;
  fray.desktop.deSwitch.enable = true;

  # --- Gaming ---
  fray.gaming.steam.enable = true;
  fray.gaming.faugus.enable = false;
  fray.gaming.faugusUpdate.enable = true;
  fray.gaming.lutris.enable = true;
  fray.gaming.eightBitDo.enable = false; # Wine lourd ; activer à la main
  fray.gaming.heroic.enable = true;
  fray.gaming.gamemode.enable = true;
  fray.gaming.gamescope.enable = true;
  fray.gaming.mangohud.enable = true;
  fray.gaming.proton.enable = true;
  fray.gaming.umu.enable = true;

  # --- Hardware ---
  fray.hardware.amd.enable = true;
  fray.hardware.amd.overdrive = false; # LACT inutile en VM
  fray.hardware.kernelGaming.enable = true;
  fray.hardware.kernelGaming.enableScx = false;

  fray.system.zramFstrim.enable = true;
  fray.system.security.enable = true;
  fray.system.nh.enable = true;
  fray.system.aliases.enable = true;
  fray.system.audio.enable = true;
  fray.system.firmware.enable = true;
  fray.system.nixCompat.enable = true;

  # --- Apps / services ---
  fray.apps.obs.enable = true;
  fray.apps.flatpak.enable = true;
  fray.apps.fhsBwrap.enable = true;
  fray.apps.disk.enable = true;
  fray.apps.discord.enable = true;
  fray.apps.matrix.enable = true;
  fray.apps.kdeconnect.enable = true;
  fray.apps.firefox.enable = true;
  fray.apps.terminal.enable = true;
  fray.apps.base.enable = true;
  fray.services.inputRemapper.enable = true;
  fray.services.updateManager.enable = true;
  fray.services.autoUpdate.enable = true;
  fray.services.batteryNotify.enable = true;

  # Limine/Plymouth/Lanzaboote : ISO / machine réelle, pas QEMU
  fray.boot.limine.enable = false;
  fray.boot.plymouth.enable = false;
  fray.boot.lanzaboote.enable = false;

  # Quatre sessions ; GNOME par défaut
  services.displayManager.defaultSession = "gnome";

  networking.hostName = "fray-vm";
  networking.networkmanager.enable = true;

  nix.settings.experimental-features = [
    "nix-command"
    "flakes"
  ];
  nixpkgs.config.allowUnfree = true;

  time.timeZone = "Europe/Paris";
  i18n.defaultLocale = "fr_FR.UTF-8";
  console.useXkbConfig = true;
  services.xserver.xkb = {
    layout = "us";
    variant = "alt-intl";
  };

  # Audio : fray.system.audio (PipeWire)

  users.users.kouro = {
    isNormalUser = true;
    description = "Kouro";
    extraGroups = [
      "networkmanager"
      "wheel"
      "video"
      "render"
      "input"
      "users"
    ];
    initialPassword = "fray";
    shell = pkgs.fish;
  };
  programs.fish.enable = true;
  security.sudo.wheelNeedsPassword = false;

  services.openssh.enable = true;
  services.openssh.settings.PermitRootLogin = "yes";
  users.users.root.initialPassword = "fray";

  environment.systemPackages = with pkgs; [
    vim
  ];

  virtualisation = {
    memorySize = 6144;
    cores = 4;
    # Flatpak Discord/Element + runtimes need room (default 1024 Mo trop juste)
    diskSize = 12288;
    graphics = false;
    forwardPorts = [
      {
        from = "host";
        host.port = 2222;
        guest.port = 22;
      }
    ];
  };

  system.stateVersion = "25.11";
}
