# Tactical ground blast radius (experimental)

The artillery HE blast radius now uses two terrain-projected rings rather
than the older translucent 3D sphere. The default splash anchor is
`objects/artysplash_ground.model`, which reuses the original mesh but has
a transparent diffuse map. The mesh is present only to host the
`BigWorld.PyTerrainSelectedArea` attachments. The centre marker uses the
original `artydot.model` and a cyan DXT1 texture.

- Outer ring: diameter 2 in model space, cyan `0xFF22D3EE`.
- Inner ring: diameter 1.55 in model space, translucent cyan `0x6622D3EE`.
- Both inherit the parent scale set from `shell.type.explosionRadius`.
- Both update terrain heights at the current gun marker.
- Existing Z/Alt and C/Alt key toggles and camera/shell gating remain intact.

## Compatibility and testing

This change cannot be fully validated without a live World of Tanks
client. Confirm the terrain ring projection, alpha handling, colours,
scale and performance in strategic view with HE shells. The outer ring
must represent the explosion radius in metres; verify this against a
known radius. Ensure the inner ring is not drawn through obstacles.
Check that switching shell type and leaving battle removes both rings.
The ground rings use the existing game asset
`content/Interface/CheckPoint/CheckPoint_yellow_black.model`, so
appearance depends on its client implementation.

**Rollback:** restore `modelPathSplash` to
`objects/artysplash.model` and revert the Python ring change. Original
model, visual, primitive and splash DDS remain in the repository.

Avoid changing model scale conventions until verified in client.
