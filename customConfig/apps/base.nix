# Apps / outils de base : desk + CLI + polices
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.apps.base;
in
{
  options.fray.apps.base = {
    enable = lib.mkEnableOption "Calculator, calendar, clocks, Wi-Fi, Bluetooth, CLI tools, fonts";
  };

  config = lib.mkIf cfg.enable {
    networking.networkmanager.enable = lib.mkDefault true;

    hardware.bluetooth = {
      enable = true;
      powerOnBoot = true;
    };
    services.blueman.enable = true;

    fonts.packages = with pkgs; [
      noto-fonts
      noto-fonts-cjk-sans
      noto-fonts-color-emoji
      liberation_ttf
    ];

    environment.systemPackages = with pkgs; [
      # desk
      gnome-calculator
      gnome-calendar
      gnome-clocks
      networkmanagerapplet
      file-roller
      eog

      # CLI utiles
      git
      curl
      wget
      btop
      htop
      pciutils
      usbutils
      lsof
      ripgrep
      fd
      jq
      p7zip
      unzip
      zip
      ffmpeg
      fastfetch
    ];
  };
}
