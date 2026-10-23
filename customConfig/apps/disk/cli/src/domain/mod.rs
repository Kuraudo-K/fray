//! Domaine : blocs / partitions - zéro I/O

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BlockDevice {
    pub name: String,
    pub path: String,
    pub size: String,
    pub fstype: Option<String>,
    pub mountpoint: Option<String>,
    pub label: Option<String>,
    pub kind: BlockKind,
    pub children: Vec<BlockDevice>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BlockKind {
    Disk,
    Part,
    Other,
}

impl BlockKind {
    pub fn parse(type_str: &str) -> Self {
        match type_str {
            "disk" => Self::Disk,
            "part" => Self::Part,
            _ => Self::Other,
        }
    }

    pub fn as_str(self) -> &'static str {
        match self {
            Self::Disk => "disk",
            Self::Part => "part",
            Self::Other => "other",
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DiskError {
    Io(String),
    NotFound(String),
    Refused(String),
}

impl std::fmt::Display for DiskError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Io(s) | Self::NotFound(s) | Self::Refused(s) => write!(f, "{s}"),
        }
    }
}

impl std::error::Error for DiskError {}

pub type DiskResult<T> = Result<T, DiskError>;

/// Formate une ligne lisible (règle pure)
pub fn format_row(dev: &BlockDevice, indent: usize) -> String {
    let pad = "  ".repeat(indent);
    let fs = dev.fstype.as_deref().unwrap_or("-");
    let mnt = dev.mountpoint.as_deref().unwrap_or("-");
    let label = dev
        .label
        .as_deref()
        .map(|l| format!(" [{l}]"))
        .unwrap_or_default();
    format!(
        "{pad}{:<12} {:>8}  {:<8}  {}{}",
        dev.name, dev.size, fs, mnt, label
    )
}

pub fn find_by_name<'a>(devices: &'a [BlockDevice], name: &str) -> Option<&'a BlockDevice> {
    for d in devices {
        if d.name == name || d.path == name || d.path.ends_with(&format!("/{name}")) {
            return Some(d);
        }
        if let Some(found) = find_by_name(&d.children, name) {
            return Some(found);
        }
    }
    None
}

/// Interdit les cibles clairement dangereuses pour mount/umount CLI
pub fn assert_safe_target(path: &str) -> DiskResult<()> {
    let p = path.trim();
    if p.is_empty() || p == "/" || p == "/boot" || p == "/nix" || p.starts_with("/nix/") {
        return Err(DiskError::Refused(format!(
            "cible refusée (trop sensible) : {path}"
        )));
    }
    if !(p.starts_with("/dev/") || p.starts_with('/')) {
        return Err(DiskError::Refused(format!(
            "chemin invalide (attends /dev/… ou un point de montage) : {path}"
        )));
    }
    Ok(())
}

/// FS gérés pour la génération Nix (ext4, btrfs + compatibles courants)
pub fn is_nix_fstype(fs: &str) -> bool {
    matches!(
        fs.to_lowercase().as_str(),
        "ext4" | "ext3" | "ext2" | "btrfs" | "xfs" | "f2fs" | "vfat" | "fat32" | "exfat" | "ntfs" | "ntfs3"
    )
}

fn escape_nix_string(s: &str) -> String {
    s.replace('\\', "\\\\").replace('"', "\\\"")
}

fn flatten_devices<'a>(devices: &'a [BlockDevice], out: &mut Vec<&'a BlockDevice>) {
    for d in devices {
        out.push(d);
        flatten_devices(&d.children, out);
    }
}

