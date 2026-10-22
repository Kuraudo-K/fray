//! Adapters — filesystem, env, greeter ~/.dmrc

mod fs_profiles;
mod greeter_dmrc;
mod json_state;
mod xdg_detector;

pub use fs_profiles::FsProfileStore;
pub use greeter_dmrc::DmrcGreeter;
pub use json_state::JsonStateStore;
pub use xdg_detector::XdgSessionDetector;

use std::fs;
use std::io;
use std::path::{Path, PathBuf};

pub(crate) fn home_dir() -> PathBuf {
    dirs::home_dir().expect("HOME")
}

pub(crate) fn data_root() -> PathBuf {
    dirs::data_local_dir()
        .unwrap_or_else(|| PathBuf::from(".").join(".local/share"))
        .join("fray")
}

pub(crate) fn copy_tree(src: &Path, dst: &Path) -> io::Result<()> {
    if !src.exists() {
        return Ok(());
    }
    if src.is_file() {
        if let Some(parent) = dst.parent() {
            fs::create_dir_all(parent)?;
        }
        fs::copy(src, dst)?;
        return Ok(());
    }
    fs::create_dir_all(dst)?;
    for entry in fs::read_dir(src)? {
        let entry = entry?;
        let ty = entry.file_type()?;
        let to = dst.join(entry.file_name());
        if ty.is_dir() {
            copy_tree(&entry.path(), &to)?;
        } else if ty.is_file() {
            fs::copy(entry.path(), &to)?;
        }
    }
    Ok(())
}

pub(crate) fn remove_tree(path: &Path) -> io::Result<()> {
    if path.is_dir() {
        fs::remove_dir_all(path)?;
    } else if path.is_file() {
        fs::remove_file(path)?;
    }
    Ok(())
}
