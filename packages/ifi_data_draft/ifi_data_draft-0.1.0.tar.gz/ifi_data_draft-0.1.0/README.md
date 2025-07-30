# Deployment

## Requirements

- `git`
- `docker` and `docker-compose`
- `mise` or `just` (for convenience)

## Setup

```bash
git clone git@gitlab.tu-clausthal.de:ifi-data/api.git
cd api/draft
mise trust
mise install
just start
```

# Usage

TODO

# TODOs

- [ ] support insertion via REST api
- [ ] visualization (using `grafana`)
- [ ] config file management (at least for `cli`)
- [ ] docs site
- [ ] support read/append only

## Ideas

- [ ] duckdb and [duckdbui](https://github.com/duckdb/duckdb-ui)
- [ ] hyperfunctions for efficient time-related queries (https://docs.timescale.com/api/latest/hyperfunctions/time-weighted-calculations/time_weight/)
