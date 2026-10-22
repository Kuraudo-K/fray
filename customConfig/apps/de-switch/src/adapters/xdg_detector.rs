use crate::domain::SessionId;
use crate::ports::SessionDetector;

pub struct XdgSessionDetector;

impl SessionDetector for XdgSessionDetector {
    fn current(&self) -> Option<SessionId> {
        let desk = std::env::var("XDG_CURRENT_DESKTOP").unwrap_or_default();
        SessionId::from_xdg_desktop(&desk)
    }
}
