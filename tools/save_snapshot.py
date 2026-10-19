"""Copy today's saved prices into data/snapshot, the copy that ships with the code (and the online app)."""

from riskkit.config import DEFAULT_CACHE_DIR
from riskkit.data.cache import save_snapshot

if __name__ == "__main__":
    n = save_snapshot(DEFAULT_CACHE_DIR)
    print(f"Saved {n} files to data/snapshot.")
