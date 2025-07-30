#include <gtest/gtest.h>
#include "utilities.cuh"
#include "reduce.cuh"

#include <type_traits>

namespace mosaic {
namespace {

template<typename GX, typename Gx, typename F, int thread_num, int... reduce_Is>
__global__ void test_smem_reduce_kernel(const GX gX, Gx gx, F f, Int<thread_num> threadNum) {
    int t = threadIdx.x;
    using T = decltype(gX)::value_type;
    __shared__ T smem[size(gX.layout())];
    auto sX = make_tensor(make_smem_ptr(smem), make_layout(gX.shape()));
    if (thread0()) {
        copy(gX, sX);
    }
    __syncthreads();
    smem_reduce<reduce_Is...>(sX, f, t, threadNum);
    auto sx = make_tensor(make_smem_ptr(smem), drop<reduce_Is...>(sX.layout()));
    if (thread0()) {
        copy(sx, gx);
    }
}

template<int... reduce_Is, typename OnesTensor, typename ThreadNum>
void test_reduce_sum(OnesTensor Ones, ThreadNum threadNum) {
    auto result = make_managed_tensor<int>(make_layout(drop<reduce_Is...>(Ones.shape())));
    int correct_result = size<reduce_Is...>(Ones.shape());
    // Test the basic (thread level) reduction on the CPU
    reduce<reduce_Is...>(Ones, result, SumCallable{});
    for (int i = 0; i < size(result.shape()); i++) {
        EXPECT_EQ(result(i), correct_result);
    }
    clear(result);
    // Test the smem reduction on the GPU
    auto f = SumCallable{};
    constexpr int threads = ThreadNum::value;
    test_smem_reduce_kernel<decltype(Ones), decltype(result), decltype(f), threads, reduce_Is...>
                           <<<1,threads>>>(Ones, result, f, Int<threads>{});
    CHECK_CUDA();
    for (int i = 0; i < size(result.shape()); i++) {
        EXPECT_EQ(result(i), correct_result);
    }
}

TEST(ReduceTest, ReduceSum) {
    {
        using L = Layout<Shape<_2,_4>>;
        auto Ones = make_managed_tensor<int>(L{});
        auto threadNum = Int<4>{};
        fill(Ones, 1);
        test_reduce_sum<0>(Ones, threadNum);
        test_reduce_sum<1>(Ones, threadNum);
    }
    {
        using L = Layout<Shape<_16,_16>>;
        auto Ones = make_managed_tensor<int>(L{});
        auto threadNum = Int<128>{};
        fill(Ones, 1);
        test_reduce_sum<0>(Ones, threadNum);
        test_reduce_sum<1>(Ones, threadNum);
    }
    {
        using L = Layout<Shape<Shape<_2,_4>,_8,_1,_6>>;
        auto Ones = make_managed_tensor<int>(L{});
        auto threadNum = Int<32>{};
        fill(Ones, 1);
        test_reduce_sum<0>(Ones, threadNum);
        test_reduce_sum<0,0>(Ones, threadNum);
        test_reduce_sum<0,1>(Ones, threadNum);
        test_reduce_sum<1>(Ones, threadNum);
        test_reduce_sum<2>(Ones, threadNum);
    }
    {
        using L = Layout<Shape<_128,Shape<_8,_4>,_2,_1>>;
        auto Ones = make_managed_tensor<int>(L{});
        auto threadNum = Int<128>{};
        fill(Ones, 1);
        test_reduce_sum<0>(Ones, threadNum);
        test_reduce_sum<1>(Ones, threadNum);
        test_reduce_sum<1,0>(Ones, threadNum);
        test_reduce_sum<1,1>(Ones, threadNum);
        test_reduce_sum<2>(Ones, threadNum);
        test_reduce_sum<3>(Ones, threadNum);
    }
}

template<typename GX, typename Gx, typename F, int thread_num,
         typename XFrgThr, typename xFrgThr, int... reduce_Is>
__global__ void test_rmem_reduce_kernel(const GX gX, Gx gx,
                                        F f, Int<thread_num> threadNum,
                                        XFrgThr X_FrgThr, xFrgThr x_FrgThr) {
    int t = threadIdx.x;
    using T = decltype(gX)::value_type;
    auto rX_frag = make_tensor<T>(get<0>(X_FrgThr));
    auto rx_frag = make_tensor<T>(get<0>(x_FrgThr));
    copy(slice_rest(gX, X_FrgThr, t), rX_frag);
    __syncthreads();
    constexpr int buffSize = rmem_reduce_buffer_size<reduce_Is...>(LayoutShape(GX){}, XFrgThr{});
    __shared__ T sBuff[buffSize];
    using XShape = decltype(gX.shape());
    using RXFrg = decltype(rX_frag);
    using RxFrg = decltype(rx_frag);
    rmem_reduce<XShape, XFrgThr, xFrgThr, reduce_Is...>(rX_frag, rx_frag, f, t, threadNum, sBuff);
    copy(rx_frag, slice_rest(gx, x_FrgThr, t));
}

template<int... reduce_Is, typename OnesTensor, typename ThreadNum>
void test_rmem_reduce_sum(OnesTensor Ones, auto X_FrgThr, auto x_FrgThr, ThreadNum threadNum) {
    auto x = make_managed_tensor<int>(make_layout(drop<reduce_Is...>(Ones.shape())));
    auto correct_x = make_managed_tensor<int>(make_layout(drop<reduce_Is...>(Ones.shape())));
    fill(correct_x, size<reduce_Is...>(Ones.shape()));
    auto f = SumCallable{};
    constexpr int threads = ThreadNum::value;
    test_rmem_reduce_kernel<decltype(Ones), decltype(x), decltype(f), threads, decltype(X_FrgThr), decltype(x_FrgThr), reduce_Is...>
                           <<<1,threads>>>(Ones, x, f, Int<threads>{}, X_FrgThr, x_FrgThr);
    CHECK_CUDA();
    ASSERT_TRUE(check_tensors_match(x, correct_x, 0., false));
}

template<int... reduce_Is, typename XSlab, typename ThreadNum>
void test_rmem_reduce_max(XSlab X, auto X_FrgThr, auto x_FrgThr, ThreadNum threadNum) {
    auto x = make_managed_tensor<int>(make_layout(drop<reduce_Is...>(X.shape())));
    for (int i = 0; i < size(x.shape()); i++) x(i) = rand();
    auto f = MaxCallable{};
    constexpr int threads = ThreadNum::value;
    test_rmem_reduce_kernel<decltype(X), decltype(x), decltype(f), threads, decltype(X_FrgThr), decltype(x_FrgThr), reduce_Is...>
                           <<<1,threads>>>(X, x, f, Int<threads>{}, X_FrgThr, x_FrgThr);
    CHECK_CUDA();
    auto reference_x = make_managed_tensor<int>(make_layout(drop<reduce_Is...>(X.shape())));
    reduce<reduce_Is...>(X, reference_x, f);
    ASSERT_TRUE(check_tensors_match(x, reference_x, 0., false));
}


TEST(ReduceTest, RmemReduceSum) {
    {
        using L = Layout<Shape<_2,_4>>;
        auto Ones = make_managed_tensor<int>(L{});
        fill(Ones, 1);
        auto threadNum = Int<4>{};
        auto X_FrgThr = Layout<Shape<Shape<_2,_1>,_4>>{};
        auto x_FrgThr = Layout<Shape<_1,_4>>{};
        test_rmem_reduce_sum<0>(Ones, X_FrgThr, x_FrgThr, threadNum);
    }
    {
        using L = Layout<Shape<_16,_16>>;
        auto Ones = make_managed_tensor<int>(L{});
        fill(Ones, 1);
        auto X_FrgThr = zipped_divide(L{}, Shape<_4,_4>{});
        auto threadNum = size<1>(X_FrgThr);
        auto x_FrgThr = Layout<Shape<_1,decltype(threadNum)>>{};
        test_rmem_reduce_sum<0>(Ones, X_FrgThr, x_FrgThr, threadNum);
        test_rmem_reduce_sum<1>(Ones, X_FrgThr, x_FrgThr, threadNum);
    }
    // { // example where smem reduce must be serialized
    //     using L = Layout<Shape<_16,_32>>;
    //     auto Ones = make_managed_tensor<int>(L{});
    //     fill(Ones, 1);
    //     auto X_FrgThr = zipped_divide(L{}, Shape<_4,_8>{});
    //     auto threadNum = size<1>(X_FrgThr);
    //     auto x_FrgThr_0 = Layout<Shape<_2,decltype(threadNum)>>{};
    //     auto x_FrgThr_1 = Layout<Shape<_1,decltype(threadNum)>>{};
    //     test_rmem_reduce_sum<0>(Ones, X_FrgThr, x_FrgThr_0, threadNum);
    //     test_rmem_reduce_sum<1>(Ones, X_FrgThr, x_FrgThr_1, threadNum);
    // }
    { // Using the classic Mma A matrix TV layout on 16x16 tiles
        using L = Layout<Shape<_16,_16>>;
        auto Ones = make_managed_tensor<int>(L{});
        fill(Ones, 1);
        auto X_FrgThr = Layout<Shape<Shape<_2,_2,_2>,Shape<_4,_8>>,
                                Stride<Stride<_16,_8, _128>,Stride<_32,_1>>>{};
        auto x_FrgThr_0 = Layout<Shape<Shape<_2,_2>,_4>,
                                  Stride<Stride<_1,_8>,_2>>{};
        auto x_FrgThr_1 = Layout<Shape<_2,_8>,Stride<_8,_1>>{};
        test_rmem_reduce_sum<0>(Ones, X_FrgThr, x_FrgThr_0, _32{});
        test_rmem_reduce_sum<1>(Ones, X_FrgThr, x_FrgThr_1, _32{});
    }
}

TEST(ReduceTest, MaxeReduce) {
    {
        using L = Layout<Shape<_2,_4>>;
        auto Ones = make_managed_tensor<int>(L{});
        fill(Ones, 1);
        auto threadNum = Int<4>{};
        auto X_FrgThr = Layout<Shape<Shape<_2,_1>,_4>>{};
        auto x_FrgThr = Layout<Shape<_1,_4>>{};
        test_rmem_reduce_max<0>(Ones, X_FrgThr, x_FrgThr, threadNum);
    }
    {
        using L = Layout<Shape<_16,_16>>;
        auto Ones = make_managed_tensor<int>(L{});
        fill(Ones, 1);
        auto X_FrgThr = zipped_divide(L{}, Shape<_4,_4>{});
        auto threadNum = size<1>(X_FrgThr);
        auto x_FrgThr = Layout<Shape<_1,decltype(threadNum)>>{};
        test_rmem_reduce_max<0>(Ones, X_FrgThr, x_FrgThr, threadNum);
        test_rmem_reduce_max<1>(Ones, X_FrgThr, x_FrgThr, threadNum);
    }
    // { // example where smem reduce must be serialized
    //     using L = Layout<Shape<_16,_32>>;
    //     auto Ones = make_managed_tensor<int>(L{});
    //     fill(Ones, 1);
    //     auto X_FrgThr = zipped_divide(L{}, Shape<_4,_8>{});
    //     auto threadNum = size<1>(X_FrgThr);
    //     auto x_FrgThr_0 = Layout<Shape<_2,decltype(threadNum)>>{};
    //     auto x_FrgThr_1 = Layout<Shape<_1,decltype(threadNum)>>{};
    //     test_rmem_reduce_max<0>(Ones, X_FrgThr, x_FrgThr_0, threadNum);
    //     test_rmem_reduce_max<1>(Ones, X_FrgThr, x_FrgThr_1, threadNum);
    // }
    { // Using the classic Mma A matrix TV layout on 16x16 tiles
        using L = Layout<Shape<_16,_16>>;
        auto Ones = make_managed_tensor<int>(L{});
        fill(Ones, 1);
        auto X_FrgThr = Layout<Shape<Shape<_2,_2,_2>,Shape<_4,_8>>,
                                Stride<Stride<_16,_8, _128>,Stride<_32,_1>>>{};
        auto x_FrgThr_0 = Layout<Shape<Shape<_2,_2>,_4>,
                                  Stride<Stride<_1,_8>,_2>>{};
        auto x_FrgThr_1 = Layout<Shape<_2,_8>,Stride<_8,_1>>{};
        test_rmem_reduce_max<0>(Ones, X_FrgThr, x_FrgThr_0, _32{});
        test_rmem_reduce_max<1>(Ones, X_FrgThr, x_FrgThr_1, _32{});
    }
}



template<typename YShape, typename YFrgThr, typename XFrgThr, int keep_dim, typename GY, typename GX>
__global__ void test_tprod_rmem_reduce_kernel(GY gY, GX gX) {
    int tid = threadIdx.x;
    auto gY_frg = slice_rest(gY, YFrgThr{}, tid);
    auto gX_frg = slice_rest(gX, XFrgThr{}, tid);
    using T = TensorType(gY);
    constexpr auto buff_size = tprod_rmem_reduce_buffer_size<YShape, YFrgThr>(); // Buffer big enough we could reduce any dimension
    __shared__ T smem[buff_size];
    auto rY_frg = make_tensor<T>(make_layout(gY_frg.shape()));
    auto rX_frg = make_tensor<T>(make_layout(gX_frg.shape()));
    copy(gY_frg, rY_frg);
    __syncthreads();
    tprod_rmem_reduce_sum<keep_dim, YShape, YFrgThr, XFrgThr>(rY_frg, rX_frg, tid, smem);
    __syncthreads();
    if (tid < size<1>(XFrgThr{}))
        copy(rX_frg, gX_frg);
}

template<typename T, typename YShape, typename YFrgShape, typename XFrgShape, int keep_dim>
void test_tprod_reduce() {
    using XShape = decltype(make_shape(get<0,keep_dim>(YShape{}), get<1>(YShape{})));
    using GY = Layout<YShape>;
    using GX = Layout<XShape>;
    using YFrgThr = decltype(zipped_divide(GY{}, YFrgShape{}));
    using XFrgThr = decltype(zipped_divide(GX{}, XFrgShape{}));
    auto gY = make_managed_tensor<T>(GY{});
    for (int i = 0; i < size(gY); ++i) gY(i) = static_cast<T>(i);
    auto gX = make_managed_tensor<T>(GX{});
    int threads = size<1>(YFrgThr{});
    test_tprod_rmem_reduce_kernel<YShape, YFrgThr, XFrgThr, keep_dim><<<1,threads>>>(gY, gX);
    CHECK_CUDA();
    auto gX_ref = make_managed_tensor<T>(GX{});
    tprod_reduce_sum<keep_dim>(gY, gX_ref);
    EXPECT_TRUE(check_tensors_match(gX, gX_ref, 0., false));
}

TEST(Reduce, TprodReduce) {
    {
        using T = int;
        using YShape = Shape<Shape<_4,_8>,_1>;
        constexpr int keep_dim = 0;
        using XShape = decltype(make_shape(get<0,keep_dim>(YShape{}), get<1>(YShape{})));
        using YFrgShape = Shape<Shape<_2,_2>,_1>;
        using XFrgShape = Shape<_2,_1>;
        // using YFrgShape = Shape<Shape<_1,_1>,_1>;
        // using XFrgShape = Shape<_1,_1>;
        test_tprod_reduce<T, YShape, YFrgShape, XFrgShape, keep_dim>();
    }
    {
        using T = int;
        using YShape = Shape<Shape<_16,_8>,_2>;
        constexpr int keep_dim = 0;
        using XShape = decltype(make_shape(get<0,keep_dim>(YShape{}), get<1>(YShape{})));
        using YFrgShape = Shape<Shape<_2,_2>,_1>;
        using XFrgShape = Shape<_2,_1>;
        test_tprod_reduce<T, YShape, YFrgShape, XFrgShape, keep_dim>();
    }
    {
        using T = int;
        using YShape = Shape<Shape<_16,_8,_4>,_2>;
        constexpr int keep_dim = 0;
        using YFrgShape = Shape<Shape<_2,_2,_2>,_1>;
        using XFrgShape = Shape<_2,_1>;
        test_tprod_reduce<T, YShape, YFrgShape, XFrgShape, keep_dim>();
    }
    {
        using T = float;
        using YShape = Shape<Shape<_16,_8,_4,_2>,_8>;
        constexpr int keep_dim = 1;
        using YFrgShape = Shape<Shape<_2,_4,_2,_1>,_1>;
        using XFrgShape = Shape<_1,_1>;
        test_tprod_reduce<T, YShape, YFrgShape, XFrgShape, keep_dim>();
    }
}

} // namespace
} // namespace mosaic