# Docker Adapter

<p align="center">
  <img src="assets/png/eviesales.png" alt="Bitzer Logo" width="200">
</p>


A Python library for managing Docker containers and images with a clean and intuitive interface.

[![PyPI version](https://badge.fury.io/py/docker-adapter.svg)](https://badge.fury.io/py/docker-adapter)
[![Python Versions](https://img.shields.io/pypi/pyversions/docker-adapter.svg)](https://pypi.org/project/docker-adapter/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## About

Docker Adapter is developed and maintained by [Evolvis](https://evolvis.ai), a company specializing in AI and software development solutions. This library provides a clean and intuitive interface for managing Docker containers and images in Python applications.

## Features

- Container management (start, stop, pause, unpause, kill, remove)
- Image management (pull, push, tag, remove)
- Container and image inspection
- Container logs and stats
- Command execution in containers
- Error handling with custom exceptions
- Type hints for better IDE support

## Installation

```bash
pip install docker-adapter
```

## Quick Start

```python
from docker_adapter import DockerClient

# Initialize the Docker client
client = DockerClient()

# List all containers
containers = client.list_containers(all=True)
for container in containers:
    print(f"Container: {container.name} (ID: {container.id})")

# List all images
images = client.list_images()
for image in images:
    print(f"Image: {image.tags[0] if image.tags else image.id}")
```

## Documentation

For detailed documentation, please visit our [documentation page](docs/README.md).

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Alban Maxhuni, PhD**  
Email: [a.maxhuni@evolvis.ai](mailto:a.maxhuni@evolvis.ai)  
[Evolvis](https://evolvis.ai)

## Support

For support, please contact [support@evolvis.ai](mailto:support@evolvis.ai) or visit our [website](https://evolvis.ai).

## About Evolvis

[Evolvis](https://evolvis.ai) is a technology company that specializes in:
- Artificial Intelligence Solutions
- Software Development
- Cloud Infrastructure
- DevOps Automation
- Container Orchestration

Visit our [website](https://evolvis.ai) to learn more about our services and solutions. 