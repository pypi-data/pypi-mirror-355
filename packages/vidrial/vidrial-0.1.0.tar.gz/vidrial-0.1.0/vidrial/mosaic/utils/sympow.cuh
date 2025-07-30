#pragma once
#include "utilities.cuh"
#include "tprod.cuh"

namespace mosaic {

template<int... Is> constexpr
auto dynamic_zero_tuple(int_sequence<Is...>) {
    auto return_zero = [](int x) { return 0; };
    return tuple(return_zero(Is)...);
}
template<int rank>
auto make_tuple_of_rank() {
    return dynamic_zero_tuple(make_int_sequence<rank>());
}

// ------- Layouts for the Symmetric Power -------
template<int p, int d, int bk=1>
constexpr index_t sympow_dim() {
    return n_choose_k(p + d/bk - 1, p) * static_pow<p>(bk);
}
template<int p, int d, int b, int d_blk>
auto sympow_shape() {
    static_assert(d % d_blk == 0, "d must be divisible by d_blk");
    auto feature_block = repeat<p>(Int<d_blk>{});
    constexpr auto block_num = sympow_dim<p, d/d_blk>();
    return make_shape(make_shape(feature_block, Int<block_num>{}), Int<b>{});
}
template<int p, int d_blk, typename XShape>
auto sympow_shape(XShape) {
    static constexpr int d = get<0>(XShape{});
    static_assert(d % d_blk == 0, "d must be divisible by d_blk");
    auto feature_tile = repeat<p>(Int<d_blk>{});
    constexpr auto tile_num = sympow_dim<p, d/d_blk>();
    return make_shape(make_shape(feature_tile, Int<tile_num>{}), get<1>(XShape{}));
}

/////////////////////

template<typename T> CUTE_HOST_DEVICE
auto& dynamic_get_impl(int_sequence<>, auto i, T& t) {
    assert(false);
    return get<0>(t);
}
template<int I, int... Is, typename T> CUTE_HOST_DEVICE
auto& dynamic_get_impl(int_sequence<I,Is...>, auto i, T& t) {
    if (I == i) return get<I>(t);
    else return dynamic_get_impl<Is...>(int_sequence<Is...>{}, i, t);
}
template<typename T> CUTE_HOST_DEVICE
auto& dynamic_get(auto i, T& t) {
    return dynamic_get_impl(make_int_sequence<rank(T{})>{}, i, t);
}

// ------- NonDecSeq for coordinates -------
template<int _rng, int _len, typename Derived>
struct NonDecSeqBase {
    static constexpr int rng = _rng;
    static constexpr int len = _len;
    // static constexpr int num_elements = n_choose_k(rng + len - 1, len);
    static constexpr int num_elements = sympow_dim<len, rng>();
    using seq_t = decltype(make_tuple_of_rank<len>());
    seq_t seq;
    int idx = 0;
    CUTE_HOST_DEVICE
    Derived& operator++() {
        increment<len-1>();
        idx++;
        return *static_cast<Derived*>(this);
    }
    CUTE_HOST_DEVICE
    Derived operator+(int n) {
        Derived result = *this;
        for (int i = 0; i < n; ++i) {
            ++result;
        }
        return result;
    }
    CUTE_HOST_DEVICE
    Derived& operator+=(int n) {
        for (int i = 0; i < n; ++i) {
            ++(*this);
        }
        return *static_cast<Derived*>(this);
    }
    template<int r> CUTE_HOST_DEVICE
    void increment() {
        if (get<r>(seq) < rng-1) {
            get<r>(seq)++;
        }
        else if constexpr (r > 0) {
            increment<r-1>();
            get<r>(seq) = get<r-1>(seq);
        }
    }
    CUTE_HOST_DEVICE void reset() {
        for (int i = 0; i < len; ++i) {
            get<i>(seq) = 0;
        }
        idx = 0;
    }
};

template<int _rng, int _len>
struct NonDecSeq : NonDecSeqBase<_rng, _len, NonDecSeq<_rng, _len>> {
    CUTE_HOST_DEVICE
    int duplicate_count() {
        auto arr = to_array<int>(this->seq);
        int hist[_rng]; 
        for(int i = 0; i < _rng; ++i)
            hist[i] = 0;
        for(int i = 0; i < _len; ++i)
            hist[arr[i]]++;
        int result = factorial(_len);
        for (int i = 0; i < _rng; ++i)
            result /= factorial(hist[i]);
        return result;
    }
};
template<int _rng>
struct NonDecSeq<_rng, 1> : NonDecSeqBase<_rng, 2, NonDecSeq<_rng, 2>> {
    CUTE_HOST_DEVICE
    static constexpr int duplicate_count() {
        return 1;
    }
};
template<int _rng>
struct NonDecSeq<_rng, 2> : NonDecSeqBase<_rng, 2, NonDecSeq<_rng, 2>> {
    CUTE_HOST_DEVICE
    int duplicate_count() {
        return (get<0>(this->seq) == get<1>(this->seq)) ? 1 : 2;
    }
};
template<int _rng>
struct NonDecSeq<_rng, 3> : NonDecSeqBase<_rng, 3, NonDecSeq<_rng, 3>> {
    CUTE_HOST_DEVICE
    int duplicate_count() {
        const auto& s = this->seq;
        bool ab = get<0>(s) == get<1>(s);
        bool bc = get<1>(s) == get<2>(s);
        // if (ab && bc) return 1;
        // if (ab || bc) return 3; // since seq is non-decreasing, and not all are equal we don't need to check ac
        // TODO: investigate this super weird issue. The above two lines should be
        // a correct implementation, but for some fucked up reason the test TEST(SympowMosaic, SimpleP3) fails
        // But the following code seems to pass all test cases.
        bool ac = get<0>(s) == get<2>(s);
        if (ab && bc && ac) return 1;
        if (ab || bc || ac) return 3;
        return 6;
    }
};
template<int _rng>
struct NonDecSeq<_rng, 4> : NonDecSeqBase<_rng, 4, NonDecSeq<_rng, 4>> {
    CUTE_HOST_DEVICE
    int duplicate_count() {
        auto& s = this->seq;
        uint8_t x = (get<0>(s) == get<1>(s)) +
                    (get<2>(s) == get<3>(s)) +
                    (get<0>(s) == get<2>(s)) +
                    (get<1>(s) == get<3>(s)) +
                    (get<0>(s) == get<3>(s)) +
                    (get<1>(s) == get<2>(s));
        switch (x) {
            case 6: return 1; // All match
            case 3: return 4; // 3 match
            case 2: return 6; // 2 pairs
            case 1: return 12; // 1 pair
        }
        return 24; // all different
    }
};



// ------- Symmetric Power Operations -------
template<int p, int d_blk, bool duplicate_correction, int... Is,
         typename ZEngine, typename ZLayout,
         typename XEngine, typename XLayout>
void sympow(Tensor<ZEngine,ZLayout>& gZ, Tensor<XEngine,XLayout>& gX, int_sequence<Is...>) {
    using T = typename ZEngine::value_type;
    constexpr int d = size<0>(XLayout{}); constexpr int b = size<1>(XLayout{});
    auto X_TileShape = Shape<Int<d_blk>, Int<b>>{};
    auto X_TileBlock = zipped_divide(make_layout(gX.shape()), X_TileShape);
    for (NonDecSeq<d/d_blk, p> c{}; c.idx < c.num_elements; ++c) {
        auto Z_tile = gZ(make_coord(_,c.idx),_);
        tprod(Z_tile,
              slice_rest(gX, X_TileBlock,get<Is>(c.seq))...);
        if constexpr (duplicate_correction) {
            T scale = static_cast<T>(sqrtf(c.duplicate_count()));
            tensor_scalar_prod(Z_tile, scale);
        }
   }
}

template<int p, int d_blk, bool duplicate_correction=false>
void sympow(auto& gZ, auto& gX) {
    sympow<p, d_blk, duplicate_correction>(gZ, gX, make_int_sequence<p>{});
}

} // namespace mosaic
