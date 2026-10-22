# Proton-GE (+ proton-cachyos-bin s'il est dans nixpkgs)
# Uniquement via Steam extraCompatPackages
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.gaming.proton;
  cachy = lib.optional (pkgs ? proton-cachyos-bin) pkgs.proton-cachyos-bin;
in
{
  options.fray.gaming.proton = {
    enable = lib.mkEnableOption "Proton-GE compatibility tools for Steam";
  };

  config = lib.mkIf cfg.enable {
    programs.steam.extraCompatPackages = lib.mkAfter ([ pkgs.proton-ge-bin ] ++ cachy);

    environment.sessionVariables.STEAM_EXTRA_COMPAT_TOOLS_PATHS =
      "\${HOME}/.steam/root/compatibilitytools.d";
  };
}
