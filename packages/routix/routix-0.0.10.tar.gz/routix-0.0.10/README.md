# routix

Routix is a lightweight Python toolkit for designing and executing structured algorithmic workflows.

It provides:

- Subroutine-based execution control (`SubroutineController`)
- Structured flow validation (`SubroutineFlowValidator`)
- Dot-accessible configuration trees (`DynamicDataObject`)
- Logging with routine-context traceability
- Experiment summary and timing support
- Abstract base classes for runners in `src/routix/runner/` for extensible workflow execution patterns

## Subroutine Flow Data Format

Routix executes algorithmic workflows based on a structured and validated subroutine flow.
Each step in the flow is represented by a dictionary with clearly defined keys,
enabling modular orchestration, logging, and reproducibility.

```yaml
# my_flow.yaml
- method: initialize
- method: repeat
  params:
    n_repeats: 3
    routine_data:
      - method: sample_method
        params:
          value: 42
```

For more details, refer to [subroutine_flow_data.md](./subroutine_flow_data.md).

## Abstract base classes for runners

Classes in `routix.runner` are extensible abstract base classes for implementing custom workflow runners. These classes provide a foundation for building repeatable, modular, and testable execution patterns for algorithmic experiments.

- **`SingleInstanceRunner`**: An abstract base class for running a single problem instance. It provides a template for implementing the logic for one experiment, including setup, execution, and result collection.
  - Typical usage: custom solvers, single-run experiments, or as a building block for higher-level runners.
- **`MultiInstanceRunner`**: An abstract base class for running multiple problem instances. It defines the interface and core logic for iterating over multiple instances, managing results, and integrating with experiment summaries.
  - Typical usage: batch experiments, benchmarking, or automated evaluation over a dataset.
- **`MultiInstanceConcurrentRunner`**: An abstract base class for running multiple problem instances concurrently (in parallel). It extends the multi-instance execution pattern to support concurrent processing, enabling faster experimentation and efficient use of computational resources.
  - Typical usage: parallel batch experiments, multi-core benchmarking, or scenarios where multiple instances should be solved simultaneously.

> **Note:** `InstanceSetRunner` is a deprecated name. Please use **`MultiInstanceRunner`** instead.

Both classes are designed to be subclassed and extended. You can implement your own runner by inheriting from these base classes and overriding the required methods to fit your workflow.

For implementation details, see the source files in `src/routix/runner/`.
