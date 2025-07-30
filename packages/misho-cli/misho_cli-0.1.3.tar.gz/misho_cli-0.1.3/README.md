# Misho CLI

Command Line Interface for Misho — the sportbooking reservation management system.

## 🔐 Authentication

Before using the CLI, make sure to set the required environment variable with your access token:

```bash
export MISHO_ACCESS_KEY=your_token_here
```

## Usage

For more information about available commands and usage, run:

```bash
mischo_cli --help
```

To enable tab-completions for your shell, run:

```bash
misho_cli --install-completion
```

This will detect your shell and install the appropriate completion script so you can use tab to auto-complete commands and options.

## Usage

Example usage for monitoring time slot:

```bash
misho_cli job create --day tomorrow --hour 19 21 notify
```

Example usage for getting reservation calendar:

```bash
misho_cli calendar get
```
