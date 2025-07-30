
### Added

- Support for setting `cursorable` when specifying an index on container
properties.

### Fixed

- Neat can now specify and maintains the order of multi-property order
on indices. You do this with the syntax,
`btree:multipPropertyIntdex(order=1)` in the Index column of the
physical data model spreadsheet.

### Changed

- When setting an index on a property(ies) with a listable container,
Neat uses an `InvertedIndex` instead of a `BTreeIndex`.