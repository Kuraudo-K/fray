# GameMode + manettes
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.gaming.gamemode;
in
{
  options.fray.gaming.gamemode = {
    enable = lib.mkEnableOption "GameMode and Xbox/DualSense controller support";
  };

  config = lib.mkIf cfg.enable {
    programs.gamemode.enable = true;
    environment.systemPackages = with pkgs; [ joystickwake ];

    # DualSense : ignorer le touchpad comme pointeur système
    # DualSense: ignore touchpad as a system pointer
    services.udev.extraRules = ''
      ATTRS{name}=="Sony Interactive Entertainment Wireless Controller Touchpad", ENV{LIBINPUT_IGNORE_DEVICE}="1"
      ATTRS{name}=="Sony Interactive Entertainment DualSense Wireless Controller Touchpad", ENV{LIBINPUT_IGNORE_DEVICE}="1"
      ATTRS{name}=="Wireless Controller Touchpad", ENV{LIBINPUT_IGNORE_DEVICE}="1"
      ATTRS{name}=="DualSense Wireless Controller Touchpad", ENV{LIBINPUT_IGNORE_DEVICE}="1"
    '';

    hardware.xone.enable = true;
    hardware.xpad-noone.enable = false;
    boot.extraModulePackages = [ config.boot.kernelPackages.xpadneo ];
    boot.kernelModules = [ "hid_xpadneo" ];
  };
}
