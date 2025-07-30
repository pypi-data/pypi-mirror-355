from dataclasses import dataclass
from typing import List, Dict, Any
import torch as th
from vidrial.jit.jit import render, jit
from vidrial.jit.decorator import pickbest
from vidrial.jit.timingcache import ConfigTimingCache

# ------------------- Source Code -------------------
@dataclass
class SourceCode:
    d0: int
    d1: int
    tile_d0: int
    tile_d1: int
    thread_num: int
    
    @property
    def template(self) -> str:
        return """
#include "add_one/add_one_kernels.cuh"
#include "copy/copy_kernels.cuh"
using namespace cute;
using namespace mosaic;

extern "C" {
    void launch(float* Vptr) {
        using SlabShape = Shape<Int<{d0}>, Int<{d1}>>;
        using TileShape = Shape<Int<{tile_d0}>, Int<{tile_d1}>>;
        using ASlab = Layout<SlabShape>;
        launch_add_one_inplace<float, {thread_num}, SlabShape, TileShape, ASlab>(Vptr);
    }
}"""

    def __str__(self) -> str:
        return render(self.template, self.__dict__)


@dataclass
class BindingCfg:
    d0: int
    d1: int
    tile_d0: int
    tile_d1: int
    thread_num: int
    
    @classmethod
    def from_args(cls, X, tile_d0, tile_d1, thread_num):
        return cls(
            d0=X.shape[0],
            d1=X.shape[1],
            tile_d0=tile_d0,
            tile_d1=tile_d1,
            thread_num=thread_num)

    @property
    def source(self):
        return SourceCode(
            d0=self.d0,
            d1=self.d1,
            tile_d0=self.tile_d0,
            tile_d1=self.tile_d1,
            thread_num=self.thread_num)


def binding(X: th.Tensor, tile_d0: int, tile_d1: int, thread_num: int):
    cfg = BindingCfg.from_args(X, tile_d0, tile_d1, thread_num)
    jit(name = "add_one", code = str(cfg.source))(X)


# ---------------------- Autotune --------------------------------

def make_add_one_configurator(num_range: List[int]):
    def add_one_configurator(args: dict) -> List[dict[str, Any]]:
        X = args['X']
        configs = []
        d0, d1 = X.shape
        for thread_num in num_range:
            for tile_d0 in num_range:
                for tile_d1 in num_range:
                    if tile_d0 > d0 or tile_d1 > d1:
                        continue
                    configs.append({
                        'thread_num': thread_num,
                        'tile_d0': tile_d0,
                        'tile_d1': tile_d1,
                    })

        return configs
    return add_one_configurator


def hash_fn(args: dict) -> str:
    X = args['X']
    return f"{X.shape[0]}_{X.shape[1]}_{X.dtype}"

cache = ConfigTimingCache('add_one', hash_fn)
add_one_kernel = pickbest(cache=cache, sweep=make_add_one_configurator([1, 4, 32]), verbose=True, allow_failure=True)(binding)


if __name__ == '__main__':
    input = th.ones((64,64), dtype=th.float32, device="cuda")
    add_one_kernel(input)
