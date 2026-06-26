import os
import re

from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineCore import QWebEngineUrlRequestInterceptor

FILTER_DIR = os.path.join(os.path.dirname(__file__), "resources", "easylist")

BUILTIN_RULES = [
    "||doubleclick.net^", "||googlesyndication.com^", "||googleadservices.com^",
    "||google-analytics.com^", "||googletagmanager.com^", "||adservice.google.com^",
    "||adnxs.com^", "||adsrvr.org^", "||advertising.com^", "||criteo.com^",
    "||outbrain.com^", "||taboola.com^", "||moatads.com^", "||pubmatic.com^",
    "||rubiconproject.com^", "||scorecardresearch.com^", "||quantserve.com^",
    "||amazon-adsystem.com^", "||hotjar.com^", "||mixpanel.com^", "||segment.io^",
    "||fullstory.com^", "||chartbeat.com^", "||facebook.com/tr^",
]


def _domain_rule_to_regex(rule: str) -> re.Pattern:
    domain = rule.lstrip("|").rstrip("^")
    domain = re.escape(domain)
    return re.compile(
        rf"^[a-z]+://([a-zA-Z0-9\-]+\.)*{domain}([/:?#]|$)", re.IGNORECASE
    )


class AdBlocker(QWebEngineUrlRequestInterceptor):
    def __init__(self, enabled: bool = True):
        super().__init__()
        self.enabled = enabled
        self._domain_patterns = []
        self._substring_rules = []
        self._whitelist_domains = set()
        self.blocked_count = 0
        self.load_filter_lists()

    def load_filter_lists(self):
        self._domain_patterns.clear()
        self._substring_rules.clear()
        self._whitelist_domains.clear()

        if os.path.isdir(FILTER_DIR):
            loaded = False
            for fname in os.listdir(FILTER_DIR):
                if not fname.endswith(".txt"):
                    continue
                try:
                    with open(os.path.join(FILTER_DIR, fname), encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            self._parse_rule(line.strip())
                    loaded = True
                except OSError:
                    pass
            if loaded:
                return

        for rule in BUILTIN_RULES:
            self._parse_rule(rule)

    def _parse_rule(self, line: str):
        if not line or line.startswith(("!", "[")):
            return
        if line.startswith("@@"):
            inner = line[2:]
            if inner.startswith("||"):
                self._whitelist_domains.add(inner.lstrip("|").split("^")[0].lower())
            return
        if line.startswith("||"):
            core = line.split("$")[0]
            try:
                self._domain_patterns.append(_domain_rule_to_regex(core))
            except re.error:
                pass
            return
        if line.startswith("|") or "##" in line or line.startswith("/"):
            return
        core = line.split("$")[0].strip()
        if core and len(core) > 3:
            self._substring_rules.append(core.lower())

    def interceptRequest(self, info):
        if not self.enabled:
            return
        url: QUrl = info.requestUrl()
        url_str = url.toString().lower()
        host = url.host().lower()

        if any(host == w or host.endswith("." + w) for w in self._whitelist_domains):
            return
        for pattern in self._domain_patterns:
            if pattern.search(url_str):
                info.block(True)
                self.blocked_count += 1
                return
        for fragment in self._substring_rules:
            if fragment in url_str:
                info.block(True)
                self.blocked_count += 1
                return

    def set_enabled(self, v: bool):
        self.enabled = v

    def rule_count(self) -> int:
        return len(self._domain_patterns) + len(self._substring_rules)
