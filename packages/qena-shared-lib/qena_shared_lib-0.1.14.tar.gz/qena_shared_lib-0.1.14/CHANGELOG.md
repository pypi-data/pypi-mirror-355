# Changelog

## [0.1.14] - 2025-06-16

### Changed

- Remove unused generics variables
- Remove requirements.txt


## [0.1.13] - 2025-06-16

### Added

- Added pytest as one of pre-commit steps.
- Made http and rabbitmq exception handlers class based.
- Gracefull shutdown for rabbitmq and scheduler.

### Changed

- Moved logstash to remotelogging to generalize other forms of logging.
- Added loop class attribute for async event loop mixin.
- Made mypy type check slightly more strict.


## [0.1.12] - 2025-04-05

### Added

- Added a re-export for rabbitmq channel pool (ChannelPool) class.


[0.1.14]: https://github.com/Qena-Digital-Lending/qena-shared-kernel/compare/v0.1.13...v0.1.14
[0.1.13]: https://github.com/Qena-Digital-Lending/qena-shared-kernel/compare/v0.1.12...v0.1.13
[0.1.12]: https://github.com/Qena-Digital-Lending/qena-shared-kernel/compare/v0.1.11...v0.1.12
