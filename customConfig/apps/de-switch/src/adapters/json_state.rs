use crate::adapters::data_root;
use crate::domain::{SessionId, SwitchError, SwitchResult};
use crate::ports::StateStore;
use serde::{Deserialize, Serialize};
use std::fs;

#[derive(Serialize, Deserialize, Default)]
struct StateFile {
    preferred: Option<String>,
    last_saved: Option<String>,
}

pub struct JsonStateStore;

impl JsonStateStore {
    fn path() -> std::path::PathBuf {
        data_root().join("de-state.json")
    }

    fn load() -> StateFile {
        fs::read_to_string(Self::path())
            .ok()
            .and_then(|s| serde_json::from_str(&s).ok())
            .unwrap_or_default()
    }

    fn save(st: &StateFile) -> SwitchResult<()> {
        fs::create_dir_all(data_root()).map_err(|e| SwitchError::Io(e.to_string()))?;
        let text = serde_json::to_string_pretty(st).map_err(|e| SwitchError::Io(e.to_string()))?;
        fs::write(Self::path(), text).map_err(|e| SwitchError::Io(e.to_string()))?;
        Ok(())
    }
}

impl StateStore for JsonStateStore {
    fn preferred(&self) -> Option<String> {
        Self::load().preferred
    }

    fn last_saved(&self) -> Option<String> {
        Self::load().last_saved
    }

    fn set_preferred(&self, session: SessionId) -> SwitchResult<()> {
        let mut st = Self::load();
        st.preferred = Some(session.as_str().into());
        Self::save(&st)
    }

    fn set_last_saved(&self, session: SessionId) -> SwitchResult<()> {
        let mut st = Self::load();
        st.last_saved = Some(session.as_str().into());
        Self::save(&st)
    }
}
