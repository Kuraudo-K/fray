//! Cas d'usage - orchestre domain + ports

use crate::domain::{SessionId, SwitchError, SwitchResult};
use crate::ports::{GreeterConfig, ProfileStore, SessionDetector, StateStore};

pub struct SwitchService<'a> {
    pub detector: &'a dyn SessionDetector,
    pub profiles: &'a dyn ProfileStore,
    pub greeter: &'a dyn GreeterConfig,
    pub state: &'a dyn StateStore,
}

#[derive(Debug, Clone)]
pub struct ListInfo {
    pub current: Option<SessionId>,
    pub preferred: Option<String>,
    pub last_saved: Option<String>,
    pub profiles_root: String,
}

impl<'a> SwitchService<'a> {
    pub fn list(&self) -> ListInfo {
        ListInfo {
            current: self.detector.current(),
            preferred: self.state.preferred(),
            last_saved: self.state.last_saved(),
            profiles_root: self.profiles.profiles_root().display().to_string(),
        }
    }

    pub fn list_json(&self) -> String {
        let info = self.list();
        let sessions: Vec<_> = SessionId::all()
            .into_iter()
            .map(|de| {
                serde_json::json!({
                    "id": de.as_str(),
                    "label": de.label(),
                    "greeter": de.greeter_id(),
                    "has_profile": self.profiles.has_profile(de),
                })
            })
            .collect();
        serde_json::json!({
            "sessions": sessions,
            "current": info.current.map(|d| d.as_str()),
            "preferred": info.preferred,
            "last_saved": info.last_saved,
            "profiles_root": info.profiles_root,
        })
        .to_string()
    }

    pub fn save(&self, session: Option<SessionId>) -> SwitchResult<SessionId> {
        let session = session
            .or_else(|| self.detector.current())
            .ok_or_else(|| SwitchError::UnknownSession("(courant inconnu)".into()))?;
        self.profiles.save(session)?;
        self.state.set_last_saved(session)?;
        Ok(session)
    }

    pub fn restore(&self, session: SessionId) -> SwitchResult<()> {
        self.profiles.restore(session)
    }

    pub fn switch(&self, to: SessionId) -> SwitchResult<()> {
        if let Some(cur) = self.detector.current() {
            if cur != to {
                self.profiles.save(cur)?;
                self.state.set_last_saved(cur)?;
            }
        }
        self.profiles.restore(to)?;
        self.greeter.set_preferred(to)?;
        self.state.set_preferred(to)?;
        Ok(())
    }

    pub fn explain(&self) -> String {
        r#"Mécanisme / Mechanism
=====================
Profils : ~/.local/share/fray/de-profiles/{gnome,niri,plasma,mango}/

  gnome  -> dconf, paperwm, extensions gnome-shell
  niri   -> ~/.config/niri, ~/.config/noctalia
  plasma -> plasma*/kwin*/kdeglobals, dolphin/konsole,
           ~/.local/share/{plasma,kwin,konsole}
  mango  -> ~/.config/mango, DankMaterialShell, quickshell

switch <de> :
  1. sauve le DE courant
  2. restaure le profil cible
  3. écrit ~/.dmrc + AccountsService (fray-set-session)

GDM relit Session= au prochain login (persiste après reboot).
Chaque DE garde ses customs.
"#
        .to_string()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::cell::RefCell;
    use std::collections::HashMap;
    use std::path::PathBuf;

    struct MemDetector(Option<SessionId>);
    impl SessionDetector for MemDetector {
        fn current(&self) -> Option<SessionId> {
            self.0
        }
    }

    struct MemProfiles {
        saved: RefCell<HashMap<&'static str, bool>>,
    }
    impl ProfileStore for MemProfiles {
        fn profiles_root(&self) -> PathBuf {
            PathBuf::from("/tmp/fray-test-profiles")
        }
        fn save(&self, session: SessionId) -> SwitchResult<()> {
            self.saved.borrow_mut().insert(session.as_str(), true);
            Ok(())
        }
        fn restore(&self, _session: SessionId) -> SwitchResult<()> {
            Ok(())
        }
        fn has_profile(&self, session: SessionId) -> bool {
            self.saved.borrow().get(session.as_str()).copied().unwrap_or(false)
        }
    }

    struct MemGreeter {
        preferred: RefCell<Option<SessionId>>,
    }
    impl GreeterConfig for MemGreeter {
        fn set_preferred(&self, session: SessionId) -> SwitchResult<()> {
            *self.preferred.borrow_mut() = Some(session);
            Ok(())
        }
    }

    struct MemState {
        preferred: RefCell<Option<String>>,
        last_saved: RefCell<Option<String>>,
    }
    impl StateStore for MemState {
        fn preferred(&self) -> Option<String> {
            self.preferred.borrow().clone()
        }
        fn last_saved(&self) -> Option<String> {
            self.last_saved.borrow().clone()
        }
        fn set_preferred(&self, session: SessionId) -> SwitchResult<()> {
            *self.preferred.borrow_mut() = Some(session.as_str().into());
            Ok(())
        }
        fn set_last_saved(&self, session: SessionId) -> SwitchResult<()> {
            *self.last_saved.borrow_mut() = Some(session.as_str().into());
            Ok(())
        }
    }

    #[test]
    fn switch_saves_current_then_sets_target() {
        let detector = MemDetector(Some(SessionId::Gnome));
        let profiles = MemProfiles {
            saved: RefCell::new(HashMap::new()),
        };
        let greeter = MemGreeter {
            preferred: RefCell::new(None),
        };
        let state = MemState {
            preferred: RefCell::new(None),
            last_saved: RefCell::new(None),
        };
        let svc = SwitchService {
            detector: &detector,
            profiles: &profiles,
            greeter: &greeter,
            state: &state,
        };
        svc.switch(SessionId::Plasma).unwrap();
        assert!(profiles.has_profile(SessionId::Gnome));
        assert_eq!(*greeter.preferred.borrow(), Some(SessionId::Plasma));
        assert_eq!(state.preferred().as_deref(), Some("plasma"));
    }
}
