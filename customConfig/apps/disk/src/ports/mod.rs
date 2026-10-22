//! Ports — lsblk, montage, ouverture outil DE

use crate::domain::{BlockDevice, DiskResult};

pub trait BlockLister {
    fn list(&self) -> DiskResult<Vec<BlockDevice>>;
}

pub trait Mounter {
    fn mount(&self, source: &str) -> DiskResult<()>;
    fn unmount(&self, target: &str) -> DiskResult<()>;
}

pub trait DesktopDiskTool {
    /// Lance l’outil disque du DE (lecture / gestion avancée)
    fn open(&self) -> DiskResult<()>;
}
