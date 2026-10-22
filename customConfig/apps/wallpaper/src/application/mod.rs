//! Cas d'usage wallpaper

use crate::domain::{find_by_id, DesktopKind, Wallpaper, WallpaperError, WallpaperResult};
use crate::ports::{DesktopDetector, WallpaperApplier, WallpaperCatalog};

pub struct WallpaperService<'a> {
    pub catalog: &'a dyn WallpaperCatalog,
    pub applier: &'a dyn WallpaperApplier,
    pub desktop: &'a dyn DesktopDetector,
}

impl<'a> WallpaperService<'a> {
    pub fn list(&self) -> WallpaperResult<Vec<Wallpaper>> {
        self.catalog.list()
    }

    pub fn list_text(&self) -> WallpaperResult<String> {
        let items = self.list()?;
        let mut out = String::from("ID                      SOURCE   PATH\n");
        for w in items {
            out.push_str(&format!(
                "{:<24} {:<8} {}\n",
                w.id,
                w.source.as_str(),
                w.path
            ));
        }
        Ok(out)
    }

    pub fn set(&self, id_or_path: &str) -> WallpaperResult<()> {
        let items = self.list()?;
        let path = if std::path::Path::new(id_or_path).is_file() {
            id_or_path.to_string()
        } else {
            find_by_id(&items, id_or_path)
                .ok_or_else(|| WallpaperError::NotFound(format!("introuvable : {id_or_path}")))?
                .path
                .clone()
        };
        let desk = self.desktop.detect();
        self.applier.apply(desk, &path)?;
        Ok(())
    }

    pub fn current_text(&self) -> WallpaperResult<String> {
        let desk = self.desktop.detect();
        let cur = self.applier.current(desk)?;
        Ok(format!(
            "desktop: {}\ncurrent: {}\n",
            desk.as_str(),
            cur.unwrap_or_else(|| "-".into())
        ))
    }

    pub fn desktop_kind(&self) -> DesktopKind {
        self.desktop.detect()
    }

    pub fn explain(&self) -> String {
        r#"fray-wallpaper - fonds d'écran Fray (hexagonal)
==============================================
list                 inventaire Fray / système / ~/Images
set <id|chemin>      applique selon le DE (gsettings / plasma / swww)
current              fond actuel + DE détecté
explain              cette aide

Assets Fray : $FRAY_BRANDING/share/backgrounds/fray/
"#
        .into()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::domain::{Wallpaper, WallpaperSource};
    use std::cell::RefCell;

    struct MemCatalog(Vec<Wallpaper>);
    impl WallpaperCatalog for MemCatalog {
        fn list(&self) -> WallpaperResult<Vec<Wallpaper>> {
            Ok(self.0.clone())
        }
    }

    struct MemApplier {
        applied: RefCell<Vec<String>>,
    }
    impl WallpaperApplier for MemApplier {
        fn apply(&self, _d: DesktopKind, path: &str) -> WallpaperResult<()> {
            self.applied.borrow_mut().push(path.into());
            Ok(())
        }
        fn current(&self, _d: DesktopKind) -> WallpaperResult<Option<String>> {
            Ok(self.applied.borrow().last().cloned())
        }
    }

    struct MemDesk;
    impl DesktopDetector for MemDesk {
        fn detect(&self) -> DesktopKind {
            DesktopKind::Gnome
        }
    }

    #[test]
    fn set_by_id() {
        let cat = MemCatalog(vec![Wallpaper {
            id: "fray-gaming-arena".into(),
            path: "/tmp/fray-gaming-arena.png".into(),
            source: WallpaperSource::Fray,
        }]);
        let app = MemApplier {
            applied: RefCell::new(vec![]),
        };
        let desk = MemDesk;
        let svc = WallpaperService {
            catalog: &cat,
            applier: &app,
            desktop: &desk,
        };
        svc.set("fray-gaming-arena").unwrap();
        assert_eq!(
            app.applied.borrow().as_slice(),
            ["/tmp/fray-gaming-arena.png"]
        );
    }
}
