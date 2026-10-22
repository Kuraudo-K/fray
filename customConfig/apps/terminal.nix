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

  hideDesktop = name: text: pkgs.writeTextDir "share/applications/${name}.desktop" text;
in
{
  options.fray.apps.terminal = {
    enable = lib.mkEnableOption "Shared kitty terminal for all desktops";
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [
      pkgs.kitty
      # Masque les .desktop fournis par GNOME / Plasma / xterm
      (hideDesktop "org.gnome.Console.desktop" ''
        [Desktop Entry]
        Name=Console
        Type=Application
        NoDisplay=true
        Hidden=true
        Exec=true
      '')
      (hideDesktop "kgx.desktop" ''
        [Desktop Entry]
        Name=Console
        Type=Application
        NoDisplay=true
        Hidden=true
        Exec=true
      '')
      (hideDesktop "org.kde.konsole.desktop" ''
        [Desktop Entry]
        Name=Konsole
        Type=Application
        NoDisplay=true
        Hidden=true
        Exec=true
      '')
      (hideDesktop "konsole.desktop" ''
        [Desktop Entry]
        Name=Konsole
        Type=Application
        NoDisplay=true
        Hidden=true
        Exec=true
      '')
      (hideDesktop "xterm.desktop" ''
        [Desktop Entry]
        Name=XTerm
        Type=Application
        NoDisplay=true
        Hidden=true
        Exec=true
      '')
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
