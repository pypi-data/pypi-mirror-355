# schore

*From raw data to scheduling problem instances.*

**schore** is a lightweight Python library that helps transform tabular or textual input
into structured scheduling problem instances.

## ✨ Modules

### Core Interfaces

```python
from schore import DfManager, Table2DManager, JobStageProcessingTimeManager, JobMachineProcessingTimeManager
```

- `DfManager`: A base class to manage a DataFrame.
- `Table2DManager`: A class to manage a 2D table represented as a DataFrame.
- `JobStageProcessingTimeManager`: A class to manage a 2D DataFrame with columns for stages & rows for jobs.
- `JobMachineProcessingTimeManager`: A class to manage a 2D DataFrame with columns for machines & rows for jobs.

### Utility

```python
from schore.util import TextDataParser
```

- `TextDataParser`: A class to parse text data from a stream.

### Scheduling Models

```python
from schore.hybridflowshop import HybridFlowShopProblem
```

- `HybridFlowShopProblem`: Hybrid flow shop problem instance with multiple jobs and stages, where each stage may have multiple parallel machines.

## 🛠️ Repository Structure

```plaintext
├── src/
│   └── schore/
│       ├── hybridflowshop/
│       │   └── problem.py
│       ├── manager/
│       │   ├── base/
│       │   │   ├── df_manager.py
│       │   │   └── table_2d_manager.py
│       │   ├── processing_time/
│       │   │   ├── job_mc_p.py
│       │   │   └── job_stage_p.py
│       ├── util/
│       │   └── text_data_parser.py
│       └── type_hints.py
├── tests/
│   ├── hybridflowshop/
│   │   └── test_problem.py
│   ├── manager/
│   │   ├── base/
│   │   │   ├── test_df_manager.py
│   │   │   └── test_table_2d_manager.py
│   │   └── test_job_stage_processing_time_manager.py
│   └── util/
│       └── test_text_data_parser.py
```

## 🧪 Testing

To run the tests, use the following command:

```sh
pytest tests/
```

## Installation

```sh
pip install schore
```

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
