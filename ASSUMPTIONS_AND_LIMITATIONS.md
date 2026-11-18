# Assumptions and Limitations

1. All data is synthetic.
2. Financial operations are simulated for educational/portfolio purposes.
3. Thresholds are configurable project assumptions.
4. Data-quality scoring weights are project methodology, not industry standards.
5. SLA values are simulated.
6. No production banking/fund-accounting logic is represented.
7. No claim should be made that the application reflects State Street's internal systems.
8. Performance targets are approximate and should be measured rather than assumed.
9. Recommendations are rule-based analytical suggestions.
10. The platform is not a production financial-control system.

11. Default simulation as-of is 2026-09-30T18:00:00 UTC, independent of the actual wall clock. Aging and overdue metrics use simulation time. Actual ingestion/audit/report timestamps are UTC.
12. Default demo history is explicitly simulated. Detections are never placed before a valid source transaction date, and resolution times do not exceed as-of. Process-stage durations are synthesized allocations, not production telemetry.
13. Cross-currency amounts are never summed or converted. Nominal outlier thresholds across currencies are illustrative and not comparable economic materiality.
14. Exception history can remain after manual resolution; current source quality is measured separately. Root-cause labels derive from rule classes and are not proven causal explanations.
15. Backlog and exception trends group by origination day. They do not reconstruct historical stocks or detection-event counts. Invalid/missing source dates are excluded from temporal views but retained in unfiltered totals.
16. HTML was selected from the permitted PDF/HTML executive report choices. Offline interactive charts are embedded; direct PDF generation is not implemented. Browser print can produce PDF.
17. SQLite and the service layer target a trusted single-machine demo, without authentication, enterprise tenancy, orchestration or institutional controls. Future schema changes need explicit migrations.
18. Docker/Compose are provided but Docker runtime is unavailable on this host. Windows Python 3.12 is locally verified; Linux/Python 3.11 are covered by configured CI rather than claimed local execution.
19. Reports are reproducible in their calculated content, not byte-identical, because actual refresh timestamps and generated filenames vary. Generation records and injected defect manifests are deterministic.
