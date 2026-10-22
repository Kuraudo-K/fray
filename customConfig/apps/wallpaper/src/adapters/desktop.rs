use crate::domain::DesktopKind;
use crate::ports::DesktopDetector;

pub struct EnvDesktopDetector;

impl DesktopDetector for EnvDesktopDetector {
    fn detect(&self) -> DesktopKind {
        let desktop = std::env::var("XDG_CURRENT_DESKTOP").unwrap_or_default();
        let session = std::env::var("XDG_SESSION_DESKTOP").unwrap_or_default();
        DesktopKind::detect(&desktop, &session)
    }
}
