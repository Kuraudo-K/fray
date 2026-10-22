//! Adapters - lsblk, udisksctl, outils DE

mod desktop_open;
mod lsblk;
mod udisks;

pub use desktop_open::WhichDesktopTool;
pub use lsblk::LsblkLister;
pub use udisks::UdisksMounter;
