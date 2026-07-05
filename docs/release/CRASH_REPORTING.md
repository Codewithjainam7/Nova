# NOVA Crash Reporting & Telemetry

## 1. Philosophy
Privacy is paramount. We explicitly guarantee that **no secrets, API keys, or conversation histories are ever transmitted** via telemetry.

## 2. Telemetry (`TelemetryManager`)
- **Opt-in Only:** By default, all telemetry is disabled. 
- **Data Collected:** Only high-level performance metrics (boot time, feature usage counts) and OS versions are sent to identify widespread degradation.

## 3. Crash Reports (`CrashReporter`)
If an unhandled exception manages to bubble up to the `Kernel` level:
1. The `CrashReporter` captures a minidump and stack trace.
2. The user is prompted with an error dialog offering to upload the dump for diagnosis.
3. The app attempts a graceful restart using the last known stable snapshot from the `SettingsBackupManager`.