/// Entrées fileSystems pour partitions montées avec FS connu.
/// Ne génère pas de wipe/format. Racine /boot /nix incluses en commentaire si demandées.
pub fn generate_nix_filesystems(devices: &[BlockDevice], include_system: bool) -> String {
    let mut flat = Vec::new();
    flatten_devices(devices, &mut flat);

    let mut body = String::from(
        "# Généré par fray-disk - à importer dans la config Fray\n\
         # Ne pas coller dans /etc/nixos de l'hôte GLF.\n\
         {\n",
    );

    let mut count = 0usize;
    for d in flat {
        let Some(mnt) = d.mountpoint.as_deref().filter(|m| !m.is_empty() && *m != "[SWAP]") else {
            continue;
        };
        let Some(fs) = d.fstype.as_deref().filter(|f| !f.is_empty()) else {
            continue;
        };
        if !is_nix_fstype(fs) {
            body.push_str(&format!(
                "  # skip {} ({}) FS non géré: {}\n",
                d.path, mnt, fs
            ));
            continue;
        }
        let is_system = mnt == "/" || mnt == "/boot" || mnt == "/boot/efi" || mnt.starts_with("/nix");
        if is_system && !include_system {
            body.push_str(&format!(
                "  # système non inclus : {mnt} ({})\n",
                d.path
            ));
            continue;
        }
        let fs_out = match fs.to_lowercase().as_str() {
            "fat32" | "vfat" => "vfat".to_string(),
            "ntfs" | "ntfs3" => "ntfs".to_string(),
            _ => fs.to_string(),
        };
        body.push_str(&format!(
            "  fileSystems.\"{}\" = {{\n    device = \"{}\";\n    fsType = \"{}\";\n  }};\n",
            escape_nix_string(mnt),
            escape_nix_string(&d.path),
            escape_nix_string(&fs_out)
        ));
        count += 1;
    }

    if count == 0 {
        body.push_str("  # aucune partition montée éligible\n");
    }
    body.push_str("}\n");
    body
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn kind_parse() {
        assert_eq!(BlockKind::parse("disk"), BlockKind::Disk);
        assert_eq!(BlockKind::parse("part"), BlockKind::Part);
    }

    #[test]
    fn safe_target_blocks_root() {
        assert!(assert_safe_target("/").is_err());
        assert!(assert_safe_target("/dev/sdb1").is_ok());
    }

    #[test]
    fn find_nested() {
        let tree = vec![BlockDevice {
            name: "sda".into(),
            path: "/dev/sda".into(),
            size: "100G".into(),
            fstype: None,
            mountpoint: None,
            label: None,
            kind: BlockKind::Disk,
            children: vec![BlockDevice {
                name: "sda1".into(),
                path: "/dev/sda1".into(),
                size: "50G".into(),
                fstype: Some("ext4".into()),
                mountpoint: Some("/".into()),
                label: None,
                kind: BlockKind::Part,
                children: vec![],
            }],
        }];
        assert!(find_by_name(&tree, "sda1").is_some());
        assert!(find_by_name(&tree, "/dev/sda").is_some());
    }

    #[test]
    fn gen_nix_skips_system_by_default() {
        let tree = vec![BlockDevice {
            name: "sda".into(),
            path: "/dev/sda".into(),
            size: "100G".into(),
            fstype: None,
            mountpoint: None,
            label: None,
            kind: BlockKind::Disk,
            children: vec![
                BlockDevice {
                    name: "sda1".into(),
                    path: "/dev/sda1".into(),
                    size: "50G".into(),
                    fstype: Some("ext4".into()),
                    mountpoint: Some("/".into()),
                    label: None,
                    kind: BlockKind::Part,
                    children: vec![],
                },
                BlockDevice {
                    name: "sda2".into(),
                    path: "/dev/sda2".into(),
                    size: "20G".into(),
                    fstype: Some("btrfs".into()),
                    mountpoint: Some("/mnt/data".into()),
                    label: Some("data".into()),
                    kind: BlockKind::Part,
                    children: vec![],
                },
            ],
        }];
        let nix = generate_nix_filesystems(&tree, false);
        assert!(nix.contains("/mnt/data"));
        assert!(nix.contains("btrfs"));
        assert!(nix.contains("système non inclus"));
        assert!(!nix.contains("fileSystems.\"/\""));
    }
}
