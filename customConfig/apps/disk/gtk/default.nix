{
  lib,
  stdenv,
  rustPlatform,
  wrapGAppsHook4,
  meson,
  ninja,
  pkg-config,
  gettext,
  librsvg,
  libadwaita,
  gtk4,
  adwaita-icon-theme,
  parted,
  e2fsprogs,
  util-linux,
  cargo,
  rustc,
}:

stdenv.mkDerivation rec {
  pname = "fray-disk";
  version = (lib.importTOML ./Cargo.toml).package.version;

  src = lib.cleanSource ./.;

  cargoDeps = rustPlatform.importCargoLock {
    lockFile = ./Cargo.lock;
  };

  nativeBuildInputs = [
    gettext
    meson
    ninja
    wrapGAppsHook4
    pkg-config
    rustPlatform.cargoSetupHook
    cargo
    rustc
  ];

  buildInputs = [
    gtk4
    libadwaita
    adwaita-icon-theme
    librsvg
  ];

  # Set environment variables for build
  LOCALE_DIR = "${placeholder "out"}/share/locale";

  # Pass absolute paths to the Rust binary via environment variables at build time
  PARTED_PATH = "${parted}/bin/parted";
  MKFS_EXT4_PATH = "${e2fsprogs}/bin/mkfs.ext4";

  # Wrap the binary to include runtime dependencies in PATH
  preFixup = ''
    gappsWrapperArgs+=(
      --prefix PATH : "${lib.makeBinPath [ parted e2fsprogs util-linux ]}"
      --set PARTED_BIN "${parted}/bin/parted"
      --set MKFS_EXT4_BIN "${e2fsprogs}/bin/mkfs.ext4"
    )
  '';

  meta = with lib; {
    description = "A simple GUI to manage disks on NixOS (Rust version)";
    license = licenses.gpl3Plus;
    mainProgram = "fray-disk";
  };
}
