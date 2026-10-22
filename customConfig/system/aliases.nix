# Alias shell Fray (pas mona / pas /etc/nixos)
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.system.aliases;
  flake = config.fray.system.nh.flake or "/home/kouro/Téléchargements/GLF pc/NIX/fray";
  esc = lib.escapeShellArg;

  aliases = {
    fray-gc = "sudo nix-collect-garbage --delete-older-than 5d";
    fray-gens = "sudo nix-env --list-generations --profile /nix/var/nix/profiles/system";
    fray-history = "nix store diff-closures $(ls -d1v /nix/var/nix/profiles/system-*-link | tail -n 2)";
    fray-info = "inxi -Fxxxz";
    fray-vm-build = "fray-update --build --host fray-vm --flake ${esc flake}";
    fray-iso-build = "fray-update --build --host fray-iso --flake ${esc flake}";
  };
in
{
  options.fray.system.aliases = {
    enable = lib.mkEnableOption "Extra Fray shell aliases (gc, gens, info…)";
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = with pkgs; [
      inxi
      pciutils
      util-linux
      gawk
    ];
    environment.shellAliases = aliases;
    programs.fish.shellAliases = aliases;
  };
}
