# Lutris + umu / mangohud / vkbasalt (même nixpkgs - pas de mismatch glibc)
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.gaming.lutris;
in
{
  options.fray.gaming.lutris = {
    enable = lib.mkEnableOption "Lutris with umu-launcher and overlay libs";
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [
      (pkgs.lutris.override {
        extraLibraries =
          p: with p; [
            libadwaita
            gtk4
            gamemode.lib
            mangohud
            vkbasalt
          ];
        extraPkgs =
          p: with p; [
            umu-launcher
            mangohud
            vkbasalt
            vulkan-tools
            goverlay
            curl
            wget
            gnutar
            xz
            bzip2
            gzip
          ];
      })
    ];
  };
}
