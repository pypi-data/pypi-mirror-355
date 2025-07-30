from math import prod
import torch as th
from copy import copy
import inspect
import logging
from dataclasses import dataclass
from typing import Tuple, List, Dict, Any, Iterable
from vidrial.mosaic.utils.gpu import get_cuda_device_basic_props
from vidrial.jit.mosaic_types.types import CudaDType
from vidrial.jit.mosaic_types.shape import static_shape
from vidrial.jit.mosaic_types.util import torch_dtype_to_c
from itertools import product
from functools import lru_cache, partial, wraps

device_props = get_cuda_device_basic_props()[0]
SMEM_LIMIT = device_props['CU_DEVICE_ATTRIBUTE_MAX_SHARED_MEMORY_PER_MULTIPROCESSOR']
REG_PER_SM = device_props['CU_DEVICE_ATTRIBUTE_MAX_REGISTERS_PER_MULTIPROCESSOR']
SM_NUMBER = device_props['CU_DEVICE_ATTRIBUTE_MULTIPROCESSOR_COUNT']
MAX_THREADS_PER_BLOCK = 128 # A manual choice

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class MMAAtom:
    name: str
    MNK: Tuple[int, ...]
    D_type: CudaDType
    A_type: CudaDType
    B_type: CudaDType
    C_type: CudaDType
    thread_count: int # Number of threads required to run the atom

MMAAtom_registry = {}

def register_mma_atom(name, MNK, A_type, B_type, C_type, D_type, thread_count):
    atom = MMAAtom(name, MNK, A_type, B_type, C_type, D_type, thread_count)
    MMAAtom_registry[name] = atom

# The fundamental MMA atoms based on FMA that work on all architectures for all problem shapes
ALL_FLOAT_TYPES = [CudaDType.FLOAT32, CudaDType.FLOAT16, CudaDType.BFLOAT16]
for A_dtype in ALL_FLOAT_TYPES:
    for B_dtype in ALL_FLOAT_TYPES:
        for C_dtype in ALL_FLOAT_TYPES:
            for D_dtype in ALL_FLOAT_TYPES:
                register_mma_atom(f"UniversalFMA<{A_dtype.value},{B_dtype.value},{C_dtype.value},{D_dtype.value}>", (1, 1, 1), A_dtype, B_dtype, C_dtype, D_dtype, 1)

# A list of all available MMA atoms for the SM80 architecture
register_mma_atom("SM80_16x8x8_F16F16F16F16_TN", (16, 8, 8), CudaDType.FLOAT16, CudaDType.FLOAT16, CudaDType.FLOAT16, CudaDType.FLOAT16, 32)
register_mma_atom("SM80_16x8x16_F16F16F16F16_TN", (16, 8, 16), CudaDType.FLOAT16, CudaDType.FLOAT16, CudaDType.FLOAT16, CudaDType.FLOAT16, 32)
register_mma_atom("SM80_16x8x8_F32F16F16F32_TN", (16, 8, 8), CudaDType.FLOAT32, CudaDType.FLOAT16, CudaDType.FLOAT16, CudaDType.FLOAT32, 32)
register_mma_atom("SM80_16x8x16_F32F16F16F32_TN", (16, 8, 16), CudaDType.FLOAT32, CudaDType.FLOAT16, CudaDType.FLOAT16, CudaDType.FLOAT32, 32)
register_mma_atom("SM80_16x8x8_F32BF16BF16F32_TN", (16, 8, 8), CudaDType.FLOAT32, CudaDType.BFLOAT16, CudaDType.BFLOAT16, CudaDType.FLOAT32, 32)
register_mma_atom("SM80_16x8x16_F32BF16BF16F32_TN", (16, 8, 16), CudaDType.FLOAT32, CudaDType.BFLOAT16, CudaDType.BFLOAT16, CudaDType.FLOAT32, 32)
register_mma_atom("SM80_16x8x4_F32TF32TF32F32_TN", (16, 8, 4), CudaDType.FLOAT32, CudaDType.FLOAT32, CudaDType.FLOAT32, CudaDType.FLOAT32, 32)
register_mma_atom("SM80_16x8x8_F32TF32TF32F32_TN", (16, 8, 8), CudaDType.FLOAT32, CudaDType.FLOAT32, CudaDType.FLOAT32, CudaDType.FLOAT32, 32)
register_mma_atom("SM80_8x8x4_F64F64F64F64_TN", (8, 8, 4), CudaDType.FLOAT64, CudaDType.FLOAT64, CudaDType.FLOAT64, CudaDType.FLOAT64, 32)
# struct SM80_8x8x4_C64C64C64C64_TN
# struct SM80_8x8x4_GC64C64C64GC64_TN
# struct SM80_8x8x16_S32S8S8S32_TN
# struct SM80_8x8x16_S32S8S8S32_TN_SATURATE
# struct SM80_16x8x16_S32S8S8S32_TN
# struct SM80_16x8x16_S32S8S8S32_TN_SATURATE
# struct SM80_16x8x32_S32S8S8S32_TN
# struct SM80_16x8x32_S32S8S8S32_TN_SATURATE
# struct SM80_8x8x16_S32S8U8S32_TN
# struct SM80_8x8x16_S32S8U8S32_TN_SATURATE
# struct SM80_16x8x16_S32S8U8S32_TN
# struct SM80_16x8x16_S32S8U8S32_TN_SATURATE
# struct SM80_16x8x32_S32S8U8S32_TN
# struct SM80_16x8x32_S32S8U8S32_TN_SATURATE
# ......... there are more but we don't need them for now


