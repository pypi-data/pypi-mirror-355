#pragma once
#include "../../mosaic/mosaics/sympow_mma_mosaic.cuh"
#include "../sympow_bwd/kernel.cuh"
#include "../sympow_mma/kernel.cuh"
#include "../../cutlass/include/cute/tensor.hpp"
#include "../../cutlass/include/cute/tensor_impl.hpp"

namespace mosaic {

/* Mosaic where the expanded object is C along the M dimension
X = c
*/
template<typename T, int _pow, typename MmaAtom, typename MNKAtomPlacement, typename _MNKPSlabShape, typename MNKTileShape,
         int d, int d_tile, typename _GASlab, typename _GBSlab, typename _GcSlab>
struct SympowCMmaMosaic {
    static constexpr int pow = _pow;
    using GASlab = decltype(static_tree_cast<int64_t>(_GASlab{}));
    using GBSlab = decltype(static_tree_cast<int64_t>(_GBSlab{}));
    using GcSlab = decltype(static_tree_cast<int64_t>(_GcSlab{}));
    using MNKAtomLayout = Layout<Shape<_1,_1,_1>>; // generic layouts not implemented
    using MNKPSlabShape = decltype(static_tree_cast<int64_t>(_MNKPSlabShape{}));
    static constexpr long M=get<0>(MNKPSlabShape{}),N=get<1>(MNKPSlabShape{}),K=get<2>(MNKPSlabShape{}),P=get<3>(MNKPSlabShape{}); 
    static constexpr long M_tile=get<0>(MNKTileShape{}),N_tile=get<1>(MNKTileShape{}),K_tile=get<2>(MNKTileShape{}); 
    static constexpr int D = get<0>(MNKPSlabShape{});
    static constexpr int D_tile = static_pow<pow>(d_tile);
    static_assert(D == sympow_dim<pow, d, d_tile>());
    static_assert(D_tile == get<0>(MNKTileShape{}), "D_tile mismatch with M_tile");
    static constexpr int D_tile_num = sympow_dim<pow, d/d_tile>();
    using CSlabShape = decltype(ABC_get_MNKP(C_t{}, MNKPSlabShape{}));
    using CTileShape = decltype(ABC_get_MNK(C_t{}, MNKTileShape{}));
    using cSlabShape = Shape<Int<d>,Int<N>,Int<P>>; // similar to XSlabShape = [d,[N,P]]
    using XSlabShape = Shape<Int<d>,Shape<Int<N>,Int<P>>>;
    using cTileShape = Shape<Int<d_tile>,Int<N_tile>>; // same as XTileShape
    using XTileShape = cTileShape; // same as XTileShape
    using c2XSlab = Layout<XSlabShape>; // [d,N,P] -> [d,[N,P]]
    using X2cSlab = decltype(group<1,3>(Layout<cSlabShape>{})); // [d,[N,P]] -> [d,N,P]
    using c2XTile = Layout<XTileShape>; // [d_tile,N_tile] -> [d_tile,N_tile]
    using C2ZTile = Layout<CTileShape>; // [D_tile,N_tile] -> [d_tile^p,N_tile]
    using ZSlabShape = decltype(static_tree_cast<int64_t>(Shape<Int<D>,Shape<Int<N>,Int<P>>>{})); // [D,[N,P]]
    using C2ZSlab = decltype(flatten(Layout<ZSlabShape>{})); // [D,N,P] -> [D,[N,P]]
    using ZTileShape = decltype(tpow_shape<pow>(XTileShape{}));
    using GXSlab = decltype(GcSlab{}.compose(X2cSlab{})); // gX_slab is a view of gc_slab
    using GZSlab = decltype(make_layout(static_tree_cast<int64_t>(sympow_shape<pow,d_tile>(XSlabShape{})))); // virtual
    using GCSlab = decltype(GZSlab{}.compose(C2ZSlab{})); // virtual
    GXSlab gXSlab;
    static_assert(size(GZSlab{}) == size(GCSlab{}));
    using MmaMosaic = decltype(make_mma_mosaic<T, DefaultPerf, MmaAtom, MNKAtomPlacement>(MNKTileShape{}, MmaAtom{}, MNKAtomPlacement{}, GASlab{}, GBSlab{}, GCSlab{}));
    static constexpr MmaMosaic mma{};
    MmaAtom mma_Atom{};
    decltype(mma.A) A;
    decltype(mma.B) B;
    decltype(mma.C) C;
    using FrgTypeA = typename MmaMosaic::FrgTypeA;
    using FrgTypeB = typename MmaMosaic::FrgTypeB;
    using FrgTypeC = typename MmaMosaic::FrgTypeC;
    static constexpr int thread_num = mma.thread_num;
    static_assert(size(ZTileShape{}) == size(decltype(C){}.tileShape));
    using _ZMmaFrgThr = decltype(C2ZTile{}.compose(C.mma_FrgThr));
    using _ZTprodFrgThr = decltype(colayout(ZTileShape{}, get<0>(_ZMmaFrgThr{}))); // colayout transforms the mma_frg layout into a format compatible with tprod
    using ZTprodFrgThr = decltype(make_layout(_ZTprodFrgThr{}, get<1>(_ZMmaFrgThr{})));
    static_assert(size(ZTprodFrgThr{}) == size(ZTileShape{}));
    using CTprodFrgThr_Frg = decltype(left_inverse(C2ZTile{}).compose(get<0>(ZTprodFrgThr{}))); // maps tprod_frg_coords -> C_coords
    using YTprod__2__CMma__frg = decltype(left_inverse(get<0>(C.mma_FrgThr)).compose(CTprodFrgThr_Frg{})); // C_tprod_frg_coords -> Y_tprod_frg_coords
    YTprod__2__CMma__frg Y_tprod_frg__2__C_mma_frg;
    using SZTile = Layout<ZTileShape>; // virtual (we don't even store the expansions in smem)
    using Sympow = SympowMosaic<T, pow, XSlabShape, XTileShape, ZTprodFrgThr, GZSlab, GXSlab, SZTile>;
    Sympow sympow;
    using SympowCoords = typename Sympow::SympowCoords;
    using Xi_t = decltype(typename Sympow::Xi_t{});
    Xi_t Xi;
    Sympow::XBatching X;
    Sympow::Y_t Y;
    Sympow::Z_t Z;
    using Xi_size_t = decltype(transform(Xi_t{}, [](auto const& x) { return size(x.sTile); }));
    using Xi_offset_t = decltype(get<1>(fold(Xi_size_t{}, make_tuple(_0{},make_tuple()),
            [](auto const& carry, auto const& Xi_size) {
                    auto [current, offsets] = carry;
                    return make_tuple(current+Xi_size, append(offsets, current)); })));
    using X_size_t = decltype(fold(Xi_size_t{}, _0{}, [](auto const& a, auto const& b) { return a + b; }));
    static constexpr Xi_size_t Xi_smem_size{};
    static constexpr Xi_offset_t Xi_smem_offset{};
    static constexpr X_size_t X_smem_size{};
};

/* ----- fused sympow mma kernel -----
 * This kernel is a function A,B,c -> cdot = sympow_bwd(c, A@B)
 *     (used in the implementation of sympowA_mma_bwd)
 * Kernel uses 2 different coordinate systems for the 2 operations
 *   dims M,N,K,P
 *   A_slab = [M,K,P]  A_tile = [M_tile,K_tile]
 *   B_slab = [N,K,P]  B_tile = [N_tile,K_tile]
 *   C_slab = [M,N,P]  C_tile = [M_tile,N_tile]
 *   dims d,b: using d=M and b=[K,P]
 *   X_slab = [d,b]    X_tile = [d_tile,b_tile]
 *   Z_slab = [D,b]  Z_tile = [D_tile,b_tile]
 *   where D_tile = [d_tile,...]  (repeated power times)
 *   and D = [D_tile,d_tile_num]
 * The two systems are connected via
 *   D = M   and  b = [N,P] and b_tile = [N_tile,1]
 *   Z_slab = [D,[N,P]], X_slab = [d,[N,P]]
 *   C_tile = Z_tile = [D_tile,N_tile], c_tile = X_tile = [d_tile,N_tile]
 * Each CTA in the grid computes an Xgrad_batch of shape [d, b_tile]
 *   CTA_idx = [N_tile_idx, P_tile_idx] (constant through execution)
 *   so that each CTA computes a different c_tile
 * The mainloop has 2 nested loops:
 *   D_tile_idx  ranges  0 -> mos.D_tile_num
 *       K_tile_idx  ranges  0 -> mos.K_tile_num
*/ 
template <bool duplicate_correction, int smempipe_, auto... Is, typename Mosaic, typename AT, typename BT, typename CT>
__device__ void mma_sympow_bwd_kernel_impl(int_sequence<Is...>, Mosaic mos, AT* A_ptr, BT* B_ptr, CT* c_ptr, CT* cgrad_ptr) {
    int tid = threadIdx.x;
    int N_tile_idx = blockIdx.y;
    int P_tile_idx = blockIdx.z;
    // ----- Iterators of the kernel -----
    auto mma_tile_coords = MmaMNKCoords(mos.mma.MNK_tile_shape);
    mma_tile_coords.step_N(N_tile_idx);
    mma_tile_coords.step_P(P_tile_idx);
    auto sympow_tile_coords = SympowCoords<decltype(mos.sympow)>{};
    sympow_tile_coords.step_b(N_tile_idx + mos.mma.N_tile_num * P_tile_idx); // b_tile_idx = [N_tile_idx, P_tile_idx]
    // ------ Global memory slabs ------
    auto gA_slab = make_tensor(make_gmem_ptr(A_ptr), mos.A.gSlab);
    auto gB_slab = make_tensor(make_gmem_ptr(B_ptr), mos.B.gSlab);
    auto gX_slab = make_tensor(make_gmem_ptr(c_ptr), mos.X.gSlab); // gc and gX are equivalent
    auto gXgrad_slab = make_tensor(make_gmem_ptr(cgrad_ptr), mos.gXSlab);
    auto gX_batch = sympow_tile_coords.slice_X_batch(gX_slab);
    // ------ Shared memory tensors ------
    __shared__ CT X_smem[int(cosize(mos.X.sBatch))]; // [d, b_tile]
    __shared__ CT Xgrd_smem[int(cosize(mos.X.sBatch))]; // [d, b_tile]
    auto sX_batch = make_tensor(make_smem_ptr(X_smem), mos.X.sBatch); // [d, b_tile]
    auto sXgrad_batch = make_tensor(make_smem_ptr(Xgrd_smem), mos.X.sBatch); // [d, b_tile]
    CTA_copy_tile(mos.X.batch_copy, gX_batch, sX_batch);
    clear(slice_rest(sXgrad_batch, mos.X.batch_copy.FrgThr, tid)); // Every thread clears a fragment of the Xgrad_batch
    cp_async_fence(); cp_async_wait<0>(); __syncthreads();
    // ------ Register fragments for mma and tprod operations ------
    auto rA_frg_mma = mos.A.make_mma_frg();
    auto rB_frg_mma = mos.B.make_mma_frg();
    auto rC_frg_mma = mos.C.make_mma_frg();
    clear(rC_frg_mma);
    auto rYgrad_tprod_frg = rC_frg_mma.compose(mos.Y_tprod_frg__2__C_mma_frg);
    using YFrgType = TensorType(rYgrad_tprod_frg);
    // ------ Main loop ------
    while (sympow_tile_coords.valid_D_tile()) {
        // Compute rYgrad_tprod_frg (A@B is the gradient of an expanded C tile)
        clear(rC_frg_mma); // equivalent to clearing rYgrad_tprod_frg
        while (mma_tile_coords.valid_K_tile(mos.K)) {
            auto gA_tile = mma_tile_coords.slice_A_tile(gA_slab);
            auto gB_tile = mma_tile_coords.slice_B_tile(gB_slab);
            copy(slice_rest(gA_tile, mos.A.mma_FrgThr, tid), rA_frg_mma);
            copy(slice_rest(gB_tile, mos.B.mma_FrgThr, tid), rB_frg_mma);
            cute::gemm(mos.mma_Atom, rA_frg_mma, rB_frg_mma, rC_frg_mma);
            mma_tile_coords.step_K();
        }
        mma_tile_coords.reset_K(); // Next iteration of the main loop we need to do a full reduction over N again
        if constexpr (duplicate_correction)
            tensor_scalar_prod(rYgrad_tprod_frg, static_cast<YFrgType>(sympow_tile_coords.scale_correction()));
        // We are ready to perform an accumulation step onto Xigrad using the Ygrad_frg
        auto rXi_tprod_frg = make_tuple(make_tensor<YFrgType>(get<Is>(mos.Xi).Frg)...);
        (..., [&]() { // s2r load of Xi_tprod_frg. Could be optimized by only loading the Xi fragment when the index has changed
            auto sXi_tile = sympow_tile_coords.slice_X_tile_from_batch<Is>(sX_batch);
            auto sXi_tprod_frg = slice_rest(sXi_tile, get<Is>(mos.Xi).tprod_FrgThr, tid);
            copy(sXi_tprod_frg, get<Is>(rXi_tprod_frg));
        }());
        // slice the Xgrad fragments for accumulation
        auto sXigrad_copy_frg = make_tuple(slice_rest(sympow_tile_coords.slice_X_tile_from_batch<Is>(sXgrad_batch),
                                                      get<Is>(mos.Xi).tile_copy.FrgThr,
                                                      tid)...);
        CTA_tprod_bwd<Is...>(mos, rYgrad_tprod_frg, rXi_tprod_frg, sXigrad_copy_frg, tid);
        sympow_tile_coords.step_D();
        mma_tile_coords.step_M();
        __syncthreads(); // sXigrad_batch is being accumulated. Wait untill all threads are done.
    }
    // ------ Write X_tile to global memory ------
    auto gXgrad_batch = sympow_tile_coords.slice_X_batch(gXgrad_slab);
    CTA_copy_tile(mos.X.batch_copy, sXgrad_batch, gXgrad_batch);
}
template <bool duplicate_correction, int smempipe, typename Mosaic, typename AT, typename BT, typename CT>
__global__ void mma_sympow_bwd_kernel(Mosaic mos, AT* a_ptr, BT* B_ptr, CT* c_ptr, CT* Cgrad_ptr) {
    mma_sympow_bwd_kernel_impl<duplicate_correction, smempipe>(make_int_sequence<mos.pow>{}, mos, a_ptr, B_ptr, c_ptr, Cgrad_ptr);
}

template<bool duplicate_correction=true, int smempipe=1, typename Mosaic, typename AT, typename BT, typename CT>
void launch_mma_sympow_bwd_kernel(Mosaic mos, AT* a_ptr, BT* B_ptr, CT* c_ptr, CT* cgrad_ptr) {
    dim3 blocks(1, mos.mma.N_tile_num, mos.mma.P);
    int threads = mos.thread_num;
    mma_sympow_bwd_kernel<duplicate_correction, smempipe, Mosaic, AT, BT, CT><<<blocks,threads>>>(mos, a_ptr, B_ptr, c_ptr, cgrad_ptr);
}

} // namespace mosaic