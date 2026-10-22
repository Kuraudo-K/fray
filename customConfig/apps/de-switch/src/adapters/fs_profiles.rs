use crate::adapters::{copy_tree, data_root, home_dir, remove_tree};
use crate::domain::{SessionId, SwitchError, SwitchResult};
use crate::ports::ProfileStore;
use std::fs;
use std::path::PathBuf;

pub struct FsProfileStore;

impl ProfileStore for FsProfileStore {
    fn profiles_root(&self) -> PathBuf {
        data_root().join("de-profiles")
    }

    fn save(&self, session: SessionId) -> SwitchResult<()> {
        let home = home_dir();
        let dest_root = self.profiles_root().join(session.as_str());
        fs::create_dir_all(&dest_root).map_err(|e| SwitchError::Io(e.to_string()))?;
        for entry in session.profile_entries() {
            let live = session.live_path(&home, entry);
            let dest = dest_root.join(entry.store_name);
            let _ = remove_tree(&dest);
            copy_tree(&live, &dest).map_err(|e| SwitchError::Io(e.to_string()))?;
            eprintln!(
                "[fray-de-switch] sauvé {} -> {}",
                live.display(),
                dest.display()
            );
        }
        Ok(())
    }

    fn restore(&self, session: SessionId) -> SwitchResult<()> {
        let home = home_dir();
        let src_root = self.profiles_root().join(session.as_str());
        if !src_root.exists() {
            eprintln!(
                "[fray-de-switch] aucun profil pour {} (première utilisation OK)",
                session.label()
            );
            return Ok(());
        }
        for entry in session.profile_entries() {
            let src = src_root.join(entry.store_name);
            if !src.exists() {
                continue;
            }
            let live = session.live_path(&home, entry);
            if let Some(parent) = live.parent() {
                fs::create_dir_all(parent).map_err(|e| SwitchError::Io(e.to_string()))?;
            }
            let _ = remove_tree(&live);
            copy_tree(&src, &live).map_err(|e| SwitchError::Io(e.to_string()))?;
            eprintln!(
                "[fray-de-switch] restauré {} ← {}",
                live.display(),
                src.display()
            );
        }
        Ok(())
    }

    fn has_profile(&self, session: SessionId) -> bool {
        self.profiles_root().join(session.as_str()).exists()
    }
}
