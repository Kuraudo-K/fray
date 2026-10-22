{
  stdenvNoCC,
  lib,
}:

stdenvNoCC.mkDerivation {
  pname = "plymouth-fray";
  version = "1.0.0";

  src = ./.;

  dontBuild = true;

  installPhase = ''
    runHook preInstall
    mkdir -p $out/share/plymouth/themes/fray
    cp fray.plymouth fray.script logo.png progress-*.png \
      $out/share/plymouth/themes/fray/
    substituteInPlace $out/share/plymouth/themes/fray/fray.plymouth \
      --replace-fail "/usr/" "$out/"
    runHook postInstall
  '';

  meta = {
    description = "Fray Plymouth boot theme (logo 10 seal)";
    license = lib.licenses.mit;
    platforms = lib.platforms.linux;
  };
}
