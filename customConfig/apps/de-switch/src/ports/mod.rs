//! Ports — traits vers l'extérieur (fs, greeter, détection session)

use crate::domain::{SessionId, SwitchResult};
use std::path::PathBuf;

pub trait SessionDetector {
    fn current(&self) -> Option<SessionId>;
}

pub trait ProfileStore {
    fn profiles_root(&self) -> PathBuf;
    fn save(&self, session: SessionId) -> SwitchResult<()>;
    fn restore(&self, session: SessionId) -> SwitchResult<()>;
    fn has_profile(&self, session: SessionId) -> bool;
}

pub trait GreeterConfig {
    fn set_preferred(&self, session: SessionId) -> SwitchResult<()>;
}

pub trait StateStore {
    fn preferred(&self) -> Option<String>;
    fn last_saved(&self) -> Option<String>;
    fn set_preferred(&self, session: SessionId) -> SwitchResult<()>;
    fn set_last_saved(&self, session: SessionId) -> SwitchResult<()>;
}
