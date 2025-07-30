<!-- SPDX-FileCopyrightText: 2025 German Aerospace Center <fame@dlr.de>

SPDX-License-Identifier: Apache-2.0 -->

[![PyPI version](https://badge.fury.io/py/fameprotobuf.svg)](https://badge.fury.io/py/fameprotobuf)
[![PyPI license](https://img.shields.io/pypi/l/fameprotobuf.svg)](https://badge.fury.io/py/fameprotobuf)
[![Pipeline status](https://gitlab.com/fame-framework/fame-protobuf/badges/main/pipeline.svg)](https://gitlab.com/fame-framework/fame-protobuf/commits/main)
[![REUSE status](https://api.reuse.software/badge/gitlab.com/fame-framework/fame-protobuf)](https://api.reuse.software/info/gitlab.com/fame-framework/fame-protobuf)


# FAME-Protobuf
Google Protocol Buffer (protobuf) definitions define the structure of binary input and output files for FAME applications.
Please visit the [Wiki for FAME](https://gitlab.com/fame-framework/wiki/-/wikis/home) to get an explanation of FAME and its components.

FAME-Protobuf connects FAME-Io to applications based on FAME-Core. Thus, both depend on FAME-Protobuf.

## Repository
The repository is split into three source code parts:
* protobuf definitions reside in `src/main/resources`,
* derived Python classes for FAME-Io reside in `src/main/python`.
* derived Java classes for FAME-Core reside in `target/generated-java-sources`

## Installation instructions
Use this Maven dependency:
```
<dependency>
  <groupId>de.dlr.gitlab.fame</groupId>
  <artifactId>protobuf</artifactId>
  <version>2.1.0</version>
</dependency>
```

## Packaging
### Compile
The `pom.xml` is configured to allow automated compilation of the protobuf definitions to Python and Java classes.

### Maven build
In the cloned repository of fame-protobuf, compile and package fame-protobuf locally to your Maven repository: 

```
mvn package
```

### Deploy to PyPI
FAME-Protobuf is packaged to PyPI.
We use [poetry](https://python-poetry.org) for packaging.
Packaging requires these steps:
* install poetry: `pip install poetry`
* run the packaging script: `python packaging.py`
* build wheel: `poetry build` 
* publish: `poetry publish`

# Contribute
Please read the Contributors License Agreement (cla.md), sign it and send it to fame@dlr.de before contributing.
Also, check CONTRIBUTING.md.
