<!-- SPDX-FileCopyrightText: 2025 German Aerospace Center <fame@dlr.de>

SPDX-License-Identifier: CC0-1.0 -->
# Changelog

## [2.1.0](https://gitlab.com/fame-framework/fame-protobuf/-/tags/v2.1.0) - 2025-06-17
### Added
- Extend ModelData with a list of agent classes used in the model #57 (@dlr-cjs)
- Add field `metadata` to `InputData` message #60 (@dlr-cjs)
- Add field `metadata` to `NestedField` message #61 (@dlr-cjs)
- Add GitLab issue templates #58 (@dlr-cjs)

## [2.0.4](https://gitlab.com/fame-framework/fame-protobuf/-/tags/v2.0.4) - 2025-05-27
### Changed
- Migrate publishing server to Sonatype Central #59 (@dlr-cjs)

## [2.0.3](https://gitlab.com/fame-framework/fame-protobuf/-/tags/v2.0.3) - 2024-12-02
### Fixed
- Update outdated protobuf version with vulnerability #56 (@dlr-cjs)

## [2.0.2](https://gitlab.com/fame-framework/fame-protobuf/-/tags/v2.0.2) - 2024-09-04
### Fixed
- Fix typo in Services.Output.AgentType.Field #55 (@dlr-cjs)

## [2.0.1](https://gitlab.com/fame-framework/fame-protobuf/-/tags/v2.0.1) - 2024-09-01
_If you are upgrading: please see [`UPGRADING.md`](UPGRADING.md)_

### Changed
- **Breaking**: Set repeated numeric fields in `NestedField` to be packed more efficiently #41 (@dlr-cjs)
- **Breaking**: Change message `InputData.TimeSeriesDao` to use two separate repeated fields for times and values #39 (@dlr-cjs)
- **Breaking**: Update field names to follow style guide #42 (@dlr-cjs)
- Update Java compilation target to version 11
- Update SPDX license header email #51 (@dlr-cjs)
 
### Added
- Add `ModelData` message to `Bundle` #46 (@dlr-cjs)
- Add `StringSetDao` message to `InputData` #47, #50 (@dlr-cjs)
- Add CONTRIBUTING.md to repository #53 (@dlr-cjs)

### Removed
- **Breaking**: Remove message `OutputParam` from `InputData` #38 (@dlr-cjs)
- **Breaking**: Remove message `ProtoSetup` from `Services` #38 (@dlr-cjs)
- Delete `.project` and `.project.license` files from repository #45 (@dlr-cjs)

## 2.0.0 - 2024-08-14
_Revoked_

## [1.5.0](https://gitlab.com/fame-framework/fame-protobuf/-/tags/v1.5.0) - 2024-04-11
### Added
- Add java package section to Model #43 (@dlr-cjs)

## [1.4.0](https://gitlab.com/fame-framework/fame-protobuf/-/tags/v1.4.0) - 2024-03-17
### Changed
- Use 2-space indentation in all .proto files #20 (@dlr-cjs)

### Added
- Add new optional section to DataStorage holding simulation execution details #21 (@dlr-cjs)
- Add new optional section to DataStorage holding model details #20 (@dlr-cjs)
- Add new optional entry to NestedField telling whether a field is of type "list" #34 (@dlr-cjs)
- Add license string to each .proto file #35 (@dlr-cjs)
- Ensure reuse compatibility in CI #35 (@dlr-cjs)
- Ensure CHANGELOG is up to date in CI #36 (@dlr-cjs)

## [1.3.1](https://gitlab.com/fame-framework/fame-protobuf/-/tags/v1.3.1) - 2023-11-29
### Changed
- Loosen maximum supported Python version #33 (@dlr-cjs @dlr_fn)

## [1.3.0](https://gitlab.com/fame-framework/fame-protobuf/-/tags/v1.3.0) - 2023-11-22
### Changed 
- Switch to pyproject.toml to replace setup.py #32 (@dlr-cjs)
- Reformat Changelog to follow style guide #29 (@dlr-cjs)
- Update to latest protobuf version 24 #31 (@dlr-cjs)
- Update README.md #32 (@dlr-cjs, @dlr_fn)

### Added
- Provide Python interface files (#30 @dlr-cjs)

## [1.2.1](https://gitlab.com/fame-framework/fame-protobuf/-/tags/v1.2.1) - 2023-05-03
### Changed
- Remove `ProgramParam` from InputData - regarded as non-breaking as it was not used so far

### Added
- Store a schema in InputData
- Add optional MetaData field to AgentDao 
- Add optional MetaData field to ProtoContract 
- Update to latest protobuf version 22

## [1.2](https://gitlab.com/fame-framework/fame-protobuf/-/tags/v1.2) - 2022-07-08
### Changed
- Output messages may now contain multiple key-value mappings per column
- Update to latest protobuf version 21

## [1.1.5](https://gitlab.com/fame-framework/fame-protobuf/-/tags/v1.1.5) - 2021-06-10
### Changed
- Extract version number from `pom.xml` in setup.py
- Ensure that files are compiled before committing to PyPI

## [1.1.4](https://gitlab.com/fame-framework/fame-protobuf/-/tags/v1.1.4) - 2021-0607
### Added
- Add missing setup.yaml parameters
- Add long values for Fields

### Changed
- Make long, int, and string repeatable for Fields

### Removed
- Remove default values of Fields

## 1.1.3 - Retracted

## [1.1.2](https://gitlab.com/fame-framework/fame-protobuf/-/tags/v1.1.2) - 2021-0311
### Changed
- Update Contracts to feature recursive fields

## [1.1.1](https://gitlab.com/fame-framework/fame-protobuf/-/tags/v1.1.1) - 2021-02-19
### Changed
- Restructure Inputs to allow nested Fields  

## [1.1.0](https://gitlab.com/fame-framework/fame-protobuf/-/tags/v1.1.0) - 2021-02-11
### Changed
- Automate packaging to PyPI

## [1.0](https://gitlab.com/fame-framework/fame-protobuf/-/tags/v1.0) - 2021-02-09
_Initial release._