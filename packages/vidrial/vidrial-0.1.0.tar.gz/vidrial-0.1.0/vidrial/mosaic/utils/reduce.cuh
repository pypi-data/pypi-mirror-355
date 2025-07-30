#include "utilities.cuh"
#include "tprod.cuh"

namespace mosaic {

struct SumCallable {
    template<typename T> CUTE_HOST_DEVICE
    T operator()(T a, T b) {
        return a + b;
    }
};

struct MaxCallable {
    template<typename T> CUTE_HOST_DEVICE
    T operator()(T a, T b) {
        return a > b ? a : b;
    }
};

// -------------- Thread Level Reduction --------------
template<int... Is, typename XTensor, typename xTensor, typename F>
CUTE_HOST_DEVICE void reduce(const XTensor& X, xTensor& x, F f) {
    using L = decltype(X.layout());
    using T = typename XTensor::value_type;
    static_assert(LayoutShape(xTensor){} == drop<Is...>(LayoutShape(XTensor){}), "x must have the same shape as X after dropping the reduce index");
    auto YLayout = make_layout(drop<Is...>(L{}), get<Is...>(L{}));
    auto Y = make_tensor(X.data(), YLayout);
    for (size_t i = 0; i < size<0>(YLayout); ++i) {
        x(i) = Y(i, 0);
        for (size_t j = 1; j < size<1>(YLayout); ++j) {
            x(i) = f(x(i), Y(i,j));
        }
    }
}
template<int... Is, typename XTensor, typename xTensor>
void reduce_sum(const XTensor& X, xTensor& x) {
    reduce<Is...>(X, x, [](auto a, auto b) { return a + b; });
}
template<int... Is, typename XTensor, typename xTensor>
void reduce_prod(const XTensor& X, xTensor& x) {
    reduce<Is...>(X, x, [](auto a, auto b) { return a * b; });
}
template<int... Is, typename XTensor, typename xTensor>
void reduce_max(const XTensor& X, xTensor& x) {
    reduce<Is...>(X, x, [](auto a, auto b) { return max(a, b); });
}
template<int... Is, typename XTensor, typename xTensor>
void reduce_min(const XTensor& X, xTensor& x) {
    reduce<Is...>(X, x, [](auto a, auto b) { return min(a, b); });
}


// -------------- CTA Wide Reduction --------------
template<int... Is, typename SXEngine, typename SXLayout, typename F, int thread_num>
__device__ void smem_reduce_impl(Tensor<SXEngine, SXLayout>& sX, F f, int tid, Int<thread_num> threadNum) {
    /* A reduce acting on smem tensors. Running it modifies the contents of the smem tensor.
        Each step of the reduction the active threads are assigned 2 elements along the
        reduce dim (given by Is...). Every subsequent step halves the number of active threads.
        The output of the reduction is stored in sX at index 0 for the reduce dim
        It is assumed that there are enough threads to cover the entire sX tensor. */
    static_assert(thread_num >= size(SXLayout{})/2, "insufficient threads to perform the reduction");
    constexpr int reduce_dim = size(get<Is...>(SXLayout{}));
    static_assert(reduce_dim == (1<< static_log2<reduce_dim>()), "reduce_dim must be a power of 2");
    auto YLayout = make_layout(drop<Is...>(SXLayout{}), get<Is...>(SXLayout{}));
    auto sY = make_tensor(sX.data(), YLayout);
    constexpr int threads_along_reduce_dim = reduce_dim/2;
    int j = 2 * (tid % threads_along_reduce_dim); // consecutive threads along the reduce dim 
    int i = tid / threads_along_reduce_dim; // rest of threads along the other (batched) dims
    constexpr int steps = static_log2<reduce_dim>();
    for (int pow=0; pow<steps; ++pow) {
        bool do_reduce = (j % (2 << pow)) == 0;
        if (do_reduce && i < size<0>(YLayout)) {
            int offset = 1 << pow;
            sY(i, j) = f(sY(i, j), sY(i, j+offset));
        }
        __syncthreads();
    }
}

template<int... Is, typename SXEngine, typename SXLayout, typename F, int thread_num>
__device__ void smem_reduce(Tensor<SXEngine, SXLayout>& sX, F f, int tid, Int<thread_num> threadNum) {
    /* Reduces a tensor in smem. If the number of threads is less than the number of elements/2
    then the full reduction serialized into multiple calls to smem_reduce_impl */
    static_assert(is_static<SXLayout>::value, "SXLayout must be static");
    constexpr int reduce_dim = size<Is...>(SXLayout{});
    static_assert(reduce_dim <= thread_num, "reduction not yet implemented when thread_num is less than the reduce_dim");
    if constexpr (reduce_dim == 1)
        return;
    else {
        static_assert(size<Is...>(SXLayout{}) % 2 == 0, "reduce_dim must be 1 or even");
        constexpr int threads_along_reduce_dim = reduce_dim/2;
        constexpr int batch_size = thread_num / threads_along_reduce_dim; // how many batch elements are reduced in parallel
        constexpr auto _TileShape = nested_replace<Is...>(SXLayout{}.shape(), _1{});
        constexpr auto __TileShape = get<0>(shape_minimum(_TileShape, Int<batch_size>{})); // get the tile shape that the rest of the threads can cover
        constexpr auto TileShape = nested_replace<Is...>(__TileShape, Int<reduce_dim>{});
        auto sX_tiling = zipped_divide(sX, TileShape);
        for (int i = 0; i < size<1>(sX_tiling); ++i) {
            auto sX_tile = slice_rest(sX_tiling, i);
            smem_reduce_impl<Is...>(sX_tile, f, tid, threadNum);
        }
    }
    __syncthreads();
}
 
