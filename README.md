# Chatot

A Python utility that extracts individual participant audio from Huddle01 meetings and uploads them to R2 bucket storage.

## Overview

Chatot is a Python package developed by Huddle01 that processes meeting recordings and extracts individual audio tracks for each participant. The tool then uploads these separated audio files to Cloudflare R2 bucket storage for easy access and management.

## Features

- Extract individual audio tracks for each participant in a Huddle01 meeting
- Record and process audio streams in real-time
- Automatically upload extracted files to R2 bucket storage
- Simple configuration for different storage settings

## Configuration

Create a `.env` file in your project root with the following variables:

```
# Huddle01 Configurations
HUDDLE01_API_KEY=
HUDDLE01_PROJECT_ID=
ROOM_ID=

# R2 Configurations
ACCOUNT_ID=
ACCESS_KEY_ID=
ACCESS_KEY_SECRET=
BUCKET_NAME=
CUSTOM_DOMAIN=
```

## Usage

### Command Line Interface

```bash
poetry run
```

## Development

### Setting Up Development Environment

```bash
git clone https://github.com/Huddle01/chatot.git
cd chatot

poetry env activate
poetry install
```

## Dependencies

The project uses Poetry for dependency management. Key dependencies include:

- Python 3.10+
- boto3 (for R2 interactions)
- av (for audio processing)
- python-dotenv (for environment configuration)

## License

[MIT License](LICENSE)

## Maintainer

Maintained by [AkMo3](https://github.com/AkMo3) for [Huddle01](https://github.com/Huddle01)
