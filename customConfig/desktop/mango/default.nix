# MangoWM + DankMaterialShell (4ᵉ DE)
# Config système sans Home Manager - customs user via fray-de-switch (profil mango)
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.desktop.mangoDms;

  # Config minimale Fray (pas de moniteurs hardcodés mona)
  mangoConf = pkgs.writeText "mango-config.conf" ''
    # Fray - défauts Mango ; profils : ~/.config/mango (fray-de-switch)

    bind=SUPER,Return,spawn,kitty
    bind=SUPER,q,killclient
    bind=SUPER,d,spawn,dms ipc call spotlight toggle
    bind=SUPER,comma,spawn,dms ipc call settings toggle
    bind=SUPER,Escape,spawn,dms ipc call powermenu toggle
    bind=SUPER,v,spawn,dms ipc call clipboard toggle
    bind=SUPER+CTRL,s,spawn,dms ipc call control-center toggle

    bind=SUPER,1,view,1
    bind=SUPER,2,view,2
    bind=SUPER,3,view,3
    bind=SUPER,4,view,4
    bind=SUPER,5,view,5
    bind=SUPER+SHIFT,1,tag,1
    bind=SUPER+SHIFT,2,tag,2
    bind=SUPER+SHIFT,3,tag,3
    bind=SUPER+SHIFT,4,tag,4
    bind=SUPER+SHIFT,5,tag,5

    bind=SUPER,t,setlayout,tile
    bind=SUPER,f,togglefloating
    bind=SUPER+SHIFT,f,togglefullscreen
    bind=SUPER+CTRL+SHIFT,q,quit

    blur=0
    shadows=0
    border_radius=6
  '';
in
{
  options.fray.desktop.mangoDms = {
    enable = lib.mkEnableOption "MangoWM + DankMaterialShell (4th DE)";
  };

  config = lib.mkIf cfg.enable {
    programs.mango = {
      enable = true;
      addLoginEntry = true;
    };

    programs.dank-material-shell = {
      enable = true;
      systemd = {
        enable = true;
        restartIfChanged = true;
      };
      enableSystemMonitoring = true;
      enableDynamicTheming = true;
    };

    environment.etc."xdg/mango/config.conf".source = mangoConf;

    environment.systemPackages = with pkgs; [
      kitty
      wl-clipboard
      cliphist
      grim
      slurp
      playerctl
    ];

    environment.sessionVariables.NIXOS_OZONE_WL = "1";
  };
}
