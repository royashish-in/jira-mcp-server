# Deployment Scripts

## Usage

Run these scripts from the project root directory:

```bash
# Docker deployment
./deploy/build-and-push.sh

# PyPI deployment  
./deploy/publish-pypi.sh
```

## Scripts

- **build-and-push.sh** - Builds Docker image and pushes to Docker Hub
- **publish-pypi.sh** - Builds Python package and publishes to PyPI