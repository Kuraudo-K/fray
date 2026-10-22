# Faugus - overlay framagit (défaut) ou pin GitHub (faugus-version.nix)
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.gaming.faugus;
  ver = import ./faugus-version.nix;

  faugusGithub = pkgs.python3Packages.buildPythonApplication (
    finalAttrs: {
      pname = "faugus-launcher";
      version = ver.version;
      pyproject = false;

      src = pkgs.fetchFromGitHub {
        owner = "Faugus";
        repo = "faugus-launcher";
        tag = finalAttrs.version;
        hash = ver.hash;
      };

      nativeBuildInputs = with pkgs; [
        gobject-introspection
        meson
        ninja
        wrapGAppsHook4
      ];

      buildInputs = with pkgs; [
        gtk4
        libadwaita
        libmanette
        libayatana-appindicator
        gst_all_1.gstreamer
        gst_all_1.gst-plugins-base
        gst_all_1.gst-plugins-good
        gst_all_1.gst-plugins-bad
      ];

      dependencies = with pkgs.python3Packages; [
        pillow
        psutil
        pygobject3
        requests
        vdf
        dbus-python
      ];

      postPatch = ''
        substituteInPlace faugus-launcher \
          --replace-fail "/usr/bin/python3" "${pkgs.python3Packages.python.interpreter}"
        substituteInPlace faugus/path_manager.py \
          --replace-fail "PathManager.user_data('faugus-launcher/umu-run')" "'${lib.getExe pkgs.umu-launcher}'"
      '';

      dontWrapGApps = true;
      preFixup = ''
        makeWrapperArgs+=(
          "''${gappsWrapperArgs[@]}"
          --suffix PYTHONPATH : "$out/${pkgs.python3Packages.python.sitePackages}:$PYTHONPATH"
          --suffix PATH : "${
            lib.makeBinPath (
              with pkgs;
              [
                icoextract
                imagemagick
                libcanberra-gtk3
                umu-launcher
                vulkan-tools
                xdg-utils
              ]
            )
          }"
        )
        wrapProgram $out/bin/faugus-launcher ''${makeWrapperArgs[@]}
      '';

      meta = {
        description = "Windows games via UMU";
        homepage = "https://github.com/Faugus/faugus-launcher";
        license = lib.licenses.mit;
        mainProgram = "faugus-launcher";
        platforms = lib.platforms.linux;
      };
    }
  );

  pkg =
    if cfg.useGithubPin then
      faugusGithub
    else if pkgs ? faugus-launcher then
      pkgs.faugus-launcher
    else
      null;
in
{
  options.fray.gaming.faugus = {
    enable = lib.mkEnableOption "Faugus game launcher";
    useGithubPin = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Build from GitHub using faugus-version.nix (else framagit overlay)";
    };
  };

  config = lib.mkIf cfg.enable {
    assertions = [
      {
        assertion = pkg != null;
        message = "fray.gaming.faugus : paquet introuvable (pin GitHub ou overlay framagit)";
      }
    ];
    environment.systemPackages = lib.optional (pkg != null) pkg;
  };
}
