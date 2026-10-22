# AMD GPU (RDNA4 / RX 9060 XT et cousins)
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
    enable = lib.mkEnableOption "AMD graphics stack (Vulkan, Mesa, initrd)";
    overdrive = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Allow GPU frequency/fan tuning (LACT / amdgpu overdrive)";
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
      libva-utils
    ]
    ++ lib.optional cfg.overdrive pkgs.lact;

    services.lact.enable = lib.mkIf cfg.overdrive true;

    boot.kernelParams = lib.mkAfter [ "amd_pstate=active" ];
  };
}
