{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem
      (system:
        let
          pkgs = import nixpkgs {
            inherit system;
          };
        in
        with pkgs;
        {
          packages = rec {
            fray-disk = pkgs.callPackage ./. {};
            default = fray-disk;
          };
          devShells.default = mkShell {
            buildInputs = with pkgs; [
              rustc
              cargo
              rust-analyzer
              clippy
              rustfmt
              meson
              ninja
              libadwaita
              adwaita-icon-theme
              gtk4
              librsvg
              pkg-config
              glib
              parted
              e2fsprogs
              util-linux
            ];

            # Environment variables for development
            RUST_SRC_PATH = "${pkgs.rust.packages.stable.rustPlatform.rustLibSrc}";
          };
        }
      );
}
