# Chapter 32: Contributing Guidelines & Code Standards

## Contribution Workflow
1. Fork the repository on GitHub.
2. Create a feature branch: `git checkout -b feature/amazing-feature`.
3. Adhere to code style:
   - **Backend**: PEP8 compliance, strict type hints (`typing`), async/await standards.
   - **Frontend**: TypeScript strict mode, Tailwind CSS utility ordering, ESLint rules.
4. Run validation test suites: `python run_real_tests.py` & `npm run build`.
5. Submit a descriptive Pull Request with before/after logs.
