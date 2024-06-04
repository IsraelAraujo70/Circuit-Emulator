## [Unreleased]

### Added
- Basic GUI setup using tkinter.
- Functionality to add components (source, resistor, node) to the canvas.
- Rotation of components with a right-click.
- Wire drawing functionality with grid snapping.
- Undo and redo functionality with Control+Z and Control+Y shortcuts.
- Basic circuit calculation methods:
  - Series resistance calculation.
  - Parallel resistance calculation.
  - Current calculation.
- Check for closed circuits.
- Basic simulation to calculate voltage drops and currents in resistors.
- Grid drawing for better alignment of components.
- Basic HUD display for simulation status.

### Changed
- Added simulation mode to prevent changes to the circuit while simulating.
- Introduced colored resistors to differentiate between parallel and series groups.
- Improved the HUD to show real-time voltage and current values near the cursor during simulation.
- Added functionality to display currents on wires during simulation.
- Implemented a mechanism to prevent rotation of components during simulation.
- Improved user prompts for entering voltage and resistance values.
- Enhanced grid drawing to be responsive to window resizing.
- Added placeholders for saving and opening projects (functionalities to be implemented).

### Fixed
- Bugs related to component drawing and wire connections.

## [1.0.0] - 2024-06-03
### Added
- Initial release with all core functionalities.