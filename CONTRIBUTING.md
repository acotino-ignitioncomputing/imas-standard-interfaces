# Constributing to IMAS Standard Interfaces

Thank you for your interest in contributing to the IMAS Standard Interfaces
project! This document provides guidelines and instructions to help you
contribute effectively.

## How to Contribute

### Reporting Issues

If you find a problem or have a suggestion:

1. Check if the issue already exists in the [Issues](https://github.com/iterorganization/imas-standard-interfaces/issues) section.
2. If not, create a new issue with a clear title and detailed description.
3. Optionally, include relevant examples or error messages.

### Submitting Changes

1. Fork the repository.
2. Create a new branch with a descriptive name.
3. Make your changes.
4. Ensure all the example interface definitions are correct with respect to the
   JSON Schema and the Data Dictionary. This can be checked with e.g. the
   command `imas-interfaces validate`, or the Python libraries [`jsonschema`](https://pypi.org/project/jsonschema/) and [`imas-python`](pypi.org/project/imas-python/).
   Update the documentation accordingly.
5. Submit a pull request with a clear description of the changes.
