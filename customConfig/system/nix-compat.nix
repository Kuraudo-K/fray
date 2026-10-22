# Binaires non-Nix : nix-ld + AppImage
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.system.nixCompat;
in
{
  options.fray.system.nixCompat = {
    enable = lib.mkEnableOption "nix-ld and AppImage binfmt for non-Nix binaries";
    appimage = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "programs.appimage + binfmt";
    };
    nixLd = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "programs.nix-ld for unpatched dynamic binaries";
    };
  };

  config = lib.mkIf cfg.enable {
    programs.nix-ld = lib.mkIf cfg.nixLd {
      enable = true;
      libraries = with pkgs; [
        stdenv.cc.cc
        zlib
        zstd
        openssl
        curl
        dbus
        glib
        gtk3
        libGL
        vulkan-loader
        pipewire
        libpulseaudio
        SDL2
        xorg.libX11
        xorg.libXext
        xorg.libXcursor
        xorg.libXi
        xorg.libXrandr
      ];
    };

    programs.appimage = lib.mkIf cfg.appimage {
      enable = true;
      binfmt = true;
    };
  };
}
