\# Benchmark: Cumulative Table Design vs Rescan for User Activity Arrays using DuckDB



\## 1. Overview



This project implements and benchmarks two data engineering architectures for daily user activity metrics:



1\. Trailing-window Rescan Pipeline

2\. Cumulative Table Pipeline using bounded state arrays



The metrics include:



\* DAU

\* WAU

\* MAU

\* 30-day likes

\* 30-day comments

\* 30-day shares



The project uses Python, DuckDB, Pandas, NumPy, and Parquet.



The experiment compares the amount of data scanned and execution time as the window length changes.



\---



\## 2. Architecture



\### Rescan



```text

Daily Parquet Events

&#x20;       |

&#x20;       v

Trailing W-Day Scan

&#x20;       |

&#x20;       v

GROUP BY user\_id

&#x20;       |

&#x20;       v

DAU / WAU / MAU

Likes / Comments / Shares

```



\### Cumulative



```text

Today's Events

&#x20;     |

&#x20;     v

Daily Staging

&#x20;     |

&#x20;     v

FULL OUTER JOIN

&#x20;     ^

&#x20;     |

Yesterday's Cumulative State

&#x20;     |

&#x20;     v

Prepend Today's Values

&#x20;     |

&#x20;     v

Slice to W elements

&#x20;     |

&#x20;     v

Cumulative State Arrays

&#x20;     |

&#x20;     v

Scalar Metrics

```



The cumulative architecture avoids rescanning the historical event partitions on every day.



\---



\## 3. Data Layout



Raw events are stored as:



```text

data/events/

├── date=2023-01-01/

│   └── events.parquet

├── date=2023-01-02/

│   └── events.parquet

└── ...

```



Each Parquet file contains:



```text

user\_id     VARCHAR

event\_type  VARCHAR

event\_ts    TIMESTAMP

```



Supported event types:



```text

like

comment

share

view

```



\---



\## 4. Cumulative State



The cumulative table contains:



```text

user\_id

target\_date

activity\_array

likes\_array

comments\_array

shares\_array

```



The arrays are newest-first.



For example:



```text

activity\_array = \[1, 0, 1, 1, 0]

```



means:



```text

today       = 1

yesterday   = 0

day -2      = 1

day -3      = 1

day -4      = 0

```



The arrays are bounded to the selected benchmark window.



\---



\## 5. Equality Validation



The cumulative pipeline is considered correct only when its metrics exactly match the Rescan pipeline.



The validator compares:



```text

is\_active\_today

is\_active\_7d

is\_active\_30d

likes\_30d

comments\_30d

shares\_30d

```



for every user and target date.



Any mismatch causes the normal pipeline to fail.



\---



\## 6. Benchmark



Three window sizes are benchmarked:



```text

30 days

90 days

365 days

```



The expected behavior is that the Rescan pipeline reads more historical Parquet data as the window increases, while the cumulative pipeline reads today's partition and yesterday's cumulative state.



The benchmark output is:



```text

results/cumulative.csv

```



with:



```text

arm

window\_days

run\_date

wall\_ms

bytes\_read

peak\_mem\_mb

mismatches

```



\---



\## 7. Chaos Test



The chaos experiment deliberately removes 10% of the users from the daily staging table on the configured corruption date.



The corrupted cumulative state is then propagated into subsequent days.



The equality validator detects the resulting drift.



The cumulative state is then repaired by deleting the poisoned state and replaying the affected days sequentially.



This demonstrates the operational cost of stateful cumulative pipelines.



\---



\## 8. Backfill Result



The recovery metrics are stored in:



```text

results/backfill.csv

```



with:



```text

corrupted\_date

days\_affected

detect\_date

backfill\_runs

backfill\_wall\_s

```



\---



\## 9. Setup



\### Docker



Build the container:



```bash

docker compose build

```



Start it:



```bash

docker compose up -d

```



Verify:



```bash

docker compose ps

```



Check Python:



```bash

docker compose exec app python --version

```



Check DuckDB:



```bash

docker compose exec app python -c "import duckdb; print(duckdb.\_\_version\_\_)"

```



\---



\## 10. Local Setup



