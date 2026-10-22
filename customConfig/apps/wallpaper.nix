# fray-wallpaper - liste / applique les fonds Fray (Rust + GUI + autostart)
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.apps.wallpaper;
  src = ./wallpaper;

  rustSrc = lib.cleanSourceWith {
    src = src;
    filter =
      path: _type:
      let
        base = baseNameOf path;
      in
      !(base == "target" || base == "gui.py" || lib.hasSuffix ".pyc" base);
  };

  fray-wallpaper = pkgs.rustPlatform.buildRustPackage {
    pname = "fray-wallpaper";
    version = "0.1.0";
    src = rustSrc;
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

  pythonEnv = pkgs.python3.withPackages (ps: [ ps.pygobject3 ]);

  fray-wallpaper-gui = pkgs.stdenv.mkDerivation {
    pname = "fray-wallpaper-gui";
    version = "0.1.0";
    dontUnpack = true;
    nativeBuildInputs = with pkgs; [
      wrapGAppsHook3
      gobject-introspection
      makeWrapper
    ];
    buildInputs = with pkgs; [
      gtk3
      glib
      pango
      gdk-pixbuf
      atk
      pythonEnv
    ];
    installPhase = ''
      runHook preInstall
      mkdir -p $out/bin $out/share/fray-wallpaper $out/share/applications
      install -m 644 ${src}/gui.py $out/share/fray-wallpaper/gui.py
      makeWrapper ${pythonEnv}/bin/python3 $out/bin/fray-wallpaper-gui \
        --add-flags "$out/share/fray-wallpaper/gui.py" \
        --set FRAY_WALLPAPER_BIN ${fray-wallpaper}/bin/fray-wallpaper \
        --set-default FRAY_ICON /run/current-system/sw/share/icons/hicolor/256x256/apps/fray-wallpaper.png \
        --prefix PATH : ${lib.makeBinPath [ fray-wallpaper pkgs.glib ]}
      cat > $out/share/applications/fray-wallpaper.desktop <<'DESKTOP'
[Desktop Entry]
Name=Fray Wallpaper
Comment=Choisir un fond d'écran Fray
Exec=fray-wallpaper-gui
Icon=fray-wallpaper
Terminal=false
Type=Application
Categories=Settings;DesktopSettings;
Keywords=fray;wallpaper;background;
StartupWMClass=fray-wallpaper
DESKTOP
      runHook postInstall
    '';
  };

  # Auto-apply au login (dernier choix ou fray-gaming-arena)
  autostart = pkgs.writeTextFile {
    name = "fray-wallpaper-autostart";
    destination = "/etc/xdg/autostart/fray-wallpaper.desktop";
    text = ''
      [Desktop Entry]
      Type=Application
      Name=Fray Wallpaper Auto
      Comment=Appliquer le fond Fray au démarrage de session
      Exec=${fray-wallpaper}/bin/fray-wallpaper auto
      Icon=fray-wallpaper
      Terminal=false
      NoDisplay=true
      X-GNOME-Autostart-enabled=true
      X-GNOME-Autostart-Delay=2
      X-KDE-autostart-phase=2
    '';
  };

  wallpaperUri = "file:///run/current-system/sw/share/backgrounds/gnome/fray-gaming-arena.png";
in
{
  options.fray.apps.wallpaper = {
    enable = lib.mkEnableOption "fray-wallpaper (Rust) - fonds Fray";
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [
      fray-wallpaper
      fray-wallpaper-gui
    ];

    # Défaut GNOME (si l'utilisateur n'a pas encore choisi)
    programs.dconf.profiles.user.databases = [
      {
        settings."org/gnome/desktop/background" = {
          picture-uri = wallpaperUri;
          picture-uri-dark = wallpaperUri;
          picture-options = "zoom";
        };
      }
    ];

    environment.etc = {
      "xdg/autostart/fray-wallpaper.desktop".source =
        "${autostart}/etc/xdg/autostart/fray-wallpaper.desktop";
    };
  };
}
