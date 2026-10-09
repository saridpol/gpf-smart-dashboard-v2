# GPF Smart Dashboard V2 — Complete Project

Android WebView dashboard with local SVG charts and offline NAV fallback.

## Data integrity
- Member account figures are starter/sample values and must be checked against a current statement.
- Shariah 100% is the real-plan reference. Aggressive 35, Aggressive 65 and Foreign Equity are shadow portfolios only.
- The app never calculates the member's real balance from shadow portfolios.
- The app reports verified NAV only if the JSON explicitly says `verified: true`; successful download alone is not proof of freshness.
- If the online file cannot be read, it uses the locally saved NAV or bundled starter values and visibly reports fallback status.
- The scraper may need adjustment if the GPF website changes. Inspect NAV values before relying on them.

## Repository contents
- `app/src/main/assets/index.html`: dashboard, responsive UI, charts.
- `app/src/main/assets/config.js`: URL for the repository's `nav-data.json`.
- `app/src/main/res/mipmap-*`: new launcher icon.
- `scripts/fetch_gpf_nav.py`: tries official page and preserves fallback on failure.
- `.github/workflows/build-apk.yml`: Android APK build.
- `.github/workflows/update-nav.yml`: manual/scheduled NAV update.
- `nav-data.json`: remote NAV payload.

## Install to a new GitHub repository
Create a public repository named `gpf-smart-dashboard-v2`, then upload the *contents* of this folder to the repository root, including `.github`. Check the account/repository URL in `app/src/main/assets/config.js`.

## Build APK
GitHub → Actions → `Build Android APK V2` → `Run workflow` on `main`. When successful, download artifact `gpf-smart-dashboard-v2-apk`, extract it and install the APK.

## Update NAV
`Update GPF NAV V2` runs manually or weekdays at 20:30 Thailand time (13:30 UTC). Green workflow means the script completed; inspect `nav-data.json` fields `verified`, `date`, and `fetch_error` to determine whether fresh NAV was actually found.

## Charts
SVG charts run locally without a CDN. They compare NAV start and latest points; they do not invent daily history.