def get_largest_atoms(atoms):
    """Returns the list of the atoms with the largest MNK.
    Where atom0.MNK < atom1.MNK iff atom0.MNK[0] < atom1.MNK[0] and atom0.MNK[1] < atom1.MNK[1] and atom0.MNK[2] < atom1.MNK[2]
    Since this relationship is a partial order we only filter out the atoms that are strictly smaller than others"""
    def is_smaller(atom0, atom1):
        # If any dimension of atom0 is greater, then atom0 is not strictly smaller
        if atom0.MNK[0] > atom1.MNK[0] and atom0.MNK[1] > atom1.MNK[1] and atom0.MNK[2] > atom1.MNK[2]:
            return False
        # If at least one dimension of atom0 is smaller, then atom0 is strictly smaller
        return atom0.MNK[0] < atom1.MNK[0] or atom0.MNK[1] < atom1.MNK[1] or atom0.MNK[2] < atom1.MNK[2]
    largest_atoms = set()
    for atom in atoms:
        # If atoms is smaller than any of the largest atoms, skip it
        if any(is_smaller(atom, largest_atom) for largest_atom in largest_atoms):
            continue
        # remove any ellements in the largest atoms set that are strictly smaller than atom
        for largest_atom in list(largest_atoms):
            if is_smaller(largest_atom, atom):
                largest_atoms.remove(largest_atom)
        largest_atoms.add(atom)
    return list(largest_atoms)

def evenly_divides(a, b):
    return all([a % b == 0 for a, b in zip(a, b)])

def get_valid_atoms(MNKTileShape, dtype, acc_dtype):
    """Returns all the atoms that evenly divide the tile shape and which have compatible types
    """
    Dtype = torch_dtype_to_c(dtype)
    AccDtype = torch_dtype_to_c(acc_dtype)
    valid_atoms = []
    for atom in MMAAtom_registry.values():
        divides = evenly_divides(MNKTileShape, atom.MNK)
        valid_types = atom.A_type.value == Dtype and atom.B_type.value == Dtype and atom.C_type.value == AccDtype and atom.D_type.value == AccDtype
        if divides and valid_types:
            valid_atoms.append(atom)
    return valid_atoms

def reasonable_MNK_tile_shapes(M=None, N=None, K=None, MNK=None):
    """Generate a list of reasonable tile shapes for the MMA problem.
    """
    default_sizes = {1, 2, 4, 8, 16, 32, 64, 128}
    K_default_sizes = {1, 2, 4, 8, 16, 32, 64}
    M_sizes = default_sizes if M is None else {M,}
    N_sizes = default_sizes if N is None else {N,}
    K_sizes = K_default_sizes if K is None else {K,}
    for M in list(M_sizes):
        for N in list(N_sizes):
            for K in list(K_sizes):
                yield (M, N, K)

def reasonable_atom_placements(MNKTileShape, atom, max_threads):
    """Generate a list of reasonable atom placements for the MMA problem.
    """
    M_rest = MNKTileShape[0] // atom.MNK[0]
    N_rest = MNKTileShape[1] // atom.MNK[1]
    # Only loop over powers of 2
    for M in [2**i for i in range(0, M_rest.bit_length()) if 2**i <= M_rest]:
        for N in [2**j for j in range(0, N_rest.bit_length()) if 2**j <= N_rest]:
            if M * N * atom.thread_count > max_threads:
                continue
            yield (M, N, 1)

