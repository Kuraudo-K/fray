# Terminal unique Fray : kitty (GPU, customisable)
# Retire les doublons menu (gnome-console / kgx, konsole, xterm).
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.apps.terminal;

  # Ecrase le .desktop amont (meme id, Hidden=true). writeTextFile destination
  # = chemin sous $out ; le nom du fichier DOIT etre l'id .desktop exact.
  hideApp =
    id: pkgs.writeTextFile {
      name = "hide-${id}";
      destination = "/share/applications/${id}";
      text = ''
        [Desktop Entry]
        Type=Application
        Name=Hidden
        Exec=true
        NoDisplay=true
        Hidden=true
      '';
    };
in
{
  options.fray.apps.terminal = {
    enable = lib.mkEnableOption "Shared kitty terminal for all desktops";
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [
      pkgs.kitty
      (hideApp "org.gnome.Console.desktop")
      (hideApp "kgx.desktop")
      (hideApp "org.kde.konsole.desktop")
      (hideApp "konsole.desktop")
      (hideApp "xterm.desktop")
      (hideApp "org.gnome.Ptyxis.desktop")
    ];

    environment.gnome.excludePackages = lib.mkDefault (
      with pkgs;
      [
        gnome-console
      ]
      ++ lib.optional (pkgs ? ptyxis) pkgs.ptyxis
    );

    # Kitty = terminal par defaut (xdg-terminal-exec / GNOME)
    xdg.terminal-exec = {
      enable = true;
      settings.default = [ "kitty.desktop" ];
    };

    programs.dconf.profiles.user.databases = [
      {
        settings."org/gnome/desktop/applications/terminal" = {
          exec = "kitty";
          exec-arg = "";
        };
      }
    ];
  };
}
