# Spade SDK

Spade SDK provides basic classes to implement Spade Files and Processes.
For more information about Spade, please visit [Spade](https:://getspade.io)

It has no dependencies on other Python libraries, and allows development for Spade without
a need to install the full Spade app.

## Installation

```bash
pip install spadesdk
```

### Optional Dependencies

For file validation functionality, install with the `pandera` extra:

```bash
pip install spadesdk[pandera]
```

## Basic objects

### FileProcessor

`FileProcessor` processes the file uploaded by the user in the Spade app.

#### File Validation

The `FileProcessor` class includes a static `validate` method that can validate file
data against a schema using the Pandera library. This method validates DataFrame data
against a Frictionless schema defined in the `File` object.

**Requirements:**
- The ` spadesdk[pandera]` package must be installed (available as an optional dependency)
- A valid Frictionless schema must be defined in Spade

```
# Validate DataFrame against the schema
FileProcessor.validate(file, dataframe)
```

**Note:** If Pandera is not installed, calling the `validate` method will raise an `ImportError`.

### Executor

`Executor` executes a Spade process, either by directly running Python code or by
calling an external service.

### HistoryProvider

`HistoryProvider` provides the history of a Spade from if the actual process is executed
by an external service. If the process is executed in Spade, a `HistoryProvider` is not
needed.
