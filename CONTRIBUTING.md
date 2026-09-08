# Contributing / 貢獻

1. Create a feature branch for normal contributions.
2. Keep integrations read-only unless a future design explicitly introduces controlled actions.
3. Add tests for adapters, authorization, tenant boundaries, and protocol behavior.
4. Run `make lint`, `make test`, and `make platform-check` before opening a pull request.
5. Keep Helm defaults compatible with a Restricted-style Pod Security posture.
6. Never commit real credentials, customer data, internal hostnames, private runbooks, or production DSNs.
7. Security-sensitive changes should include a regression test that demonstrates the expected denial path.
