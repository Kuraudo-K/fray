use std::sync::LazyLock;

use regex::Regex;

pub fn strip_ansi(text: &str) -> String {
    static RE: LazyLock<Regex> =
        LazyLock::new(|| Regex::new(r"\x1b\[[0-9;?]*[ -/]*[@-~]").expect("ansi regex"));
    RE.replace_all(text, "").into_owned()
}

pub fn short_msg(ok: bool, detail: &str, ok_text: &str, fail_text: &str) -> String {
    let detail = detail.trim();
    if ok {
        return ok_text.to_string();
    }
    if detail.is_empty() {
        return fail_text.to_string();
    }
    let mut first = detail.lines().next().unwrap_or("").trim().to_string();
    if first.chars().count() > 120 {
        first = first.chars().take(117).collect();
        first.push('…');
    }
    if first.is_empty() {
        fail_text.to_string()
    } else {
        format!("{fail_text} — {first}")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn strips_ansi_color() {
        let raw = "\u{1b}[31merreur\u{1b}[0m ok";
        assert_eq!(strip_ansi(raw), "erreur ok");
    }

    #[test]
    fn shortens_failure_to_first_line() {
        let detail = format!("{}\nsecond", "x".repeat(130));
        let msg = short_msg(false, &detail, "ok", "Échec");
        assert!(msg.starts_with("Échec — "));
        assert!(msg.ends_with('…'));
        assert!(msg.chars().count() <= "Échec — ".chars().count() + 118);
    }
}
