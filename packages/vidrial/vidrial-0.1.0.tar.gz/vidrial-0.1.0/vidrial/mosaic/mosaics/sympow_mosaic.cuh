#pragma once
#include "tprod_mosaic.cuh"
#include "../utils/sympow.cuh"
#include "perf_mosaic.cuh"

namespace mosaic {

template<typename Mosaic>
struct SympowCoords {
    static constexpr auto d = Mosaic::d; // feature dim
    static constexpr auto b = Mosaic::b; // batch dim
    static constexpr auto d_tile = Mosaic::d_tile; // size of the tile d
    static constexpr auto b_tile = Mosaic::b_tile; // size of the tile b
    static constexpr auto power = Mosaic::p;
    // The two iterators for the d,b dimensions
    using DTileSeq = NonDecSeq<d/d_tile, power>;
    DTileSeq D_tile_iter{};
    int b_tile_idx = 0;
    // Number of tiles along the D
    static constexpr auto D_tile_num = DTileSeq::num_elements;
    CUTE_HOST_DEVICE auto slice_Z_tile(auto& Z) {
        // static_assert(is_compatible<decltype(Z), typename Mosaic::ZTileShape>::value, "Z must have the same shape as the tile");
        auto tile_coord = make_coord(D_tile_iter.idx, b_tile_idx);
        return slice_rest(Z, Mosaic{}.Z.TileBlock, tile_coord);
    }
    /* Slices out all the features and a tile of the batch
    output shape = [d, b_tile]. */
    template<int i>
    CUTE_HOST_DEVICE auto slice_X_tile(auto& X) {
        auto tile_coord = make_coord(D_tile_iter.seq, b_tile_idx);
        return slice_rest(X, get<i>(Mosaic{}.Xi).TileBlock, tile_coord);
    }
    template<int i>
    CUTE_HOST_DEVICE auto slice_X_tile_from_batch(auto& X) {
        auto tile_coord = make_coord(D_tile_iter.seq, _0{});
        return slice_rest(X, get<i>(Mosaic{}.Xi).TileBlock, tile_coord);
    }
    /* Slices out all the features and a tile of the batch
    output shape = [d, b_tile]. */
    CUTE_HOST_DEVICE auto slice_X_batch(auto& X) {
        auto X_batch_shape = make_shape(Int<d>{}, Int<b_tile>{});
        auto X_tiled = zipped_divide(X, X_batch_shape);
        return slice_rest(X_tiled, make_coord(_0{},b_tile_idx));
    }
    CUTE_HOST_DEVICE float scale_correction() {
        return sqrtf(D_tile_iter.duplicate_count());
    }
    CUTE_HOST_DEVICE auto D_coord() {return D_tile_iter.idx; }
    CUTE_HOST_DEVICE auto b_coord() { return b_tile_idx; }
    CUTE_HOST_DEVICE void step_D(int step = 1) { D_tile_iter += step; }
    CUTE_HOST_DEVICE void step_b(int step = 1) { b_tile_idx += step; }
    CUTE_HOST_DEVICE bool valid_D_tile() { return D_tile_iter.idx < D_tile_num; }
    CUTE_HOST_DEVICE bool valid_b_tile(int b) { return b_tile_idx * b_tile < b; }
    CUTE_HOST_DEVICE void reset_D() { D_tile_iter.reset(); }
    CUTE_HOST_DEVICE void reset_b() { b_tile_idx = 0; }
    CUTE_HOST_DEVICE void reset() { reset_D(); reset_b(); }
};

/* This class is very similar to a Copy Mosaic, but it uses slightly dfferent layouts
that are needed to work with a symmetric power. If X is [[d,d],b]. And we are taking
second power, feature block dk and batch block bk then:
- Z.shape() = [[[dk,dk],l],b] where l is the number of feature blocks
- Z_Tile = [[dk,dk],bk]
- Z_TileBlock = [Z_Tile,[l,nb]]
- Z_FrgThr is the same that it would be for a copy mosaic
*/
template<typename T, int _thread_num, int p,
         typename XSlabShape, typename XTileShape,
         typename _GZSlab, typename SZTile>
struct SympowZTilingMosaic {
    using GZSlab = _GZSlab;
    GZSlab gSlab;
    SZTile sTile;
    static constexpr int thread_num = _thread_num;
    static_assert(rank(XSlabShape{}) == 2);
    static_assert(rank(XTileShape{}) == 2);
    static constexpr auto d = get<0>(XSlabShape{});
    static constexpr auto b = get<1>(XSlabShape{});
    static constexpr auto d_tile = get<0>(XTileShape{});
    using ZSlabShape = decltype(sympow_shape<p, d_tile>(XSlabShape{})); // [[[d_tile, d_tile, ...], N_sympow], b]
    static_assert(compatible(ZSlabShape{}, shape(GZSlab{})));
    using ZTileShape = decltype(tpow_shape<p>(XTileShape{})); // [[d_tile, d_tile, ...], b_tile]
    ZTileShape TileShape;
    static constexpr auto pad_TB(auto ZLayout) {
        auto feature_tile_shape = make_shape(get<0>(ZTileShape{}),_1{}); // [[d_tile, d_tile, ...], 1]
        auto tile_shape = make_shape(feature_tile_shape, get<1>(ZTileShape{})); // [[[d_tile, d_tile, ...], 1], b_tile]
        auto TB = zipped_divide(ZLayout, tile_shape); // [[[[d_tile, d_tile, ...], 1], b_tile], [[d_rest, d_rest, ...], N_rest], b_rest]
        auto TileLayout = make_layout(get<0,0,0>(TB),get<0,1>(TB)); // [[d_tile, d_tile, ...], b_tile]
        return make_layout(TileLayout, get<1>(TB)); // [[[d_tile, d_tile, ...], b_tile], [[d_rest, d_rest, ...], N_rest], b_rest]
    }
    using ZTileBlock = decltype(pad_TB(make_layout(ZSlabShape{}))); // [[[d_tile, d_tile, ...], b_tile], [[d_rest, d_rest, ...], N_rest], b_rest]
    using GZTile = decltype(get<0>(pad_TB(GZSlab{}))); // [[d_tile, d_tile, ...], b_tile]
    GZTile gTile;
    using TileCopy = CopyMosaic_sm80<T, thread_num, ZTileShape, GZTile, SZTile>;
    ZTileBlock TileBlock;
    TileCopy tile_copy;
};

/* This class combines TprodM + SymmetricCoords to perform all the computations on
data of the shape of ZSympowMosaic.
    - Z: [[td,td,...],r],b] where r=size(sym_coords)  Y is basically a list of cubes
    - X_batch_copy to move all the features of a batch [[d],bk]
    - Y: [[d,d],b] you most likely only want to work with tiles of Y
    - X0,X1: the factors of the tprod Y
*/
template <typename _T, int _p, typename _XSlabShape, typename _XTileShape, typename ZFrgThr, 
          typename GZSlab, typename GXSlab, typename SZTile, typename _PerfMosaic = DefaultPerf>
struct SympowMosaic {
    using T = _T;
    static constexpr int p = _p;
    using XSlabShape = _XSlabShape; // [d, b]
    static constexpr int d = size<0>(XSlabShape{});
    static constexpr int b = size<1>(XSlabShape{});
    using XTileShape = _XTileShape; // [d_tile, b_tile]
    static constexpr int b_tile = size<1>(XTileShape{});
    using YShape = decltype(static_tree_cast<int64_t>(tpow_shape<p>(XSlabShape{}))); // [[d, d, ...], b]
    using ZTileShape = decltype(tpow_shape<p>(XTileShape{})); // [[d_tile, d_tile, ...], b_tile]
    using YSlab = Layout<YShape>; // the virtual tensor that should not be materialized // [[d, d, ...], b]
    template<typename... GXiSlab>
    static constexpr auto get_Tprod(tuple<GXiSlab...> t) {
        return TprodMosaic<T, ZTileShape, ZFrgThr, SZTile, YSlab, GXiSlab...>{};
    }
    using TprodM = decltype(get_Tprod(repeat<p>(GXSlab{})));
    static constexpr TprodM tprod{};
    static constexpr int thread_num = TprodM::thread_num;
    using Xi_t = typename TprodM::Xi_t;
    using Y_t = typename TprodM::Y_t;
    using Z_t = SympowZTilingMosaic<T, thread_num, p, XSlabShape, XTileShape, GZSlab, SZTile>;
    Y_t Y;
    Xi_t Xi;
    Z_t Z;
    using PerfMosaic = _PerfMosaic;
    static constexpr PerfMosaic perf{};
    static constexpr int d_tile = size<0>(get<0>(tprod.Xi).Tile);
    using SympowCoords = NonDecSeq<size<0>(get<0>(tprod.Xi).gSlab) / d_tile, p>;
    static constexpr int d_tile_num = SympowCoords::num_elements;
    static_assert(d_tile_num==size<0,1>(GZSlab{}));
    struct XBatching { // used to move batches of X (containing all the features)
        using XBatchShape = decltype(make_shape(get<0>(XSlabShape{}), get<1>(XTileShape{}))); // [d, b_tile]
        static constexpr auto get_X_BatchBlock(auto XLayout) {
            auto TB = zipped_divide(XLayout, XBatchShape{}); // [[d, b_tile], [1, b_rest]]
            static_assert(size<1,0>(TB)==1); // there should be no blocks along the feature dim
            return make_layout(get<0>(TB), get<1,1>(TB));
        }
        using XBatchBlock_t = decltype(get_X_BatchBlock(make_layout(XSlabShape{}))); // [[d, b_tile], b_rest]
        using GXBatch = decltype(get<0>(get_X_BatchBlock(GXSlab{}))); // [d, b_tile]
        using SXBatch = decltype(default_sTile(GXSlab{}, XBatchShape{})); // [d, b_tile]
        using XBatchCopy = CopyMosaic_sm80<T, thread_num, XBatchShape, GXBatch, SXBatch>;
        XBatchBlock_t BatchBlock;
        GXSlab gSlab;
        SXBatch sBatch;
        XBatchCopy batch_copy;
    };
    XBatching X;
};

template <typename T, int p>
auto make_sympow_mosaic(auto Z_frg_shape, auto X_tile_shape, auto gZ_slab, auto gX_slab, auto sZ_tile) {
    static_assert(rank(gZ_slab)==2 && rank<0>(gZ_slab)==2 && rank<0,0>(gZ_slab)==p);
    static_assert(size<0,0,0>(gZ_slab)==size<0>(X_tile_shape)); // feature dims match
    static_assert(size<1>(gZ_slab)==size<1>(gX_slab)); // batch dims match
    // auto X_slab_shape = make_shape(size<0>(gX_slab), size<1>(gX_slab));
    auto X_slab_shape = gX_slab.shape();
    auto Z_tile_shape = tpow_shape<p>(X_tile_shape);
    using ZFrgThr = decltype(zipped_divide(make_layout(Z_tile_shape), Z_frg_shape));
    auto mos = SympowMosaic<T, p, decltype(X_slab_shape), decltype(X_tile_shape), ZFrgThr,
                                 decltype(gZ_slab), decltype(gX_slab), decltype(sZ_tile)>{};
    return mos;
}

// -------------- Mosaic Printing --------------
template<typename T, int _thread_num, int p,
         typename XSlabShape, typename XTileShape,
         typename _GZSlab, typename SZTile>
CUTE_HOST void print_mosaic(const SympowZTilingMosaic<T, _thread_num, p, XSlabShape, XTileShape, _GZSlab, SZTile> mos, const char* prefix = "") {
    print(prefix); print("SympowZTilingMosaic:\n");
    std::string prefix_str = std::string(prefix) + "  ";
    const char* _prefix = prefix_str.c_str();
    print(_prefix); print("gSlab: "); print(mos.gSlab); print("\n");
    print(_prefix); print("thread_num: "); print(mos.thread_num); print("\n");
    print_mosaic(mos.tile_copy, _prefix);
}

template <typename _T, int _p, typename _XSlabShape, typename _XTileShape, typename ZFrgThr, 
          typename GZSlab, typename GXSlab, typename SZTile, typename _PerfMosaic>
CUTE_HOST void print_mosaic(const SympowMosaic<_T, _p, _XSlabShape, _XTileShape, ZFrgThr, GZSlab, GXSlab, SZTile, _PerfMosaic> mos, const char* prefix = "") {
    print(prefix); print("SympowMosaic:\n");
    std::string prefix_str = std::string(prefix) + "  ";
    const char* _prefix = prefix_str.c_str();
    print(_prefix); print("thread_num: "); print(mos.thread_num); print("\n");
    print(_prefix); print("d_tile: "); print(mos.d_tile); print("\n");
    print(_prefix); print("d_tile_num: "); print(mos.d_tile_num); print("\n");
    print_mosaic(mos.Z, _prefix);
    print_mosaic(mos.tprod, _prefix);

    print(_prefix); print("X:\n");
    std::string _prefix_str = std::string(_prefix) + "  ";
    const char* __prefix = _prefix_str.c_str();
    print(__prefix); print("BatchBlock: "); print(mos.X.BatchBlock); print("\n");
    print(__prefix); print("gSlab: "); print(mos.X.gSlab); print("\n");
    print(__prefix); print("sBatch: "); print(mos.X.sBatch); print("\n");
    print_mosaic(mos.X.batch_copy, __prefix);
}

} // namespace mosaic