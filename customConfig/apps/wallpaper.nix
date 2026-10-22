# fray-wallpaper — liste / applique les fonds Fray (Rust hexagonal)
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.apps.wallpaper;
  src = ./wallpaper;

  fray-wallpaper = pkgs.rustPlatform.buildRustPackage {
    pname = "fray-wallpaper";
    version = "0.1.0";
    src = lib.cleanSource src;
    cargoLock.lockFile = src + /Cargo.lock;
    nativeBuildInputs = [ pkgs.makeWrapper ];
    postInstall = ''
      wrapProgram $out/bin/fray-wallpaper \
        --prefix PATH : ${
          lib.makeBinPath [
            pkgs.glib
            pkgs.kdePackages.plasma-workspace
          ]
        }
    '';
    meta = {
      description = "Fray wallpaper tool (hexagonal)";
      mainProgram = "fray-wallpaper";
    };
  };

  desktopItem = pkgs.makeDesktopItem {
    name = "fray-wallpaper";
    desktopName = "Fray Wallpaper";
    comment = "Choisir un fond d'écran Fray";
    exec = "fray-wallpaper list";
    icon = "fray";
    terminal = true;
    categories = [
      "Settings"
      "DesktopSettings"
    ];
  };
in
{
  options.fray.apps.wallpaper = {
    enable = lib.mkEnableOption "fray-wallpaper (Rust) — fonds Fray";
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [
      fray-wallpaper
      desktopItem
    ];
  };
}
