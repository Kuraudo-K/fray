use crate::domain::{DesktopKind, WallpaperError, WallpaperResult};
use crate::ports::WallpaperApplier;
use std::process::Command;

pub struct PlasmaApplier;

impl WallpaperApplier for PlasmaApplier {
    fn apply(&self, desktop: DesktopKind, path: &str) -> WallpaperResult<()> {
        if desktop != DesktopKind::Plasma {
            return Err(WallpaperError::Unsupported(
                "PlasmaApplier réservé à Plasma".into(),
            ));
        }
        // plasma-apply-wallpaperimage (Plasma 5/6)
        let status = Command::new("plasma-apply-wallpaperimage")
            .arg(path)
            .status()
            .map_err(|e| WallpaperError::Io(format!(
                "plasma-apply-wallpaperimage introuvable : {e}"
            )))?;
        if !status.success() {
            return Err(WallpaperError::Io(format!(
                "plasma-apply-wallpaperimage a échoué ({status})"
            )));
        }
        Ok(())
    }

    fn current(&self, _desktop: DesktopKind) -> WallpaperResult<Option<String>> {
        // Plasma ne expose pas un getter CLI simple
        Ok(None)
    }
}
