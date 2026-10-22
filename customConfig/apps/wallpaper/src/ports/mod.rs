//! Ports - inventaire, application DE, détection bureau

use crate::domain::{DesktopKind, Wallpaper, WallpaperResult};

pub trait WallpaperCatalog {
    fn list(&self) -> WallpaperResult<Vec<Wallpaper>>;
}

pub trait WallpaperApplier {
    fn apply(&self, desktop: DesktopKind, path: &str) -> WallpaperResult<()>;
    fn current(&self, desktop: DesktopKind) -> WallpaperResult<Option<String>>;
}

pub trait DesktopDetector {
    fn detect(&self) -> DesktopKind;
}
