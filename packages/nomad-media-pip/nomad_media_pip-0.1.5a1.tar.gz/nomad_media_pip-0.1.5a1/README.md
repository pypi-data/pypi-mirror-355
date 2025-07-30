## Nomad Media Pip SDK
This sdk is a wrapper for all of the nomad api endpoints.

## Minimum Requirements
- Python 3.12

## Installation
To use the Nomad SDK, install the package using pip.

```shell
pip install nomad-media-pip

## Quick Start

```python
from nomad_media_pip import Nomad_SDK

# Initialize SDK
config = {
    "username": "username",
    "password": "password",
    "serviceApiUrl": "https://your-api-url",
    "apiType": "admin", # Use "admin" or "portal"
    "debugMode": False, # Enable for detailed logging
    "singleton": False, # Enables to restrict sdk to single instance
    "noLogging": False # Enable to remove all logging
}

# Create SDK instance
sdk = Nomad_SDK(config)

# Example: Search assets
response = sdk.search("example")
```