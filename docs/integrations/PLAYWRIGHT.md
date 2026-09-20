# Playwright Integration

NOVA utilizes Playwright to automate an embedded Chromium (or edge) instance for full-fledged web interaction.

## Configuration
- `NOVA_BROWSER_HEADLESS`: Defaults to `true`. Can be set to `false` for visual debugging.
- `NOVA_DOWNLOADS_PATH`: Defaults to `downloads/`. Configures where exported PDFs and files are stored.

## Capabilities
- **Navigation**: Full `page.goto()`, `go_back()`, and `reload()` support.
- **DOM Interaction**: Precise `click`, `dblclick`, `fill`, `type`, and `hover` utilizing Playwright locators.
- **Persistence**: Tab and session state (cookies/cache) are maintained using `new_context()` until the user explicitly terminates the session.
- **Network**: Supports awaiting `networkidle` state to guarantee single-page applications have completed rendering before DOM queries are executed.

## Security
Playwright commands are orchestrated entirely through the `BrowserActionDispatcher`, ensuring all actions are vetted against the current `BrowserPermissionLevel` before hitting the Playwright API.
