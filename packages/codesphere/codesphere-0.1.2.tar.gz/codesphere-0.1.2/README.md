<p align="center">
  <img src="https://signup.codesphere.com/img/codesphere-circle.svg" alt="Codesphere API SDK Banner" width="300">
</p>

<h1 align="center">Codesphere Python SDK</h1>

<p align="center">
  <strong>The official Python client for the Codesphere Public API.</strong>
  <br />
  <br />
  <a href="https://pypi.org/project/[your-pypi-package-name]/">
    <img alt="PyPI Version" src="https://img.shields.io/pypi/v/[your-pypi-package-name].svg?style=flat-square&logo=pypi&logoColor=white">
  </a>
  <a href="https://github.com/[your-github-username]/[your-repo-name]/actions/workflows/ci.yml">
    <img alt="Build Status" src="https://img.shields.io/github/actions/workflow/status/[your-github-username]/[your-repo-name]/ci.yml?branch=main&style=flat-square&logo=githubactions&logoColor=white">
  </a>
  <a href="[LINK_TO_YOUR_CODECOV_REPORT_IF_ANY]">
    <img alt="Code Coverage" src="https://img.shields.io/codecov/c/github/[your-github-username]/[your-repo-name].svg?style=flat-square&logo=codecov&logoColor=white">
  </a>
  <a href="https://pypi.org/project/[your-pypi-package-name]/">
    <img alt="Python Versions" src="https://img.shields.io/pypi/pyversions/[your-pypi-package-name].svg?style=flat-square&logo=python&logoColor=white">
  </a>
  <a href="[LINK_TO_YOUR_DOCUMENTATION]">
    <img alt="Documentation" src="https://img.shields.io/badge/docs-latest-blue.svg?style=flat-square">
  </a>
  <a href="https://github.com/[your-github-username]/[your-repo-name]/releases/latest">
    <img alt="Latest Release" src="https://img.shields.io/github/v/release/[your-github-username]/[your-repo-name]?style=flat-square&logo=github&logoColor=white">
  </a>
  <a href="[LINK_TO_YOUR_LICENSE_FILE]">
    <img alt="License" src="https://img.shields.io/pypi/l/[your-pypi-package-name].svg?style=flat-square">
  </a>
</p>

---

## Overview

The Codesphere Python SDK provides a convenient wrapper for the [Codesphere Public API]([LINK_TO_API_DOCUMENTATION]), allowing you to interact with all API resources from your Python applications.

This SDK is auto-generated from our official [OpenAPI specification]([LINK_TO_YOUR_OPENAPI_SPEC.json]) and includes:
* **Modern Features**: Fully typed with Pydantic models and supports `asyncio`.
* **Easy to Use**: A high-level client that simplifies authentication and requests.
* **Comprehensive**: Covers all available API endpoints, including [e.g., Orgs, Apps, Deployments].

## Installation

You can install the SDK directly from PyPI using `pip` (or your favorite package manager like `uv`).

```bash
pip install [your-pypi-package-name]
```

##Getting Started

**Authentication**
To use the client, you need an API token. You can generate one from your Codesphere dashboard at [Link to API token generation page].

It's recommended to store your token in an environment variable:
```sh
export CS_TOKEN="your_api_token_here"
```

## Basic Usage

Instantiate the client and start making API calls. The client will automatically pick up the token from the environment variable.

```python
import os
import asyncio
from [your_package_name] import CodesphereClient

# The client automatically uses the CODESPHERE_API_TOKEN environment variable
# or you can pass it directly: CodesphereClient(api_token="your_token")
client = CodesphereClient()

async def main():
    try:
        organizations = await client.orgs.list_orgs()
        print("Found organizations:")
        for org in organizations:
            print(f"- {org.name} (ID: {org.id})")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

For synchronous usage, you can use the CodesphereClientSync class:

```python
from [your_package_name] import CodesphereClientSync

client_sync = CodesphereClientSync()
# [ADD SYNC EXAMPLE HERE]
```
# Codesphere-Python-SDK
# Codesphere-Python-SDK
