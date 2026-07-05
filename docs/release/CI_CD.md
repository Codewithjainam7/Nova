# NOVA CI/CD Pipeline

## 1. Automated Workflows
All commits pushed to the `main` branch trigger a stringent GitHub Actions pipeline:
1. **Linting (`flake8` / `mypy`)**: Ensures static typing compliance.
2. **Quality Assurance (`pytest`)**: Runs the `QualityPlatform` tests. If coverage drops below 90%, the build fails.
3. **Security Audit**: Scans dependencies for known CVEs.
4. **Compilation**: Packages the `InstallerGenerator` outputs.
5. **Release Distribution**: Pushes the `.exe` to the GitHub Releases page automatically.