def dtype_to_bytes(dtype):
    if dtype in [th.float64, th.int64]:
        return 8
    elif dtype in [th.float32, th.int32]:
        return 4
    elif dtype in [th.float16, th.bfloat16, th.int16, th.uint16]:
        return 2
    elif dtype in [th.int8, th.uint8]:
        return 1
    raise ValueError(f"Unsupported dtype: {dtype}")

def safe_filter(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        arg_names = list(inspect.signature(fn).parameters.keys())
        n_args = dict(zip(arg_names, args))
        old_configs = copy(n_args['configs'])
        new_configs = fn(*args, **kwargs)
        if not new_configs:
            logger.warning(f"No configs passed {fn.__name__} filter, returning all {len(old_configs)} configs")
            return old_configs
        return new_configs
    return wrapper

def mma_smem_estimate(MNKTileShape, dtype, acc_dtype, smempipe=1):
    A_smem = MNKTileShape[0] * MNKTileShape[2] * dtype_to_bytes(dtype) * smempipe
    B_smem = MNKTileShape[1] * MNKTileShape[2] * dtype_to_bytes(dtype) * smempipe
    C_smem = MNKTileShape[0] * MNKTileShape[1] * dtype_to_bytes(acc_dtype)
    return max(A_smem + B_smem, C_smem)

def initial_config_sweep(MNKP, dtype, acc_dtype, M_tile=None, N_tile=None, K_tile=None, max_smem=SMEM_LIMIT, max_threads=MAX_THREADS_PER_BLOCK) -> List[Dict[str, Any]]:
    configs = []
    MNK = MNKP[:-1]
    # Generate an initial large list of reasonable configs
    for MNKTileShape in reasonable_MNK_tile_shapes(M_tile, N_tile, K_tile, MNK):
        if not evenly_divides(MNK, MNKTileShape):
            continue
        # Don't consider configs that use too much shared memory
        smem = mma_smem_estimate(MNKTileShape, dtype, acc_dtype)
        if smem > max_smem:
            continue
        for atom in get_valid_atoms(MNKTileShape, dtype, acc_dtype):
            for MNKAtomPlacement in reasonable_atom_placements(MNKTileShape, atom, max_threads):
                configs.append(dict(
                    MNKTileShape=MNKTileShape,
                    MNKAtomPlacement=MNKAtomPlacement,
                    Atom=atom,
                    dtype=dtype,
                    acc_dtype=acc_dtype,
                ))
    logger.info(f"Generated {len(configs)} initial mma configs")
    return configs

@safe_filter
def thread_count_filter(configs, aux):
    # If the candiate configs don't even use a full warp, pick the largerst one (relevant for small problems)
    thread_counts = [c['Atom'].thread_count * prod(c['MNKAtomPlacement']) for c in configs]
    max_thread_count = max(thread_counts)
    if max_thread_count <= 32:
        configs = [c for c, t in zip(configs, thread_counts) if t == max_thread_count]

    # If there are configs that use multiples of 32 threads filter out the rest
    if any([t % 32 == 0 for t in thread_counts]):
        configs = [c for c, t in zip(configs, thread_counts) if t % 32 == 0]
    logger.info(f"Filtered to {len(configs)} mma configs due to thread count")
    return configs

@safe_filter
def atom_size_filter(configs, aux):
    # Use the largest possible atom. Avoid benchmarking smaller instructions. TODO: verify this is a good idea
    largest_atoms = get_largest_atoms([c['Atom'] for c in configs])
    configs = [c for c in configs if c['Atom'] in largest_atoms]
    logger.info(f"Filtered to {len(configs)} mma configs for largest atoms")
    return configs

@safe_filter
def saturation_filter(configs, aux):
    MNKP = aux['MNKP']
    # If the problem does not saturate the GPU, pick the config with the largest number of C tiles
    C_tile_nums = [ (MNKP[0]//c['MNKTileShape'][0]) * (MNKP[1]//c['MNKTileShape'][1]) * MNKP[3] for c in configs]
    max_C_tile_num = max(C_tile_nums)
    if max_C_tile_num < SM_NUMBER:
        configs = [c for c, C_tile_num in zip(configs, C_tile_nums) if C_tile_num == max_C_tile_num]
    logger.info(f"Filtered to {len(configs)} mma configs for C tile count")
    return configs

@safe_filter
def arithmetic_intensity_filter(min_MN_tile_size, configs, aux):
    # We want to pick as large a MNTile as possible to imporove arithmetic intensity
    MN_tile_sizes = [c['MNKTileShape'][0] * c['MNKTileShape'][1] for c in configs]
    if any([MN_tile_size > min_MN_tile_size for MN_tile_size in MN_tile_sizes]):
        configs = [c for c, MN_tile_size in zip(configs, MN_tile_sizes) if MN_tile_size >= min_MN_tile_size]
    logger.info(f"Filtered to {len(configs)} mma configs for large MN tile size")
    return configs

def performance_expansion(configs, smempipe=None, regpipe=None, use_ldsm=None, swizzle=None):
    smempipes = [1, 2] if smempipe is None else (smempipe,) if not isinstance(smempipe, Iterable) else smempipe
    regpipes = [1] if regpipe is None else (regpipe,) if not isinstance(regpipe, Iterable) else regpipe
    use_ldsms = [True] if use_ldsm is None else (use_ldsm,) if not isinstance(use_ldsm, Iterable) else use_ldsm
    swizzles = [1] if swizzle is None else (swizzle,) if not isinstance(swizzle, Iterable) else swizzle

    new_configs = []
    for config in configs:
        for smempipe, regpipe, use_ldsm, swizzle in product(smempipes, regpipes, use_ldsms, swizzles):
            c = config.copy()
            c['smempipe'] = smempipe
            c['regpipe'] = regpipe
            c['use_ldsm'] = use_ldsm
            c['swizzle'] = swizzle
            if mma_smem_estimate(c['MNKTileShape'], c['dtype'], c['acc_dtype'], smempipe) > SMEM_LIMIT:
                continue
            new_configs.append(c)
    logger.info(f"Expanded to {len(new_configs)} configs with smempipe, regpipe, use_ldsm, swizzle for mma")
    return new_configs

def shape_conversion(configs):
    # ---- Massage the data so it's compatible with the kernel ----
    # We dont want to return full atom object, just the name
    configs = [{**c, 'Atom': c['Atom'].name} for c in configs]
    # We want the tile shape to be a cute Shape object
    configs = [{**c, 'MNKTileShape': static_shape(c['MNKTileShape'])} for c in configs]
    # Same for the atom placement
    configs = [{**c, 'MNKAtomPlacement': static_shape(c['MNKAtomPlacement'])} for c in configs]
    # Drop unwanted keys
    configs = [{k: v for k, v in c.items() if k not in ['dtype', 'acc_dtype']} for c in configs]
    logger.info(f"Filtered to {len(configs)} mma configs for kernel compatibility")
    return configs

def register_estimate(config, aux):
    # A rough and conservative estimate of the number of registers needed
    tile = config['MNKTileShape']
    a_reg = tile[0] * tile[2]
    b_reg = tile[1] * tile[2]
    c_reg = tile[0] * tile[1]
    return float(a_reg + b_reg + c_reg)

def register_per_thread_estimate(config, aux):
    # A rough and conservative estimate of the number of registers needed per thread
    tile = config['MNKTileShape']
    atom = config['Atom']
    placement = config['MNKAtomPlacement']
    rest_m, rest_n, rest_k = tile[0] // (atom.MNK[0] * placement[0]), tile[1] // (atom.MNK[1] * placement[1]), tile[2] // (atom.MNK[2] * placement[2])
    a_reg = atom.MNK[0] * atom.MNK[2] * rest_m * rest_k // 32
    b_reg = atom.MNK[1] * atom.MNK[2] * rest_n * rest_k // 32
    c_reg = atom.MNK[0] * atom.MNK[1] * rest_m * rest_n // 32

    return float(a_reg + b_reg + c_reg)

@safe_filter
def register_spillage_filter(configs, aux):
    # We want to avoid register spillage both on per thread level and on per SM level
    configs = [c for c in configs if register_estimate(c, aux) <= REG_PER_SM and register_per_thread_estimate(c, aux) <= 256]
    logger.info(f"Filtered to {len(configs)} mma configs for register spillage")
    return configs

@safe_filter
def register_underutil_filter(level, configs, aux):
    # We want to avoid underutilizing the registers, if we are using < x% of
    # max registers, we filter out the configs that are underutilized
    top_usage = sorted([register_estimate(c, aux) for c in configs], reverse=True)[0]
    configs = [c for c in configs if register_estimate(c, aux) >= top_usage * level]
    logger.info(f"Filtered to {len(configs)} mma configs for register underutilization")
    return configs

@safe_filter
def regpipe_filter(regpipes, configs, aux):
    # Filter out configs that use regpipe other than the ones we want to use
    configs = [c for c in configs if c['regpipe'] in regpipes]
    logger.info(f"Filtered to {len(configs)} mma configs for regpipe")
    return configs

@safe_filter
def smempipe_filter(smempipes, configs, aux):
    # Filter out configs that use smempipe other than the ones we want to use
    configs = [c for c in configs if c['smempipe'] in smempipes]
    logger.info(f"Filtered to {len(configs)} mma configs for smempipe")
    return configs

@safe_filter
def warp_filter(num_warps, configs, aux):
    # Filter out configs that use more warps than the number of warps we want to use
    configs = [c for c in configs if prod(c['MNKAtomPlacement']) <= num_warps]
    logger.info(f"Filtered to {len(configs)} mma configs for warp size")
    return configs

def make_configurator(filter_funcs):

    @lru_cache(maxsize=None)
    def mma_config_sweep(MNKP, dtype, acc_dtype, M_tile=None, N_tile=None, K_tile=None, smempipe=None, regpipe=None, use_ldsm=None, swizzle=None, max_smem=SMEM_LIMIT, max_threads=MAX_THREADS_PER_BLOCK) -> List[Dict[str, Any]]:
        """Given an MMA problem, return a list of configs that can be used to configure any of the MMA kernels.
        Args:
            MNK: The shape of the MMA problem.
            dtype: The data type of the A, B matrices.
            acc_dtype: The data type of the C accumulator. (could be different from the C.dtype)
            M_tile (optional): The M_tile size
            N_tile (optional): The N_tile size
            K_tile (optional): The K_tile size
        Each returned config is a dict with keys:
            - MNKTileShape: The shape of the tile to use for the MMA kernel. Must divide the problem shape
            - Atom: The atom (MMA instruction) to use
            - MNKAtomPlacement: How to replicate the atoms across more threads of the CTA.
            Eg, if the instruction is warp level, then MNKAtomPlacement will control the number of warps in the CTA.
        
        We try to filter out as many valid configs as possible to speed up the sweeps. For example
            - We only return configs that use the largest possible atoms. If a 16x8x16 atom is valid we don't need to consider 16x8x8 or FMA based matmuls
            - We can filter out any configs that use too much shared memory
            - For small problems using < 32 threads, we return configs that use the maximum number of threads
            - Since the size of the MN tile controls the amount of gmem reloading, we only consider MN tiles >= 1024 if the setting allows it
        """
        aux = dict(
            MNKP=MNKP,
            dtype=dtype,
            acc_dtype=acc_dtype,
            M_tile=M_tile,
            N_tile=N_tile,
            K_tile=K_tile,
            max_smem=max_smem,
            max_threads=max_threads,
            smempipe=smempipe,
            regpipe=regpipe,
            use_ldsm=use_ldsm,
            swizzle=swizzle,
        )
        configs = initial_config_sweep(MNKP, dtype, acc_dtype, M_tile, N_tile, K_tile, max_smem, max_threads)
        configs = performance_expansion(configs, smempipe, regpipe, use_ldsm, swizzle)
        for filter_func in filter_funcs:
            configs = filter_func(configs, aux)

        configs = shape_conversion(configs)
        return configs
    
    return mma_config_sweep
    

# The following configurators are heuristics used to prune configs that are likely to have bad performance
# However there's no guarantee that the the top-performing config is not filtered out.
no_filter_configurator = make_configurator([])

base_configurator = make_configurator([
    thread_count_filter, # For small problems, we want to use the maximum number of threads
    atom_size_filter, # Use the largest possible atom. Avoid benchmarking smaller instructions.
    register_spillage_filter, # Avoid register spillage
    saturation_filter, # If the problem does not saturate the GPU, pick the config with the largest number of C tiles
    partial(arithmetic_intensity_filter, 2048), # We want to pick as large a MNTile as possible to imporove arithmetic intensity
])

advanced_configurator = make_configurator([
    thread_count_filter,
    atom_size_filter,
    register_spillage_filter, # Avoid register spillage
    saturation_filter,
    partial(arithmetic_intensity_filter, 2048),
    partial(register_underutil_filter, 0.4), # Avoid underutilizing the registers relative to maximum register usage
    partial(warp_filter, 4), # Avoid using more warps than the number of warps we want to use
    partial(smempipe_filter, [1, 2]), # Smempipe 1 and 2 are the only ones we want to use
    partial(regpipe_filter, [1]), # Regpipe 1 is probably good enough
])




