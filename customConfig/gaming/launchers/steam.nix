# Steam
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
      # Proton utilise la locale hôte / Proton uses host locale
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
    enable = lib.mkEnableOption "Steam client and steam-hardware";
  };

  config = lib.mkIf cfg.enable {
    hardware.steam-hardware.enable = true;
    environment.systemPackages = [ pkgs.gamescope-wsi ];

    # capSysNice=false évite un bwrap setuid qui casse pressure-vessel
    # capSysNice=false avoids setuid bwrap that breaks pressure-vessel
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

    # steam-run reste disponible via fray.apps.fhsBwrap
  };
}
