#pragma once
#include <iostream>
#include <cute/tensor.hpp>
#include "../utils/tprod.cuh"
#include <typeinfo>
#include <type_traits>
#include <tuple>
#include "copy_mosaic.cuh"

namespace mosaic {

template <typename _T, typename GY,
          typename _TileShape, typename STile,
          typename _FrgThr>
struct YTprodMosaic {
    using T = _T;
    using GSlab = decltype(static_tree_cast<int64_t>(GY{})); // [[d, d, ...], b]
    using TileShape_t = _TileShape; // [[d_tile, d_tile, ...], b_tile]
    TileShape_t TileShape;
    STile sTile;
    static_assert(rank(GSlab{}) == 2);
    static constexpr int feature_rank = rank<0>(GSlab{});
    using FrgThr_t = _FrgThr;
    GSlab gSlab;
    FrgThr_t tprod_FrgThr;
    static constexpr int thread_num = size<1>(FrgThr_t{});
    using Frg_t = decltype(make_layout(get<0>(FrgThr_t{}.shape())));
    Frg_t Frg;
    using Tile_t = decltype(make_layout(TileShape_t{}));
    Tile_t Tile;
    using TileBlock_t = decltype(zipped_divide(make_layout(GSlab{}.shape()), TileShape_t{})); // [[[d_tile, d_tile, ...], b_tile], [[d_rest, d_rest, ...], b_rest]], and a layout
    TileBlock_t TileBlock;
    static_assert(is_static<FrgThr_t>::value);
    using GTile = decltype(get<0>(zipped_divide(GSlab{}, TileShape_t{})));
    using TileCopy = CopyMosaic_sm80<T, thread_num, TileShape_t, GTile, STile>;
    TileCopy tile_copy;
};

template <typename YMosaic, int component, typename GY>
struct XTprodMosaic {
    using T = typename YMosaic::T;
    using YTileShape_t = typename YMosaic::TileShape_t; // [[d_tile, d_tile, ...], b_tile]
    using YTileBlock_t = typename YMosaic::TileBlock_t; // [[[d_tile, d_tile, ...], b_tile], [[d_rest, d_rest, ...], b_rest]], and a layout
    using YFrgThr_t = typename YMosaic::FrgThr_t;
    using YGSlab = typename YMosaic::GSlab; // [[d, d, ...], b]
    static constexpr int thread_num = YMosaic::thread_num;
    static_assert(component < YMosaic::feature_rank);

    using GSlab = GY;
    using TileShape_t = decltype(make_shape(get<0,component>(YTileShape_t{}), get<1>(YTileShape_t{})));
    using Tile_t = decltype(make_layout(TileShape_t{}));
    using TileBlock_t = decltype(tprod_factor_project<component>(YGSlab{}.shape(), YTileBlock_t{}));
    GSlab gSlab;
    TileShape_t TileShape;
    Tile_t Tile;
    TileBlock_t TileBlock;
    using TprodFrgThr_t = decltype(tprod_factor_project<component>(YTileShape_t{}, YFrgThr_t{}));
    using TprodFrg_t = decltype(make_layout(get<0>(TprodFrgThr_t{}.shape())));
    TprodFrgThr_t tprod_FrgThr;
    TprodFrg_t Frg;
    static_assert(is_static<TileBlock_t>::value);
    static_assert(is_static<TprodFrgThr_t>::value);

