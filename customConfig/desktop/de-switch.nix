# ┌─────────────────────────────────────────────────────────────┐
# │ Fray — switcher DE (Rust) + persistance par profil          │
# │ GNOME+PaperWM ↔ Niri+Noctalia                               │
# └─────────────────────────────────────────────────────────────┘
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.desktop.deSwitch;

  src = ./../apps/de-switch;

  fray-de-switch = pkgs.rustPlatform.buildRustPackage {
    pname = "fray-de-switch";
    version = "0.1.0";
    src = lib.cleanSource src;
    cargoLock.lockFile = src + /Cargo.lock;
    meta = {
      description = "Fray desktop environment switcher with per-DE persistence";
      mainProgram = "fray-de-switch";
    };
  };

  desktopItem = pkgs.makeDesktopItem {
    name = "fray-de-switch";
    desktopName = "Fray DE Switch";
    comment = "Basculer GNOME+PaperWM ↔ Niri+Noctalia (profils persistants)";
    exec = "fray-de-switch list";
    terminal = true;
    categories = [
      "Settings"
      "System"
    ];
  };
in
{
  options.fray.desktop.deSwitch = {
    enable = lib.mkEnableOption "Fray Rust DE switcher (persistance customs/DE)";
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [
      fray-de-switch
      desktopItem
    ];
  };
}