 template<int... Is, typename XShape_T, typename XFrgThr_T> constexpr
 __device__ size_t rmem_reduce_buffer_size(XShape_T const& XShape, XFrgThr_T const& XFrgThr) {
    return size(XShape_T{});

    // return size(XShape_T{}) / size<0,Is...>(XFrgThr_T{});
}

template<typename XShape, typename XFrgThr, typename xFrgThr,
        int... Is, typename RXFrg, typename RxFrg,
        typename F, typename ThreadNum, typename T>
__device__ void rmem_reduce(const RXFrg& rX_frag, RxFrg& rx_frag,
                        F f, int tid, ThreadNum threadNum, T* sBuff) {
    /* Reduces a tile of data partitioned into register fragments rX_frag using an
    arbitrary X_FrgThr layout. The results are also stored in fragments rx_frag also
    using an arbitrary X_FrgThr layout.
    First reduces the fragment as much as possible
    Then data is writen to a Y smem tensor and smem_reduce is called */
    static_assert(size(XFrgThr{}) == size(XShape{}));
    static_assert(size(xFrgThr{}) == size(drop<Is...>(XShape{})));
    static_assert(size<0>(XFrgThr{}) == decltype(size(rX_frag)){});
    static_assert(size<0>(xFrgThr{}) == decltype(size(rx_frag)){});
    static_assert(size<1>(XFrgThr{}) <= threadNum);
    static_assert(size<1>(xFrgThr{}) <= threadNum);
    auto smem = make_smem_ptr(sBuff);
    static_assert(std::is_same_v<typename RXFrg::value_type, T>, "Fragment value type must match buffer type T");

    auto sX = make_tensor(smem, make_layout(XShape{}));
    if (tid < size<1>(XFrgThr{}))
        copy(rX_frag, slice_rest(sX, XFrgThr{}, tid));
    __syncthreads();
    smem_reduce<Is...>(sX, f, tid, threadNum);
    auto sx = make_tensor(smem, drop<Is...>(sX.layout()));
    if (tid < size<1>(xFrgThr{}))
        copy(slice_rest(sx, xFrgThr{}, tid), rx_frag);
    __syncthreads();

    // // static_assert(std::is_same_v<RXFrg, decltype(colayout(XShape{}, rX_frag.layout()))>, "X_frag should have a shape compatible with XShape");
    // constexpr int thread_level_reduce_size = size<Is...>(RXFrg{}.layout());
    // auto rY_frag = make_tensor<T>(drop<Is...>(rX_frag.layout()));
    // reduce<Is...>(rX_frag, rY_frag, f);
    // constexpr auto new_reduce_dim = shape_div(get<Is...>(XShape{}), Int<thread_level_reduce_size>{});
    // constexpr auto Y_Shape = nested_replace<Is...>(XShape{}, new_reduce_dim);
    // // We need to create a Y tensor in smem and have each thread copy it's corresponding fragment
    // auto sY = make_tensor(smem, make_layout(Y_Shape));
    // auto copy_Y_FrgShape = shape_div(Y_Shape, threadNum);
    // auto sY_FrgThr = zipped_divide(sY, copy_Y_FrgShape);
    // if (tid < size<1>(sY_FrgThr))
    //     copy(rY_frag, sY_FrgThr(_, tid));
    // __syncthreads();
    // smem_reduce<Is...>(sY, f, tid, threadNum);
    // auto sx = make_tensor(smem, drop<Is...>(sY.layout()));
    // if (tid < size<1>(xFrgThr{}))
    //     copy(slice_rest(sx, xFrgThr{}, tid), rx_frag);
}

// -------------- Tprod Reduce --------------
template<int keep_dim>
CUTE_HOST_DEVICE constexpr void tprod_reduce_sum(auto& Y, auto& X) {
    auto YLayout = Y.layout();
    auto _YLayout = make_layout(drop<keep_dim>(get<0>(YLayout)), get<0,keep_dim>(YLayout),  get<1>(YLayout));
    auto _Y = make_tensor(Y.data(), _YLayout);
    reduce_sum<0>(_Y, X);
}

template<int N, typename L, typename L2>
CUTE_HOST_DEVICE constexpr auto layout_insert(L l, L2 l2) {
    auto shape = insert<N>(l.shape(), l2.shape());
    auto stride = insert<N>(l.stride(), l2.stride());
    return make_layout(shape, stride);
}

template<int keep_dim, typename YShape, typename YFrgThr, typename XFrgThr, typename T>
__device__ void tprod_rmem_reduce_sum(const auto& Y_frg, auto& X_frg, int tid, T* sBuff) {
    constexpr int thread_num = size<1>(YFrgThr{});

    auto _YShape = make_shape(drop<keep_dim>(get<0>(YShape{})), get<0,keep_dim>(YShape{}), get<1>(YShape{}));
    auto _YLayout = make_layout(_YShape);
    auto Y_convert0 = layout_insert<keep_dim>(get<0>(_YLayout), get<1>(_YLayout));
    auto Y_convert = make_layout(Y_convert0, get<2>(_YLayout));
    auto _Y_FrgThr = Y_convert.compose(YFrgThr{});

    auto Y_frg_shape = Y_frg.layout().shape();
    auto _Y_frg_shape = make_shape(drop<keep_dim>(get<0>(Y_frg_shape)), get<0,keep_dim>(Y_frg_shape), get<1>(Y_frg_shape));
    auto _Y_frg_layout = make_layout(_Y_frg_shape);
    auto _Y_frg_convert0 = layout_insert<keep_dim>(get<0>(_Y_frg_layout), get<1>(_Y_frg_layout));
    auto _Y_frg_convert = make_layout(_Y_frg_convert0, get<2>(_Y_frg_layout));
    // auto _Y_frg = make_tensor(Y_frg.data(), _Y_frg_convert.compose(_Y_frg_layout));
    auto _Y_frg = make_tensor(Y_frg.data(), _Y_frg_layout);
    rmem_reduce<decltype(_YShape), decltype(_Y_FrgThr), XFrgThr, 0>(_Y_frg, X_frg, SumCallable{}, tid, Int<thread_num>{}, sBuff);
}

template<typename YShape, typename YFrgThr, int keep_dim>
CUTE_HOST_DEVICE constexpr int tprod_rmem_reduce_buffer_size() {
    // using _YShape = decltype(make_shape(drop<keep_dim>(get<0>(YShape{})), get<0,keep_dim>(YShape{}),  get<1>(YShape{})));
    // auto _Y_FrgThr0 = make_layout(drop<keep_dim>(get<0,0>(YFrgThr{})), get<0,0,keep_dim>(YFrgThr{}), get<0,1>(YFrgThr{}));
    // auto _Y_FrgThr = make_layout(_Y_FrgThr0, get<1>(YFrgThr{}));
    auto _YShape = make_shape(drop<keep_dim>(get<0>(YShape{})), get<0,keep_dim>(YShape{}), get<1>(YShape{}));
    auto _YLayout = make_layout(_YShape);
    auto Y_convert0 = layout_insert<keep_dim>(get<0>(_YLayout), get<1>(_YLayout));
    auto Y_convert = make_layout(Y_convert0, get<2>(_YLayout));
    auto _Y_FrgThr = Y_convert.compose(YFrgThr{});
    return rmem_reduce_buffer_size<0>(_YShape, _Y_FrgThr);
}
template<typename YShape, typename YFrgThr, auto... Is>
CUTE_HOST_DEVICE constexpr int tprod_rmem_reduce_buffer_size_impl(int_sequence<Is...>) {
    constexpr auto buff_sizes = make_tuple(Int<tprod_rmem_reduce_buffer_size<YShape, YFrgThr, Is>()>{}...);
    constexpr auto buff_size = fold(buff_sizes, _0{}, [](auto a, auto b) { return Int<static_max(a,b)>{}; });
    return buff_size;
}
template<typename YShape, typename YFrgThr>
CUTE_HOST_DEVICE constexpr int tprod_rmem_reduce_buffer_size() {
    constexpr int rnk = rank<0>(YShape{});
    return tprod_rmem_reduce_buffer_size_impl<YShape, YFrgThr>(make_int_sequence<rnk>());
}

} // namespace mosaic