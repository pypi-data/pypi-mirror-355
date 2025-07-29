# sf-helper

A command-line interface (CLI) tool to simplify backing up Salesforce metadata.

## Overview

`sf-helper` is a Python-based CLI tool that helps Salesforce administrators and developers back up metadata from their Salesforce orgs. It streamlines the process of retrieving metadata components, such as objects, workflows, and profiles, and saves them to a local directory for version control or archival purposes.

## Features

- Backup Salesforce metadata with a single command.
- Support for multiple metadata types (e.g., Apex classes, custom objects, profiles).
- Configurable output directory for backups.
- Secure storage of Salesforce credentials (API key/token).

## Installation

### Prerequisites
- Python 3.8 or higher
- `pip` (Python package manager)
- Salesforce account with API access

### Steps
1. Install `sf-helper` using pip:
   ```bash
   pip install sf-helper
   ```
## Configuration

Before using `sf-helper`, set up your Salesforce API key or access token:

```bash
sf-helper set-key --api-key <your-api-key>
```

This stores the API key securely in a configuration file (`~/.sf_helper_config.ini`).

## Usage

### Backup Metadata
To back up metadata to a local directory:
**Not Yet Implemented**
```bash
sf-helper backup --output-dir ./salesforce-backup
```

This retrieves metadata from your Salesforce org and saves it to the specified directory.

### Specify Metadata Types
**Not Yet Implemented**
To back up specific metadata types (e.g., custom objects and profiles):

```bash
sf-helper backup --output-dir ./salesforce-backup --types CustomObject,Profile
```

### View Stored API Key
To check the stored API key:

```bash
sf-helper get-key
```

### Help
To see all available commands and options:

```bash
sf-helper --help
```

## Example

```bash
# Set API key
sf-helper set-key --api-key my-secret-key-123

# Backup all metadata (Not yet implemented)
sf-helper backup --output-dir ./my-backups

# Backup specific metadata types (Not yet implemented)
sf-helper backup --output-dir ./my-backups --types ApexClass,CustomObject
```

## Contributing

Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/YourFeature`).
3. Commit your changes (`git commit -m 'Add YourFeature'`).
4. Push to the branch (`git push origin feature/YourFeature`).
5. Open a pull request.

## License

This project is licensed under the MIT License.

## Support

For issues or questions, please open an issue on the [GitHub repository](https://github.com/yourusername/sf-helper).