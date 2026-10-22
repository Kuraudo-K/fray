# Discord via Flatpak (Krisp + auto-update - pas le paquet nixpkgs patché)
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.apps.discord;
  flatpakOn = config.fray.apps.flatpak.enable or false;

  launcher = pkgs.writeShellApplication {
    name = "Discord";
    runtimeInputs = [
      pkgs.flatpak
      pkgs.coreutils
    ];
    text = ''
      set -euo pipefail
      if ! flatpak info com.discordapp.Discord >/dev/null 2>&1; then
        echo "Discord Flatpak absent. Installe : flatpak install -y flathub com.discordapp.Discord" >&2
        exit 1
      fi
      runtime="''${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
      mkdir -p "$runtime/app/com.discordapp.Discord"
      # Rich Presence : lien IPC hôte -> sandbox Flatpak
      if [ ! -S "$runtime/discord-ipc-0" ] || [ -L "$runtime/discord-ipc-0" ]; then
        rm -f "$runtime/discord-ipc-0"
        ln -sfn "app/com.discordapp.Discord/discord-ipc-0" "$runtime/discord-ipc-0"
      fi
      exec flatpak run com.discordapp.Discord "$@"
    '';
  };

  discordShim = pkgs.symlinkJoin {
    name = "discord-flatpak-shim";
    paths = [ launcher ];
    postBuild = ''
      ln -s Discord $out/bin/discord
    '';
    meta = {
      description = "Discord via Flathub Flatpak (Krisp + auto-update)";
      homepage = "https://discord.com/";
      license = lib.licenses.unfree;
      mainProgram = "Discord";
    };
  };

  desktopItem = pkgs.makeDesktopItem {
    name = "discord";
    desktopName = "Discord";
    comment = "Chat vocal et texte (Flatpak)";
    exec = "Discord";
    icon = "discord";
    categories = [
      "Network"
      "InstantMessaging"
    ];
  };
in
{
  options.fray.apps.discord = {
    enable = lib.mkEnableOption "Discord Flatpak (Flathub) with launcher shim";
  };

  config = lib.mkIf cfg.enable {
    assertions = [
      {
        assertion = flatpakOn;
        message = "fray.apps.discord needs fray.apps.flatpak.enable = true";
      }
    ];

    environment.systemPackages = [
      discordShim
      desktopItem
      pkgs.flatpak
    ];

    services.flatpak.packages = [ "com.discordapp.Discord" ];
  };
}
