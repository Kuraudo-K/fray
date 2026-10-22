use crate::domain::{BlockDevice, BlockKind, DiskError, DiskResult};
use crate::ports::BlockLister;
use serde::Deserialize;
use std::process::Command;

pub struct LsblkLister;

#[derive(Debug, Deserialize)]
struct LsblkOut {
    blockdevices: Vec<LsblkNode>,
}

#[derive(Debug, Deserialize)]
struct LsblkNode {
    name: String,
    #[serde(default)]
    path: Option<String>,
    #[serde(default)]
    size: Option<String>,
    #[serde(default)]
    fstype: Option<String>,
    #[serde(default)]
    mountpoint: Option<String>,
    #[serde(default)]
    label: Option<String>,
    #[serde(rename = "type", default)]
    type_: Option<String>,
    #[serde(default)]
    children: Option<Vec<LsblkNode>>,
}

fn to_device(n: LsblkNode) -> BlockDevice {
    let path = n
        .path
        .unwrap_or_else(|| format!("/dev/{}", n.name));
    let kind = BlockKind::parse(n.type_.as_deref().unwrap_or(""));
    let children = n
        .children
        .unwrap_or_default()
        .into_iter()
        .map(to_device)
        .collect();
    BlockDevice {
        name: n.name,
        path,
        size: n.size.unwrap_or_else(|| "-".into()),
        fstype: n.fstype,
        mountpoint: n.mountpoint,
        label: n.label,
        kind,
        children,
    }
}

impl BlockLister for LsblkLister {
    fn list(&self) -> DiskResult<Vec<BlockDevice>> {
        let out = Command::new("lsblk")
            .args([
                "-J",
                "-o",
                "NAME,PATH,SIZE,FSTYPE,MOUNTPOINT,LABEL,TYPE",
            ])
            .output()
            .map_err(|e| DiskError::Io(format!("lsblk: {e}")))?;
        if !out.status.success() {
            return Err(DiskError::Io(format!(
                "lsblk exit {}: {}",
                out.status,
                String::from_utf8_lossy(&out.stderr)
            )));
        }
        let parsed: LsblkOut = serde_json::from_slice(&out.stdout)
            .map_err(|e| DiskError::Io(format!("parse lsblk JSON: {e}")))?;
        Ok(parsed.blockdevices.into_iter().map(to_device).collect())
    }
}
