# ┌─────────────────────────────────────────────────────────────┐
# │ Fray — Steam (adapté GLF gaming/steam.nix)                  │
# │ OBS_VKCAPTURE, HOST_LC_ALL, gamescope-wsi, capSysNice=false │
# └─────────────────────────────────────────────────────────────┘
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.gaming.steam;

  fraySteam = pkgs.steam.override {
    extraEnv = {
      OBS_VKCAPTURE = "1";
      HOST_LC_ALL = config.i18n.defaultLocale;
    };
    extraPkgs =
      _pkgs: with pkgs; [
        gamescope
        gamescope-wsi
      ];
  };
in
{
  options.fray.gaming.steam = {
    enable = lib.mkEnableOption "Fray Steam";
  };

  config = lib.mkIf cfg.enable {
    hardware.steam-hardware.enable = true;
    environment.systemPackages = [ pkgs.gamescope-wsi ];

    # false : évite setuid bwrap / pressure-vessel (GLF) — pas true (Nixerion)
    programs.gamescope = {
      enable = true;
      capSysNice = false;
    };

    programs.steam = {
      enable = true;
      package = fraySteam;
      remotePlay.openFirewall = true;
      localNetworkGameTransfers.openFirewall = true;
    };
  };
}
