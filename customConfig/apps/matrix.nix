# Matrix — Element Desktop Flatpak (E2EE, appels ; auto-update Flathub)
# Alternative plus légère : pkgs.fractal (GNOME) — voir docs
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.apps.matrix;
  flatpakOn = config.fray.apps.flatpak.enable or false;

  launcher = pkgs.writeShellApplication {
    name = "element-desktop";
    runtimeInputs = [
      pkgs.flatpak
      pkgs.coreutils
    ];
    text = ''
      set -euo pipefail
      if ! flatpak info im.riot.Riot >/dev/null 2>&1; then
        echo "Element Flatpak absent. Installe : flatpak install -y flathub im.riot.Riot" >&2
        exit 1
      fi
      exec flatpak run im.riot.Riot "$@"
    '';
  };

  elementShim = pkgs.symlinkJoin {
    name = "element-flatpak-shim";
    paths = [ launcher ];
    postBuild = ''
      ln -s element-desktop $out/bin/element
    '';
    meta = {
      description = "Element Matrix client via Flathub";
      homepage = "https://element.io/";
      mainProgram = "element-desktop";
    };
  };

  desktopItem = pkgs.makeDesktopItem {
    name = "element-desktop";
    desktopName = "Element";
    comment = "Client Matrix (Flatpak)";
    exec = "element-desktop";
    icon = "element-desktop";
    categories = [
      "Network"
      "InstantMessaging"
    ];
  };
in
{
  options.fray.apps.matrix = {
    enable = lib.mkEnableOption "Element Matrix client (Flathub Flatpak)";
  };

  config = lib.mkIf cfg.enable {
    assertions = [
      {
        assertion = flatpakOn;
        message = "fray.apps.matrix needs fray.apps.flatpak.enable = true";
      }
    ];

    environment.systemPackages = [
      elementShim
      desktopItem
      pkgs.flatpak
    ];

    services.flatpak.packages = [ "im.riot.Riot" ];
  };
}