    using GTile = decltype(get<0>(zipped_divide(GSlab{}, TileShape_t{})));
    using STile = decltype(default_sTile(GSlab{}, TileShape_t{}));
    STile sTile;
    using TileCopy = CopyMosaic_sm80<T, thread_num, TileShape_t, GTile, STile>;
    TileCopy tile_copy;
};

template <typename _T, typename YTileShape_t, typename YFrgThr, typename SYTile,
          typename GY, typename... GXi>
struct TprodMosaic {
    static constexpr int tprod_rank = sizeof...(GXi);
    static_assert(tprod_rank > 0);
    // GY, GX0, ... all must be batched tensors: [feature, batch]
    static_assert(rank(GY{}) == 2);
    static_assert(((rank(GXi{}) == 2) && ...));
    // GY should have 2 feature dims (due to the Rank2 in the name)
    static_assert(rank<0>(GY{}) == tprod_rank); 
    // GY.shape() should compatible with the tprod of GXi
    static_assert(shape(GY{}) == tprod_shape(GXi{}.shape()...));
    using T = _T;
    using Y_t = YTprodMosaic<T, GY, YTileShape_t, SYTile, YFrgThr>;
    template<auto... Is>
    static constexpr auto get_Xi_t(index_sequence<Is...> seq) {
        return make_tuple(XTprodMosaic<Y_t, Is, GXi>{}...);
    }
    using Xi_t = decltype(get_Xi_t(make_index_sequence<tprod_rank>{}));
    Y_t Y{};
    Xi_t Xi{};
    static constexpr int thread_num = Y_t::thread_num;
};

template <typename _T, typename YTileShape_t, typename YFrgThr, typename SYTile,
          typename GY, typename... GXi>
auto make_tprod_mosaic(GY , GXi... ) {
    return TprodMosaic<_T, YTileShape_t, YFrgThr, SYTile, GY, GXi...>{};
}

template <typename _T, typename YTileShape_t,
          typename GY, typename... GXi>
auto make_tprod_mosaic(GY , GXi... ) {
    constexpr int rank = sizeof...(GXi);
    using YFrgShape = Shape<decltype(repeat<rank>(_1{})),_1>;
    auto Y_FrgThr = zipped_divide(make_layout(YTileShape_t{}), YFrgShape{});
    using YFrgThr = decltype(Y_FrgThr);
    using SYTile = Layout<YTileShape_t>;
    return make_tprod_mosaic<_T, YTileShape_t, YFrgThr, SYTile>(GY{}, GXi{}...);
}

template <typename T>
auto make_tprod_mosaic(auto Y, auto... Xi) {
    constexpr int rank = sizeof...(Xi);
    using YTileShape = decltype(repeat<rank>(_32{}));
    return make_tprod_mosaic<T, YTileShape>(Y, Xi...);
}

// -------------- Mosaic Printing --------------
template <typename _T, typename GY,
          typename _TileShape_t, typename STile,
          typename _FrgThr>
CUTE_HOST void print_mosaic(const YTprodMosaic<_T, GY, _TileShape_t, STile, _FrgThr> mos, const char* prefix = "") {
    print(prefix); print("YTprodMosaic:\n");
    std::string prefix_str = std::string(prefix) + "  ";
    const char* _prefix = prefix_str.c_str();
    print(_prefix); print("gSlab: "); print(mos.gSlab); print("\n");
    print(_prefix); print("TileShape: "); print(mos.TileShape); print("\n");
    print(_prefix); print("sTile: "); print(mos.sTile); print("\n");
    print(_prefix); print("tprod_FrgThr: "); print(mos.tprod_FrgThr); print("\n");
    print(_prefix); print("Frg: "); print(mos.Frg); print("\n");
    print(_prefix); print("Tile: "); print(mos.Tile); print("\n");
    print(_prefix); print("TileBlock: "); print(mos.TileBlock); print("\n");
    print(_prefix); print("thread_num: "); print(mos.thread_num); print("\n");
    print_mosaic(mos.tile_copy, _prefix);
}

template <typename YMosaic, int component, typename GY>
CUTE_HOST void print_mosaic(const XTprodMosaic<YMosaic, component, GY> mos, const char* prefix = "") {
    print(prefix); print("XTprodMosaic:\n");
    std::string prefix_str = std::string(prefix) + "  ";
    const char* _prefix = prefix_str.c_str();
    print(_prefix); print("component: "); print(component); print("\n");
    print(_prefix); print("TileShape: "); print(mos.TileShape); print("\n");
    print(_prefix); print("sTile: "); print(mos.sTile); print("\n");
    print(_prefix); print("tprod_FrgThr: "); print(mos.tprod_FrgThr); print("\n");
    print(_prefix); print("Frg: "); print(mos.Frg); print("\n");
    print(_prefix); print("Tile: "); print(mos.Tile); print("\n");
    print(_prefix); print("TileBlock: "); print(mos.TileBlock); print("\n");
    print(_prefix); print("thread_num: "); print(mos.thread_num); print("\n");
    print_mosaic(mos.tile_copy, _prefix);
}

template <typename _T, typename YTileShape, typename YFrgThr, typename SYTile,
          typename GY, typename... GXi>
CUTE_HOST void print_mosaic(const TprodMosaic<_T, YTileShape, YFrgThr, SYTile, GY, GXi...> mos, const char* prefix = "") {
    print(prefix); print("Rank2TprodMosaic:\n");
    std::string prefix_str = std::string(prefix) + "  ";
    const char* _prefix = prefix_str.c_str();
    print(_prefix); print("thread_num: "); print(mos.thread_num); print("\n");
    print_mosaic(mos.Y, _prefix);
    for_each(mos.Xi, [_prefix](auto& x) { print_mosaic(x, _prefix); });
}

} // namespace mosaic
