# Apps / services de base : calc, agenda, horloge, Wi‑Fi, Bluetooth
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
    enable = lib.mkEnableOption "Calculator, calendar, clocks, Wi-Fi, Bluetooth helpers";
  };

  config = lib.mkIf cfg.enable {
    # Wi‑Fi : NetworkManager (souvent déjà on dans hosts/)
    networking.networkmanager.enable = lib.mkDefault true;

    # Bluetooth
    hardware.bluetooth = {
      enable = true;
      powerOnBoot = true;
    };
    services.blueman.enable = true;

    environment.systemPackages = with pkgs; [
      gnome-calculator
      gnome-calendar
      gnome-clocks
      networkmanagerapplet # utile hors GNOME (niri) ; Plasma a son panneau
    ];
  };
}
