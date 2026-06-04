# Future Integration: metal-lathe

## Current State
The Research Wheel — a metal tooling research repository exploring hardware abstraction concepts for the SuperInstance ecosystem.

## Integration Opportunities

### With construct-core hardware abstraction
metal-lathe's hardware abstraction concepts map to construct-core's layered trait system. The "lathe" metaphor — a tool that shapes material — applies to how construct-core shapes agent behavior for different hardware tiers. Layer 0 (bare metal) is the raw material; Layer 1 (sync) is rough-cut; Layer 2 (async) is precision-machined. The lathe shapes constructs for their target hardware.

### With room-as-codespace deployment
When a room's ternary cells are compiled for different hardware, metal-lathe provides the tooling pipeline: analyze cell requirements → select target tier → compile optimizations → verify correctness. The lathe shapes the room for its deployment target.

### With tile-compiler
Tile compilation IS a form of metal tooling — compiling game strategies into fast lookup tables. metal-lathe provides the meta-tooling: how to build compilers that target different hardware. tile-compiler is one instance; agentic-compiler is another; metal-lathe is the framework.

## Dormant Ideas Now Unlockable
Hardware abstraction was theoretical when the fleet only ran on one type of hardware. Now with Codespace (cloud x86), Jetson (ARM + CUDA), and ESP32 (bare metal), hardware abstraction is essential. metal-lathe's concepts become concrete.

## Potential in Mature Systems
metal-lathe becomes the fleet's hardware targeting layer. When you build a new skill, metal-lathe compiles it for every tier: Layer 0 lookup table for ESP32, Layer 1 sync function for Jetson, Layer 2 async handler for Codespace. One skill, three targets.

## Cross-Pollination Ideas
- **tile-compiler**: Specific compiler targeting game strategies
- **agentic-compiler**: Specific compiler targeting Python hot-paths
- **pincherOS**: OS-level hardware abstraction for bare-metal rooms

## Dependencies for Next Steps
- Formalize the hardware targeting pipeline
- Integration with construct-core's trait system
- Multi-target compilation backend
