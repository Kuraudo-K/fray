# ┌─────────────────────────────────────────────────────────────┐
# │ Fray — hosts/vm.nix (SEULE machine de test)                 │
# │ Pas de docs ici ; pas d'activation hôte                     │
# └─────────────────────────────────────────────────────────────┘
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

  # ── Activer les briques Fray / enable Fray bricks ───────────
  fray.desktop.gnomePaperwm.enable = true;
  fray.desktop.niriNoctalia.enable = true;
  fray.desktop.deSwitch.enable = true;

  fray.gaming.steam.enable = true;
  fray.gaming.faugus.enable = false; # lourd ; activer à la main si besoin
  fray.gaming.heroic.enable = true;
  fray.gaming.gamemode.enable = true;
  fray.gaming.gamescope.enable = true;
  fray.gaming.mangohud.enable = true;
  fray.gaming.proton.enable = true;

  fray.hardware.amd.enable = true;
  fray.hardware.amd.overdrive = false; # LACT inutile en VM
  fray.hardware.kernelGaming.enable = true;
  fray.hardware.kernelGaming.enableScx = false;

  fray.system.zramFstrim.enable = true;

  fray.apps.obs.enable = true;
  fray.apps.flatpak.enable = true;
  fray.apps.fhsBwrap.enable = true;
  fray.apps.disk.enable = true;

  fray.services.inputRemapper.enable = true;
  fray.services.updateManager.enable = true;

  # Deux sessions au greeter ; défaut GNOME (niri module pose mkDefault niri)
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

  services.pipewire = {
    enable = true;
    alsa.enable = true;
    alsa.support32Bit = true;
    pulse.enable = true;
  };

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

  # SSH headless
  services.openssh.enable = true;
  services.openssh.settings.PermitRootLogin = "yes";
  users.users.root.initialPassword = "fray";

  environment.systemPackages = with pkgs; [
    vim
    git
    htop
    firefox
    mesa-demos
  ];

  virtualisation = {
    memorySize = 6144;
    cores = 4;
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
