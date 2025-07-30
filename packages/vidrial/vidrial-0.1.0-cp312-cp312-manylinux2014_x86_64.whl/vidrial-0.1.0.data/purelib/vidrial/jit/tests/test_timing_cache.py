import pytest
import yaml
from vidrial.jit.mosaic_types.types import Shape
from vidrial.jit.timingcache import ConfigTimingCache
import torch

def test_basic_cache_operations(tmp_path):
    # Simple hash function for testing
    hash_fn = lambda x: str(sorted(x.items()))
    
    cache = ConfigTimingCache("test_fn", hash_fn, root=str(tmp_path))
    
    # Test insertion and retrieval
    arg = {"param1": 1, "param2": 2}
    timings = [
        {"config": {"tile": 32}, "time": 0.5, "std": 0.1, "n": 10},
        {"config": {"tile": 64}, "time": 0.3, "std": 0.05, "n": 20}
    ]
    
    cache.update(arg, timings)
    
    # Test __contains__
    assert arg in cache
    
    # Test __getitem__ - should return best performing config
    best_config = cache[arg]
    assert best_config == {"tile": 64}  # The one with time 0.3
    
    # Test __len__
    assert len(cache) == 1

def test_sorting_behavior(tmp_path):
    hash_fn = lambda x: str(sorted(x.items()))
    cache = ConfigTimingCache("test_fn", hash_fn, root=str(tmp_path))
    
    arg = {"param": 1}
    
    # Add timings in non-sorted order
    timings = [
        {"config": {"tile": 32}, "time": 0.5},
        {"config": {"tile": 16}, "time": 0.2},
        {"config": {"tile": 64}, "time": 0.3}
    ]
    
    cache.update(arg, timings)
    
    # Verify best config is returned (should be tile=16 with time=0.2)
    assert cache[arg] == {"tile": 16}
    
    # Add another config that hashes to same key
    config2 = {"param": 1}  # Same hash as config
    timings2 = [
        {"config": {"tile": 8}, "time": 0.1}
    ]
    
    cache.update(config2, timings2)
    
    # Verify entries are sorted by best timing
    key = hash_fn(arg)
    entries = cache._cache[key]
    assert entries[0]["timings"][0]["time"] == 0.1  # Best timing should be first
    assert entries[1]["timings"][0]["time"] == 0.2  # Second best timing next

def test_size_limiting(tmp_path):
    hash_fn = lambda x: str(x["id"])
    cache = ConfigTimingCache("test_fn", hash_fn, root=str(tmp_path), size=2)
    
    # Add 3 configs - should only keep 2
    for i in range(3):
        config = {"id": i}
        timings = [{"config": {"tile": 32}, "time": float(i)}]
        cache.update(config, timings)
    
    assert len(cache) == 2
    # Should keep the ones with better timings
    assert {"id": 0} in cache
    assert {"id": 1} in cache
    assert {"id": 2} not in cache

def test_file_persistence(tmp_path):
    hash_fn = lambda x: str(sorted(x.items()))
    
    # Create and populate cache
    cache1 = ConfigTimingCache("test_fn", hash_fn, root=str(tmp_path))
    arg = {"param": 1}
    timings = [{"config": {"tile": 32}, "time": 0.5, "std": 0.1, "n": 10}]
    cache1.update(arg, timings)
    
    # Create new cache instance - should load from file
    cache2 = ConfigTimingCache("test_fn", hash_fn, root=str(tmp_path))
    assert arg in cache2
    assert cache2[arg] == {"tile": 32}
    
    # Test remove functionality
    cache2.remove()
    cache3 = ConfigTimingCache("test_fn", hash_fn, root=str(tmp_path))
    assert len(cache3) == 0

def test_strict_verification(tmp_path):
    hash_fn = lambda x: str(sorted(x.items()))
    cache = ConfigTimingCache("test_fn", hash_fn, root=str(tmp_path))
    
    arg = {"param": 1}
    timings = [
        {"config": {"tile": 32}, "time": 0.5, "std": 0.1, "n": 10},
        {"config": {"tile": 16}, "time": 0.2, "std": 0.05, "n": 20}
    ]
    cache.update(arg, timings)
    
    # Manually corrupt the cache file to test verification
    key = hash_fn(arg)
    with open(cache.location, 'r') as f:
        data = yaml.safe_load(f)
    
    # Corrupt the sorting
    data[key][0]["timings"].reverse()
    
    with open(cache.location, 'w') as f:
        yaml.safe_dump(data, f)
    
    # Loading with strict=True should raise error
    with pytest.raises(ValueError):
        ConfigTimingCache("test_fn", hash_fn, root=str(tmp_path), strict=True)
    
    # Loading with strict=False should work
    cache2 = ConfigTimingCache("test_fn", hash_fn, root=str(tmp_path), strict=False)
    assert arg in cache2

def test_storing_mosaic_types(tmp_path):
    x = torch.randn(10, 10)
    hash_fn = lambda arg: str(arg['x'].shape)
    arg = {'x': x}
    cache = ConfigTimingCache("test_fn", hash_fn, root=str(tmp_path))
    tile_shape = Shape(32, 32)
    cache.update(arg, [{"config": {"tile": tile_shape}, "time": 0.5, "std": 0.1, "n": 10}])
   
    assert arg in cache
    assert cache[arg] == {"tile": tile_shape}

    # test loading from file
    cache2 = ConfigTimingCache("test_fn", hash_fn, root=str(tmp_path))
    assert arg in cache2
    assert cache2[arg] == {"tile": tile_shape}