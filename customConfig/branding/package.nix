# Paquet branding Fray : logo charcoal-crimson, wallpaper, icônes session
{
  lib,
  stdenvNoCC,
  ...
}:

stdenvNoCC.mkDerivation {
  pname = "fray-branding";
  version = "1.1.0";

  src = ./assets;

  dontBuild = true;

  installPhase = ''
    runHook preInstall

    mkdir -p \
      $out/share/icons/hicolor/scalable/apps \
      $out/share/backgrounds/fray \
      $out/share/backgrounds/gnome \
      $out/share/gnome-background-properties \
      $out/share/pixmaps \
      $out/share/fray/logo

    # Icône officielle apps : 04gr10-charcoal-crimson (frost-leaf gray/red)
    cp logo/04gr10-charcoal-crimson.svg $out/share/icons/hicolor/scalable/apps/fray.svg
    cp logo/04gr10-charcoal-crimson.svg $out/share/icons/hicolor/scalable/apps/fray-logo.svg
    cp logo/04gr10-charcoal-crimson.svg $out/share/icons/hicolor/scalable/apps/fray-apply.svg
    cp logo/04gr10-charcoal-crimson.png $out/share/pixmaps/fray.png
    cp logo/04gr10-charcoal-crimson.png $out/share/fray/logo/fray-icon.png
    cp logo/04gr10-charcoal-crimson.svg $out/share/fray/logo/fray-icon.svg
    cp logo/04gr10-charcoal-crimson.png $out/share/fray/logo/04gr10-charcoal-crimson.png
    cp logo/04gr10-charcoal-crimson.svg $out/share/fray/logo/04gr10-charcoal-crimson.svg

    # Archive seal (référence historique, non utilisée comme icône apps)
    if [ -f logo/10-seal-fray.png ]; then
      cp logo/10-seal-fray.png $out/share/fray/logo/10-seal-fray.png
      cp logo/10-seal-fray.svg $out/share/fray/logo/10-seal-fray.svg
    fi

    for SIZE in 16 32 48 64 128 256 512; do
      mkdir -p $out/share/icons/hicolor/''${SIZE}x''${SIZE}/apps
      mkdir -p $out/share/icons/hicolor/''${SIZE}x''${SIZE}/emblems
      if [ -f logo/fray-logo-$SIZE.png ]; then
        cp logo/fray-logo-$SIZE.png \
          $out/share/icons/hicolor/''${SIZE}x''${SIZE}/apps/fray.png
        cp logo/fray-logo-$SIZE.png \
          $out/share/icons/hicolor/''${SIZE}x''${SIZE}/apps/fray-apply.png
        cp logo/fray-logo-$SIZE.png \
          $out/share/icons/hicolor/''${SIZE}x''${SIZE}/apps/fray-de-switch.png
        cp logo/fray-logo-$SIZE.png \
          $out/share/icons/hicolor/''${SIZE}x''${SIZE}/apps/fray-disk.png
        cp logo/fray-logo-$SIZE.png \
          $out/share/icons/hicolor/''${SIZE}x''${SIZE}/apps/fray-wallpaper.png
        cp logo/fray-logo-$SIZE.png \
          $out/share/icons/hicolor/''${SIZE}x''${SIZE}/emblems/fray-logo.png
      fi
    done

    cp wallpaper/fray-gaming-arena.png $out/share/backgrounds/fray/
    cp wallpaper/fray-gaming-arena.png $out/share/backgrounds/gnome/fray-gaming-arena.png

    # KDE wallpaper package
    mkdir -p $out/share/wallpapers/FrayGaming/contents/images
    cp wallpaper/fray-gaming-arena.png \
      $out/share/wallpapers/FrayGaming/contents/images/2560x1440.png
    cat > $out/share/wallpapers/FrayGaming/metadata.json <<'EOF'
{
  "KPlugin": {
    "Id": "FrayGaming",
    "Name": "Fray Gaming Arena",
    "Authors": [ { "Name": "Fray" } ],
    "License": "MIT",
    "Website": "https://github.com/Kuraudo-K/fray"
  }
}
EOF

    cat > $out/share/gnome-background-properties/fray-gaming.xml <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE wallpapers SYSTEM "gnome-wp-list.dtd">
<wallpapers>
  <wallpaper deleted="false">
    <name>Fray Gaming Arena</name>
    <filename>/run/current-system/sw/share/backgrounds/gnome/fray-gaming-arena.png</filename>
    <filename-dark>/run/current-system/sw/share/backgrounds/gnome/fray-gaming-arena.png</filename-dark>
    <options>zoom</options>
    <shade_type>solid</shade_type>
    <pcolor>#1F1F1F</pcolor>
    <scolor>#1F1F1F</scolor>
  </wallpaper>
</wallpapers>
EOF

    runHook postInstall
  '';

  meta = {
    description = "Fray logos (charcoal-crimson), emblems and wallpapers";
    license = lib.licenses.mit;
    platforms = lib.platforms.linux;
  };
}
