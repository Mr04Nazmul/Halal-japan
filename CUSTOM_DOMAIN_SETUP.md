# Custom domain setup — japanhalal.qzz.io

Status (2026-10-14): **NOT REGISTERED OR VERIFIED**. No GitHub Pages custom-domain setting or DNS change has been applied. Keep the current site https://mr04nazmul.github.io/Halal-japan/ working until domain registration and delegation are confirmed.

1. Sign in at https://dash.domain.digitalplat.org/ ; read current notices, suffix limits, and any slot/fee requirement. Choose `japanhalal` and `.qzz.io`; click **Check availability**. Availability cannot be inferred from the repository or a DNS lookup.
2. If eligible and free, create a zone for `japanhalal.qzz.io` at an authoritative DNS provider, and obtain that provider's actual assigned nameservers.
3. Return to DigitalPlat registration; submit those actual nameservers and register the exact domain. Confirm ownership/status in Domain List. Never put account credentials in this repository.
4. In GitHub's **Settings → Pages → Custom domain** for `Mr04Nazmul/Halal-japan`, enter `japanhalal.qzz.io` and Save **only after successful registration**. A custom GitHub Actions workflow may not need a root CNAME file.
5. At the external DNS provider, create a CNAME for the domain's apex `@` (or the label/hostname that the provider instructs) pointing to `mr04nazmul.github.io`. Some providers do not allow apex CNAME; use their supported CNAME flattening/ALIAS or equivalent, or consult their GitHub Pages instructions. **Never point to `mr04nazmul.github.io/Halal-japan`**.
6. Confirm DNS resolution and Pages certificate status; enable **Enforce HTTPS** when available. Check redirects and scanner camera HTTPS.
7. Do not remove existing GitHub Pages URL or unrelated application files.

Sources: https://github.com/DigitalPlatDev/FreeDomain/blob/main/documents/tutorial/platform/1.2-domain-registration.md
https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site

This document is instructions only; it does not constitute successful domain registration.
