# Formica

A low-code automation tool for network configuration

## Requirements

- Python 3.12 

## Usage

### 1. Initialize the metadata folder

The default path for the metadata folder is `~/formica`. You can change it by setting the `FORMICA_HOME` environment variable.
To initialize the metadata folder, run:

```bash
formica init
```

The metadata folder will be created at the specified path, and it will contain the following files:
- `formica.ini`: Configuration file for Formica.
- `logs/`: Directory for logs.
- `logging_config.json`: Logging configuration file.

You should check the `formica.ini` file to configure before running.

### 2. Run Formica

To run all 3 components of Formica (Webserver, Scheduler and Executor), use this command:

```bash
formica standalone
```

Formica will be available at `http://localhost:8000`. (with default `HOST` and `PORT`)
