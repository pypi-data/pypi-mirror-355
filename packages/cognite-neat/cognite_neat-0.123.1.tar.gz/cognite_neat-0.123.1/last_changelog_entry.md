
### Fixed

- When writing instances (nodes and edges) to CDF using the
`neat.to.cdf.instance()` method, Neat now checks that CDF will have at
least free space for 500 000 instances after the writing is done.