Create the environment file:



```bash

copy .env.example .env

```



Install dependencies:



```bash

python -m pip install -r requirements.txt

```



\---



\## 11. First Small Test



Before running the complete benchmark, generate a small dataset:



```bash

python generate\_data.py --users 1000 --days 10

```



Verify the partitions:



```bash

dir data\\events

```



Run tests:



```bash

python -m pytest -q

```



\---



\## 12. Run the Complete Pipeline



The required one-command entry point is:



```bash

make run DAYS=365

```



The command performs:



1\. Data generation

2\. Rescan execution

3\. Cumulative execution

4\. Equality validation

5\. Benchmarking



\---



\## 13. Windows Without Make



If GNU Make is not installed, use:



```bash

python generate\_data.py --users 10000 --days 365

```



Then:



```bash

python orchestrator.py run --days 365

```



\---



\## 14. Small Evaluation Run



For a quick evaluation:



```bash

python generate\_data.py --users 1000 --days 5

```



Then:



```bash

python orchestrator.py run --days 5

```



Check:



```text

results/cumulative.csv

```



\---



\## 15. Benchmark



Run:



```bash

python orchestrator.py benchmark --days 30

```



The benchmark contains:



```text

30-day rescan

30-day cumulative



90-day rescan

90-day cumulative



365-day rescan

365-day cumulative

```



\---



\## 16. Chaos Experiment



Run:



```bash

python orchestrator.py chaos

```



The default corruption day is configured through:



```text

CHAOS\_DAY=120

```



The default corruption removes:



```text

10%

```



of the staging users.



\---



\## 17. Backfill



After the chaos experiment:



```bash

python backfill.py

```



The recovery result is:



```text

results/backfill.csv

```



\---



\## 18. Validation



For a particular date:



```bash

python validate.py --date 2023-01-05

```



Expected:



```text

PASS: Rescan and cumulative outputs match for 2023-01-05

```



\---



\## 19. Results



The main benchmark file is:



```text

results/cumulative.csv

```



Required columns:



```text

arm

window\_days

run\_date

wall\_ms

bytes\_read

peak\_mem\_mb

mismatches

```



A successful normal run must have:



```text

mismatches = 0

```



for every row.



\---



\## 20. Engineering Tradeoff



The Rescan architecture is simpler because every day is independent.



The Cumulative architecture is more efficient for large windows because it processes today's events and carries forward bounded state arrays.



However, cumulative state introduces operational dependency between days. A corrupted state can propagate to subsequent days and requires ordered backfill.



Therefore, the correct engineering decision depends on:



\* window length

\* data volume

\* daily execution time

\* bytes scanned

\* memory usage

\* backfill cost

\* correctness requirements



The benchmark numbers in `results/cumulative.csv` should be used to make the final decision rather than assuming that cumulative tables are always faster.



\---



\## 21. Requirement Mapping



| Requirement           | Implementation                                     |

| --------------------- | -------------------------------------------------- |

| req-1 Docker          | `Dockerfile`, `docker-compose.yml`, `.env.example` |

| req-2 Generator       | `generate\_data.py`                                 |

| req-3 Rescan          | `sql/rescan\_metrics.sql`                           |

| req-4 Daily staging   | `sql/cumulative\_staging.sql`                       |

| req-5 Cumulative join | `sql/cumulative\_join.sql`                          |

| req-6 Extraction      | `sql/cumulative\_extract.sql`                       |

| req-7 Equality        | `validate.py`, `orchestrator.py`                   |

| req-8 Benchmark       | `results/cumulative.csv`                           |

| req-9 Chaos           | `orchestrator.py chaos`                            |

| req-10 Backfill       | `backfill.py`                                      |

| req-11 Automation     | `Makefile`                                         |



\---



\## 22. Final Verification



Run:



```bash

python -m pytest -q

```



Then:



```bash

python generate\_data.py --users 1000 --days 5

```



Then:



```bash

python orchestrator.py run --days 5

```



Then check:



```text

results/cumulative.csv

```



Finally run:



```bash

python validate.py --date 2023-01-05

```



A successful implementation should report zero mismatches.



