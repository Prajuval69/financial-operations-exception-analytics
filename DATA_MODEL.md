# Data Model

## Transaction

Fields:
- transaction_id
- account_id
- business_unit_id
- source_system_id
- transaction_date
- processing_date
- transaction_type
- amount
- currency
- status
- priority
- team_id
- owner
- reference_code
- created_at
- updated_at

## Account

- account_id
- account_type
- business_unit_id
- country
- currency
- status
- created_at

## Processing Event

- event_id
- transaction_id
- stage
- event_timestamp
- team_id
- status
- duration_minutes
- exception_flag

## Exception

- exception_id
- transaction_id
- rule_code
- category
- description
- severity
- priority
- status
- root_cause
- business_impact
- owner
- detected_at
- due_date
- resolved_at
- resolution_notes

## Action

- action_id
- exception_id
- title
- description
- owner
- priority
- due_date
- status
- dependency
- created_at
- completed_at

## Risk

- risk_id
- related_exception_id
- title
- description
- probability
- impact
- risk_score
- owner
- status
- mitigation
- due_date

## Reference data

Include controlled values for:
- currencies
- countries
- transaction types
- teams
- business units
- source systems
- statuses
- priorities
- exception categories

## Implemented persistence notes

`Transaction.id` is the internal row identity; external transaction_id remains nullable/nonunique for validation. Source amount/date/reference values remain text and `raw` contains original input. `transaction_day` is a nullable normalized UTC day derived for correct SQL date filtering. `rework` is a Boolean analytical field.

Processing events link `record_id` to the internal transaction row. Exceptions add source_entity/source_record_id, record_id and suggested_action; uniqueness is source entity + source identity + rule. Actions have an optional self-reference dependency. Risks can link to an action as well as an exception. Reference kinds include business units, teams, sources, currencies, countries, statuses, priorities, types and exception categories.

Additional tables: dataset_meta stores seed, source, simulation as-of and actual ingestion time; validation_runs stores summary and policy snapshots; audit_events stores entity identity, actual timestamp and before/after differences. The synchronized `DATA_DICTIONARY.md` and `docs/data_dictionary.csv` enumerate all persisted fields.
