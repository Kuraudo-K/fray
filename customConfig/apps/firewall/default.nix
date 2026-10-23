{
  lib,
  stdenv,
  rustPlatform,
  wrapGAppsHook4,
  meson,
  ninja,
  pkg-config,
  glib,
  desktop-file-utils,
  gettext,
  librsvg,
  blueprint-compiler,
  appstream-glib,
  adwaita-icon-theme,
  libadwaita,
  gtk4,
  polkit,
  gobject-introspection,
  cargo,
  rustc,
}:

stdenv.mkDerivation rec {
  pname = "fray-firewall";
  version = (lib.importTOML ./Cargo.toml).package.version;

  src = lib.cleanSource ./.;

  cargoDeps = rustPlatform.importCargoLock {
    lockFile = ./Cargo.lock;
  };

  nativeBuildInputs = [
    appstream-glib
    blueprint-compiler
    desktop-file-utils
    gettext
    glib
    gobject-introspection
    meson
    ninja
    wrapGAppsHook4
    pkg-config
    rustPlatform.cargoSetupHook
    cargo
    rustc
  ];

  buildInputs = [
    adwaita-icon-theme
    gtk4
    libadwaita
    glib
    librsvg
    polkit
  ];

  # Set environment variables for build
  LOCALE_DIR = "${placeholder "out"}/share/locale";
  ADWAITA_ICON_THEME_PATH = "${adwaita-icon-theme}/share/icons";

  meta = with lib; {
    description = "A simple GUI to manage firewall rules on NixOS / Fray";
    license = licenses.gpl3Plus;
    mainProgram = "fray-firewall";
  };
}
