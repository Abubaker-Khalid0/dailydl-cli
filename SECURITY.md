# Security policy

DailyDL CLI accepts only Dailymotion video URLs or IDs and normalizes them before extraction. It does not accept arbitrary media URLs, execute shell command strings, or use video titles as worker output paths.

The application supervises a separate yt-dlp worker and its FFmpeg children. Downloads are created in a unique temporary directory and published only after completion. Ctrl+C and the total deadline clean up partial files.

Run with normal user privileges. Upstream media, DNS, redirects and media decoders remain trust boundaries. Keep yt-dlp, curl-cffi and FFmpeg maintained. Domain checks are not a substitute for an OS/network sandbox. No cookie import, password authentication or DRM bypass workflow is provided.

Metadata output intentionally excludes signed CDN URLs. Do not attach cookies or credentials to bug reports. Report security issues privately through GitHub Security Advisories if enabled, or contact the repository owner privately. No response SLA is promised.
