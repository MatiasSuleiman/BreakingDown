# BreakingDown

Desktop app to log into Gmail, search/filter mails, and export breakdown spreadsheets (`.xlsx`).

## Run Locally

```bash
python3 main.py
```

## Briefcase Commands

```bash
python3 -m briefcase create
python3 -m briefcase build
python3 -m briefcase package
```

On Apple Silicon Macs, this project builds an arm64-only macOS app. Keep the
project in a path without spaces before running Briefcase commands, for example
`~/Projects/BreakingDown/src`.

## Build macOS On GitHub

If you do not have a Mac, use the GitHub Actions workflow at
`.github/workflows/build-macos.yml`.

It is pinned to:

- Python `3.12`
- Briefcase `0.3.25`

Before running the workflow, create a GitHub Actions secret named
`GOOGLE_CLIENT_SECRET_JSON_B64` with the base64-encoded contents of your Google
OAuth client secret JSON.

Run it from the GitHub Actions tab with `workflow_dispatch`, then download the
artifact named `breakingdown-macos`.

## Google OAuth Files

The packaged app does not save the Google token next to the executable.

- Linux: `~/.config/breakingdown/google_oauth_token.json`
- macOS: `~/Library/Application Support/breakingdown/google_oauth_token.json`
- Windows: `%APPDATA%\\breakingdown\\google_oauth_token.json`

You can override these paths with:

- `BREAKINGDOWN_GOOGLE_CLIENT_SECRETS_FILE`
- `BREAKINGDOWN_CONFIG_DIR`
- `BREAKINGDOWN_GOOGLE_TOKEN_FILE`
