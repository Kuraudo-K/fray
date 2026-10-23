use std::fs::File;
use std::io::{Read, Write};
use std::os::unix::fs::{OpenOptionsExt, PermissionsExt};
use std::path::{Path, PathBuf};
use std::process::{Command, Output, Stdio};
use std::thread;
use std::time::{Duration, Instant};

#[derive(Debug)]
pub enum CaptureError {
    Timeout,
    Spawn(std::io::Error),
}

pub fn which(name: &str) -> Option<PathBuf> {
    let path = std::env::var_os("PATH")?;
    for dir in std::env::split_paths(&path) {
        let candidate = dir.join(name);
        if is_executable(&candidate) {
            return Some(candidate);
        }
    }
    None
}

pub fn is_executable(path: &Path) -> bool {
    match path.metadata() {
        Ok(meta) => meta.is_file() && meta.permissions().mode() & 0o111 != 0,
        Err(_) => false,
    }
}

pub fn lossy(bytes: &[u8]) -> String {
    String::from_utf8_lossy(bytes).into_owned()
}

pub fn capture(mut cmd: Command, timeout: Duration) -> Result<Output, CaptureError> {
    cmd.stdout(Stdio::piped()).stderr(Stdio::piped());
    let mut child = cmd.spawn().map_err(CaptureError::Spawn)?;

    let stdout_handle = take_reader(child.stdout.take());
    let stderr_handle = take_reader(child.stderr.take());
    let status = wait_with_timeout(&mut child, timeout, &stdout_handle, &stderr_handle)?;

    Ok(Output {
        status,
        stdout: join_buf(stdout_handle),
        stderr: join_buf(stderr_handle),
    })
}

pub fn capture_with_input(
    mut cmd: Command,
    input: &[u8],
    timeout: Duration,
) -> Result<Output, CaptureError> {
    cmd.stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    let mut child = cmd.spawn().map_err(CaptureError::Spawn)?;
    if let Some(mut stdin) = child.stdin.take() {
        let _ = stdin.write_all(input);
    }
    let stdout_handle = take_reader(child.stdout.take());
    let stderr_handle = take_reader(child.stderr.take());
    let status = wait_with_timeout(&mut child, timeout, &stdout_handle, &stderr_handle)?;
    Ok(Output {
        status,
        stdout: join_buf(stdout_handle),
        stderr: join_buf(stderr_handle),
    })
}

fn take_reader(
    pipe: Option<impl Read + Send + 'static>,
) -> Option<thread::JoinHandle<Vec<u8>>> {
    pipe.map(|mut pipe| {
        thread::spawn(move || {
            let mut buf = Vec::new();
            let _ = pipe.read_to_end(&mut buf);
            buf
        })
    })
}

fn join_buf(handle: Option<thread::JoinHandle<Vec<u8>>>) -> Vec<u8> {
    handle
        .and_then(|handle| handle.join().ok())
        .unwrap_or_default()
}

fn wait_with_timeout(
    child: &mut std::process::Child,
    timeout: Duration,
    stdout: &Option<thread::JoinHandle<Vec<u8>>>,
    stderr: &Option<thread::JoinHandle<Vec<u8>>>,
) -> Result<std::process::ExitStatus, CaptureError> {
    let started = Instant::now();
    loop {
        match child.try_wait() {
            Ok(Some(status)) => return Ok(status),
            Ok(None) if started.elapsed() > timeout => {
                let _ = child.kill();
                let _ = child.wait();
                let _ = stdout.as_ref().map(|_| ());
                let _ = stderr.as_ref().map(|_| ());
                return Err(CaptureError::Timeout);
            }
            Ok(None) => thread::sleep(Duration::from_millis(50)),
            Err(err) => return Err(CaptureError::Spawn(err)),
        }
    }
}

pub fn write_private_script(body: &str) -> Result<PathBuf, std::io::Error> {
    let mut n = 0u32;
    loop {
        n += 1;
        let path = std::env::temp_dir().join(format!(
            "fray-um-askpass-{}-{n}.sh",
            std::process::id()
        ));
        match std::fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .mode(0o755)
            .open(&path)
        {
            Ok(mut file) => {
                file.write_all(body.as_bytes())?;
                let mut perms = file.metadata()?.permissions();
                perms.set_mode(0o755);
                std::fs::set_permissions(&path, perms)?;
                return Ok(path);
            }
            Err(err) if err.kind() == std::io::ErrorKind::AlreadyExists && n < 100 => continue,
            Err(err) => {
                if err.kind() != std::io::ErrorKind::InvalidInput {
                    return Err(err);
                }
                let mut file = File::create(&path)?;
                file.write_all(body.as_bytes())?;
                let mut perms = file.metadata()?.permissions();
                perms.set_mode(0o755);
                std::fs::set_permissions(&path, perms)?;
                return Ok(path);
            }
        }
    }
}

pub struct DeleteOnDrop(pub Option<PathBuf>);

impl Drop for DeleteOnDrop {
    fn drop(&mut self) {
        if let Some(path) = self.0.take() {
            let _ = std::fs::remove_file(path);
        }
    }
}

pub fn pkexec_write(path: &Path, data: &[u8]) -> Result<(), String> {
    let pkexec = if Path::new("/run/wrappers/bin/pkexec").is_file() {
        Path::new("/run/wrappers/bin/pkexec").to_path_buf()
    } else {
        which("pkexec").unwrap_or_else(|| Path::new("pkexec").to_path_buf())
    };
    let parent = path
        .parent()
        .map(|dir| dir.display().to_string())
        .unwrap_or_else(|| ".".to_string());
    let script = format!("mkdir -p \"{parent}\" && cat > \"{}\"", path.display());
    let mut cmd = Command::new(pkexec);
    cmd.args(["bash", "-c", &script]);
    match capture_with_input(cmd, data, Duration::from_secs(120)) {
        Ok(output) if output.status.success() => Ok(()),
        Ok(output) => {
            let err = lossy(&output.stderr);
            let err = if err.trim().is_empty() {
                lossy(&output.stdout)
            } else {
                err
            };
            let err = err.trim();
            if err.is_empty() {
                Err("pkexec a refusé l'écriture.".to_string())
            } else {
                Err(err.to_string())
            }
        }
        Err(CaptureError::Timeout) => Err("Délai dépassé pendant pkexec.".to_string()),
        Err(CaptureError::Spawn(err)) => Err(err.to_string()),
    }
}
