# ┌─────────────────────────────────────────────────────────────┐
# │ Fray — AMD (RDNA4 / RX 9060 XT)                             │
# │ Sources : GLF amdgpu.nix + Nixerion LACT/overdrive + rapport│
# └─────────────────────────────────────────────────────────────┘
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.hardware.amd;
in
{
  options.fray.hardware.amd = {
    enable = lib.mkEnableOption "Fray AMD graphics (RDNA4-ready)";
    overdrive = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "hardware.amdgpu.overdrive (LACT / fréquences) — Nixerion";
    };
  };

  config = lib.mkIf cfg.enable {
    hardware.graphics = {
      enable = true;
      enable32Bit = true;
    };

    hardware.amdgpu.initrd.enable = lib.mkDefault true;
    hardware.amdgpu.overdrive.enable = lib.mkIf cfg.overdrive true;

    environment.systemPackages = with pkgs; [
      vulkan-tools
      mesa-demos
      clinfo
    ]
    ++ lib.optional cfg.overdrive pkgs.lact;

    services.lact.enable = lib.mkIf cfg.overdrive true;

    boot.kernelParams = lib.mkAfter [ "amd_pstate=active" ];
  };
}
