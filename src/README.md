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

## Build macOS On GitHub

If you do not have a Mac, use the GitHub Actions workflow at
`.github/workflows/build-macos.yml`.

It is pinned to:

- Python `3.12`
- Briefcase `0.3.25`

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
