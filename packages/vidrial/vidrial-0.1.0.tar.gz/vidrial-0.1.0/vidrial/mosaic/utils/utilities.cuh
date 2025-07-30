#pragma once

#include <cute/tensor.hpp>
#include <cute/algorithm/tuple_algorithms.hpp>
#include <cute/algorithm/functional.hpp>
#include <cute/underscore.hpp>
#include <cute/int_tuple.hpp>
#include <cxxabi.h>
#include <random>
#include <optional>

#ifdef DEBUG
#define DEBUG_ASSERT(condition) assert(condition)
#else
#define DEBUG_ASSERT(condition) ((void)0)
#endif

#define CHECK_CUDA() do {                                                 \
    cudaDeviceSynchronize();\
    cudaError_t error = cudaGetLastError(); \
    ASSERT_EQ(error, cudaSuccess) << "CUDA error: " << cudaGetErrorString(error); \
} while(0)                                                                      \ 

namespace mosaic {
using namespace cute;

// --------------- Lazy Conditional ---------------
template<bool Condition, typename T, typename F>
struct lazy_conditional;

template<typename T, typename F>
struct lazy_conditional<true, T, F> {
    using type = typename T::type;
};

template<typename T, typename F>
struct lazy_conditional<false, T, F> {
    using type = typename F::type;
};

// --------------- Tree Type Utilities ---------------
template <int64_t v>
using Int64 = C<v>;

constexpr auto tree_types(auto t) {
    return transform_leaf(t, [](auto x) {
            return abi::__cxa_demangle(typeid(x.value).name(), nullptr, nullptr, nullptr);
    });
}
template<typename XEngine, typename XLayout>
constexpr auto tree_types(Layout<XEngine,XLayout> X) {
    return make_layout(tree_types(X.shape()), tree_types(X.stride()));
}

template<typename NewType>
constexpr auto static_tree_cast(auto t) {
    return transform_leaf(t, [](auto x) {
        return C<static_cast<NewType>(x.value)>();
    });
}
template<typename NewType, typename XEngine, typename XLayout>
constexpr auto static_tree_cast(Layout<XEngine,XLayout> X) {
    return make_layout(static_tree_cast<NewType>(X.shape()), static_tree_cast<NewType>(X.stride()));
}



// --------------- Int Tuple Utilities ---------------
template<int... Is> constexpr
CUTE_HOST_DEVICE auto int_seq_tuple(int_sequence<Is...>) {
    return tuple(Int<Is>{}...);
}
template<int value, typename Tuple, typename true_case = _1, typename false_case = _0>
CUTE_HOST_DEVICE constexpr auto leafs_match_value(Tuple t) {
    return transform_leaf(t,
                    [](auto& a) {
                        if constexpr(std::is_same_v<remove_cvref_t<decltype(a)>, Int<value>>) {
                            return true_case{};
                        } else {
                            return false_case{};
                        }
                    });
}
template<int N, int H>
CUTE_HOST_DEVICE constexpr auto one_hot_int_tuple() {
    auto t = int_seq_tuple(make_int_sequence<N>());
    return leafs_match_value<H>(t);
}

template<int i, int j>
CUTE_HOST_DEVICE constexpr auto tuple_permute(auto const& t) {
    using T = decltype(t);
    constexpr auto t1 = replace<i>(T{}, get<j>(T{}));
    constexpr auto t2 = replace<j>(t1, get<i>(T{}));
    return t2;
}
constexpr int static_min(int a, int b) {
    return (a < b) ? a : b;
}
constexpr int static_max(int a, int b) {
    return (a > b) ? a : b;
}
// This get returns by value, not reference
template<auto... Is, typename T>
auto copy_get(T&& t) {
    return get<Is...>(t);
}


// --------------- Basic Layout Utilities ---------------
#define LayoutShape(L) decltype(shape(declval<L>()))
#define LayoutStride(L) decltype(stride(declval<L>()))

template<int... Is, typename Layout>
CUTE_HOST_DEVICE auto transpose_layout(Layout const& layout) {
    return make_layout(get<Is>(layout)...);
}
template<int match_dim, typename XLayout, typename YLayout>
CUTE_HOST_DEVICE auto broadcast_layout(XLayout X, YLayout Y) {
    auto I = X.shape();
    static_assert(size(X) == size<match_dim>(Y), "Broadcast layout sizes do not match");
    auto shape = transform(Y.shape(), [](auto const& shp_i) { return size(shp_i); });
    auto strides = one_hot_int_tuple<rank(Y), match_dim>();
    return make_layout(shape, strides);
}
template <class IntTupleA, class IntTupleB>
CUTE_HOST_DEVICE constexpr
auto shape_minimum(IntTupleA const& a, IntTupleB const& b) {
    if constexpr (is_tuple<IntTupleB>::value) {
        static_assert(dependent_false<IntTupleA>, "Not implemented.");
    } else if constexpr (is_tuple<IntTupleA>::value) {
        return fold(a, make_tuple(make_tuple(), b),
        [] (auto const& carry, auto const& a_i) {
            auto [carry_min, carry_rest] = carry;
            auto [min_i, new_rest] = shape_minimum(a_i, carry_rest);
            auto new_min = append(carry_min, min_i);
            return make_tuple(new_min, new_rest);
        });
    } else {
        return tuple(cute::min(a, b), shape_div(b, a));
    }
}

// Returns the major mode of a layout (the mode with stride 1), or (-1):(-1) if no such mode exists (when the layout is an injection)
template<typename Shape, typename Stride>
constexpr auto major_mode(Layout<Shape, Stride> L) {
    constexpr auto L_flat = flatten(L);
    constexpr auto dims =  int_seq_tuple(make_int_sequence<rank(L_flat.shape())>());
    constexpr auto dim_str = zip(dims, L_flat.stride());
    constexpr int major_dim = fold(dim_str, -1, [](int carry, auto ds_i) {
        auto [dim_i, stride_i] = ds_i;
        if constexpr(is_constant<1, decltype(stride_i)>::value) {
            return dim_i;
        } else {
            return carry;
        }
    });
    if constexpr(major_dim == -1) {
        return make_layout(Int<-1>{}, Int<-1>{});
    } else {
        return get<major_dim>(L_flat);
    }
}

template<typename Shp, typename Str>
constexpr int flat_major_dim(Layout<Shp, Str> L) {
    static_assert(depth(L) == 1);
    if constexpr (size(Shp{}) == 1) {
        return 0;
    } else {
        constexpr auto dims =  int_seq_tuple(make_int_sequence<rank(L.shape())>());
        constexpr auto dim_str = zip(dims, L.stride());
        constexpr int major_dim = fold(dim_str, -1, [](int carry, auto ds_i) {
            auto [dim_i, stride_i] = ds_i;
            if constexpr(is_constant<1, decltype(stride_i)>::value) {
                return dim_i;
            } else {
                return carry;
            }
        });
        static_assert(major_dim >= 0 && major_dim < rank(L.shape()), "Major dimension is out of bounds");
        static_assert(is_constant<1, decltype(get<major_dim>(L.stride()))>::value);
        return major_dim;
    }
}
template<typename L_t>
constexpr int flat_major_dim_length(L_t L) {
    constexpr auto flat_L = flatten(L_t{});
    constexpr int dim = flat_major_dim(flat_L);
    return get<dim>(flat_L.shape());
}
template<typename L> constexpr
bool has_major_dim() {
    /* A layout is considered to have a major dim if it has a node with a stride
    of 1 and shape >=2 */
    if constexpr (size(L{}) == 0 || size(L{}) == 1) {
        return true;
    }
    constexpr auto fL = flatten(L{});
    constexpr auto shpstr = zip(fL.shape(), fL.stride());
    return fold(shpstr, false, [](bool b, auto const& ss) {
        if constexpr (is_constant<1, decltype(get<1>(ss))>::value &&
                      decltype(get<0>(ss)){} >= _2{}) {
            return true;
        } else {
            return b;
        }
    });
}

template<typename Shp, typename Str, typename Scale>
constexpr auto scale_stride(Layout<Shp,Str> const L, Scale scale) {
    static_assert(is_static<Layout<Shp,Str>>::value, "Layout must be static");
    static_assert(is_static<Scale>::value, "Scale must be static");
    constexpr auto new_str = transform_leaf(Str{},
                                [](auto const& str_i){return str_i*Scale{};});
    return make_layout(L.shape(), new_str);
}

template<int I, int... Is, typename T>
constexpr auto drop(const T& t) {
    constexpr int r = rank(T{});
    static_assert(r>0, "Cannot drop from an empty tuple");
    static_assert(I >= 0 && I < r, "Index out of bounds");
    constexpr auto ids =  int_seq_tuple(make_int_sequence<r>());
    constexpr auto x = zip(ids, T{});
    return fold(x, tuple(), [](const auto& carry, const auto& xi) {
        using Xi = decltype(xi);
        if constexpr(get<0>(Xi{}) != I) {
            return append(carry, get<1>(Xi{}));
        } else {
            if constexpr(sizeof...(Is) == 0) {
                return carry;
            } else {
                return append(carry, drop<Is...>(get<1>(Xi{})));
            }
        }
    });
}

template<int I, int... Is, typename T, typename V>
constexpr auto nested_replace(const T& t, const V& v) {
    constexpr int r = rank(T{});
    static_assert(r>0, "Cannot replace an empty tuple");
    static_assert(I >= 0 && I < r, "Index out of bounds");
    constexpr auto ids =  int_seq_tuple(make_int_sequence<r>());
    constexpr auto x = zip(ids, T{});
    return fold(x, tuple(), [](const auto& carry, const auto& xi) {
        using Xi = decltype(xi);
        if constexpr(get<0>(Xi{}) != I) {
            return append(carry, get<1>(Xi{}));
        } else {
            if constexpr(sizeof...(Is) == 0) {
                return append(carry, V{});
            } else {
                return append(carry, nested_replace<Is...>(get<1>(Xi{}), V{}));
            }
        }
    });
}

template<int... Is, typename Shp, typename Str>
constexpr auto drop(const Layout<Shp, Str>& L) {
    return make_layout(drop<Is...>(Shp{}), drop<Is...>(Str{}));
}

// --------------- Layout SFINAE ---------------
// Detection idiom to check if zipped_divide works with specific types
template <typename Layout1, typename Layout2, typename = void>
struct can_zipped_divide : std::false_type {};

// This specialization only participates in overload resolution if 
// zipped_divide<Layout1, Layout2> is a valid expression
template <typename Layout1, typename Layout2>
struct can_zipped_divide<Layout1, Layout2, 
    std::void_t<decltype(zipped_divide(std::declval<Layout1>(), std::declval<Layout2>()))>> 
    : std::true_type {};


// --------------- Tuple and Layout Sorting ---------------
template<int r, typename T> constexpr
auto tuple_sort_pass() {
    if constexpr(r==rank(T{})-1) {
        return T{};
    } else if constexpr(get<r>(T{}) > get<r+1>(T{})) {
        using T1 = decltype(tuple_permute<r,r+1>(T{}));
        return tuple_sort_pass<r+1, T1>();
    } else {
        return tuple_sort_pass<r+1, T>();
    }
}
template<typename T> constexpr
auto tuple_sort_impl() {
    using T1 = decltype(tuple_sort_pass<0, T>());
    if constexpr(is_same_v<T1, T>) {
        return T{};
    } else {
        return tuple_sort_impl<T1>();
    }
}
template<typename T, typename D>
struct SortPair {
    T first{};
    D second{};
};

template<typename T1, typename D1, typename T2, typename D2>
constexpr bool operator>(const SortPair<T1,D1>& a, const SortPair<T2,D2>& b) {
    return T1{} > T2{};
}
/* Uses the order of the first tuple to sort the second tuple */
template<typename _T, typename _D>
constexpr auto sort_by() {
    using T = remove_cvref_t<_T>;
    using D = remove_cvref_t<_D>;
    constexpr auto fT = flatten(T{});
    constexpr auto fD = flatten(D{});
    constexpr auto fZ = zip(fT, fD);
    constexpr auto packed = transform(fZ,
            [](auto const t){return SortPair<decltype(get<0>(t)), decltype(get<1>(t))>{};});
    constexpr auto sorted = tuple_sort_impl<decltype(packed)>();
    constexpr auto sorted_D = transform(sorted, [](auto const& t){return t.second;});
    return sorted_D;
}

template<typename T, typename L>
constexpr auto sort_layout_by(T, L) {
    using Shp = remove_cvref_t<LayoutShape(L)>;
    using Str = remove_cvref_t<LayoutStride(L)>;
    auto sorted_shape = sort_by<T, Shp>();
    auto sorted_stride = sort_by<T, Str>();
    return make_layout(sorted_shape, sorted_stride);
}


// --------------- Structured Zip ---------------
CUTE_HOST_DEVICE auto zip_nested(auto structure, auto... ts);
template<size_t... Is>
CUTE_HOST_DEVICE auto unzip_and_recurse(auto const& zipped, std::index_sequence<Is...>) {
    return zip_nested(get<Is>(zipped)...);
}
CUTE_HOST_DEVICE auto zip_nested(auto structure, auto... ts) {
    if constexpr (is_tuple<decltype(structure)>::value) {
        return transform(zip(structure, ts...), [&](auto const& zipped) {
            return unzip_and_recurse(zipped, std::make_index_sequence<sizeof...(ts) + 1>{});
        });
    } else {
        return make_tuple(ts...);
    }
}
template<int... I>
CUTE_HOST_DEVICE auto zip_nested_tuple(auto structure, auto t, int_sequence<I...>) {  
    return zip_nested(structure, get<I>(t)...);
}
CUTE_HOST_DEVICE auto zip_nested_tuple(auto structure, auto t) {
    return zip_nested_tuple(structure, t, make_int_sequence<rank(t)>{});
}

// --------------- Natural Layout ---------------
template<typename Denom, typename... Args>
CUTE_HOST_DEVICE auto safe_div(tuple<Args...> t, Denom denom) {
    return transform(t, [&](auto const& a) {
        return safe_div(a, denom);
    });
}
template <class LShape, class LStride, class RShape, class RStride>
CUTE_HOST_DEVICE auto natural_composition_impl(LShape const& lhs_shape, LStride const& lhs_stride,
     RShape const& rhs_shape, RStride const& rhs_stride) {
    if constexpr (is_tuple<RShape>::value) {
        return transform_layout(rhs_shape, rhs_stride, [&](auto const& s, auto const& d) {
            return natural_composition_impl(lhs_shape, lhs_stride, s, d);
        });
    } else if constexpr (is_constant<0, RStride>::value) { // Special case for rhs_stride = 0, avoids division by zero
        auto [result_shape, rest_shape] = shape_minimum(lhs_shape, rhs_shape);
        auto result_stride = transform_leaf(lhs_stride, [&](auto const& d) {return _0{};});
        return make_layout(result_shape, result_stride);
    } else {
        auto result_shape_1 = shape_div(lhs_shape, rhs_stride);
        auto [result_shape_2, rest_shape] = shape_minimum(result_shape_1, rhs_shape);
        auto result_stride = elem_scale(lhs_stride, shape_div(lhs_shape, result_shape_1));
        auto result = make_layout(result_shape_2, result_stride);
        static_assert(size(decltype(result){})==decltype(rhs_shape){}, "Composition does not have the correct number of elements");
        static_assert(rank(decltype(result){})==rank(decltype(lhs_shape){}), "Composition does not have the correct rank");
        return result;
    }
}
CUTE_HOST_DEVICE auto natural_composition(auto LLayout, auto RLayout) {
    if constexpr (depth(RLayout) == 0) {
        return natural_composition_impl(LLayout.shape(), LLayout.stride(), wrap(RLayout.shape()), wrap(RLayout.stride()));
    } else {
        return natural_composition_impl(LLayout.shape(), LLayout.stride(), RLayout.shape(), RLayout.stride());
    }
}
// --------------- Layout Utilties ---------------
template<int... Is, typename Layout>
CUTE_HOST_DEVICE constexpr auto coalesce_each_impl(int_sequence<Is...>, Layout) {
    return make_layout(coalesce(get<Is>(Layout{}))...);
}

template<typename Layout>
CUTE_HOST_DEVICE constexpr auto coalesce_each(Layout const& layout) {
    constexpr auto rnk = rank(Layout{});
    return coalesce_each_impl(make_int_sequence<rnk>(), layout);
}

template<int... Is, typename Layout>
CUTE_HOST_DEVICE constexpr auto filter_each_impl(int_sequence<Is...>, Layout) {
    return make_layout(filter(get<Is>(Layout{}))...);
}

template<typename Layout>
CUTE_HOST_DEVICE constexpr auto filter_each(Layout const& layout) {
    constexpr auto rnk = rank(Layout{});
    return filter_each_impl(make_int_sequence<rnk>(), layout);
}


// Fill a tuple with X from the back until it has a rank of N
template<int N, typename X=_1, typename T>
CUTE_HOST_DEVICE constexpr auto fill_back(T const& t) {
    static_assert(N >= rank(T{}), "Cannot fill back a tuple with more elements than it currently has");
    if constexpr (N == rank(T{})) {
        return T{};
    } else {
        return fill_back<N>(append(T{}, X{}));
    }
}

// Fill a layout with 1 from the back until it has a rank of N
template<int N, typename Shape, typename Stride>
CUTE_HOST_DEVICE constexpr auto fill_back(Layout<Shape, Stride> const& layout) {
    static_assert(N >= rank(Shape{}), "Cannot fill back a layout with more elements than it currently has");
    if constexpr (N == rank(Shape{})) {
        return layout;
    } else {
        return make_layout(fill_back<N>(append(Shape{}, _1{})), fill_back<N>(append(Stride{}, Int<size(Shape{})>{})));
    }
}

template<int N, int... Is, typename Layout>
CUTE_HOST_DEVICE constexpr auto fill_back_each_impl(int_sequence<Is...>, Layout) {
    return make_layout(fill_back<N>(get<Is>(Layout{}))...);
}

template<int N, typename Layout>
CUTE_HOST_DEVICE constexpr auto fill_back_each(Layout const& layout) {
    constexpr auto rnk = rank(Layout{});
    return fill_back_each_impl<N>(make_int_sequence<rnk>(), layout);
}

// unwrap a layout until it has a rank > 1 or depth = 1
template<typename Layout>
CUTE_HOST_DEVICE constexpr auto unwrap_layout(Layout const& layout) {
    if constexpr (depth(Layout{}) >= 1 && rank(Layout{}.shape()) == 1) {
        return make_layout(unwrap(Layout{}.shape()), unwrap(Layout{}.stride()));
    } else {
        return layout;
    }
}

// rotate a tuple to the right by N elements
template<int N, typename T>
CUTE_HOST_DEVICE constexpr auto rotate(T const& t) {
    constexpr auto rnk = rank(T{});
    return append(take<rnk-N, -1>(t), take<0, rnk-N>(t));
}

// rotate a layout to the right by N elements
template<int N, typename Shape, typename Stride>
CUTE_HOST_DEVICE constexpr auto rotate(Layout<Shape, Stride> const& layout) {
    return make_layout(rotate<N>(layout.shape()), rotate<N>(layout.stride()));
}

template<int... Is, typename Shape1, typename Shape2>
CUTE_HOST_DEVICE constexpr auto rotating_divides_impl(Shape1 const& a, Shape2 const& b, int_sequence<Is...>) {
    return (evenly_divides(a, b) || ... || evenly_divides(rotate<Is>(a), b));
}

// rotating_divides checks if one shape divides another, as long as one rotated version of the shape divides the other
template<typename Shape1, typename Shape2>
CUTE_HOST_DEVICE constexpr auto rotating_divides(Shape1 const& a, Shape2 const& b) {
    constexpr auto rnk = rank(Shape1{});
    return rotating_divides_impl(a, b, make_int_sequence<rnk>());
}

template<typename Shape, typename Stride>
CUTE_HOST_DEVICE constexpr auto unwrap(Layout<Shape, Stride> const& layout) {
    return make_layout(unwrap(layout.shape()), unwrap(layout.stride()));
}

template<typename A, typename O, typename B>
CUTE_HOST_DEVICE constexpr auto unwrap(ComposedLayout<A,O,B> const& layout) {
    return composition(layout.layout_a(), layout.offset(), unwrap(layout.layout_b()));
}

// --------------- Tensor Utilities ---------------
#define TensorType(tensor) typename std::remove_reference_t<decltype(tensor)>::element_type

template<typename Storage, typename Layout>
CUTE_HOST_DEVICE auto coalesce_each(Tensor<Storage, Layout> const& tensor) {
    return make_tensor(tensor.data(), coalesce_each(tensor.layout()));
}

template<typename Storage, typename Layout, typename NewLayout>
CUTE_HOST_DEVICE auto relayout(Tensor<Storage, Layout> const& tensor, NewLayout const& new_layout) {
    return make_tensor(tensor.data(), new_layout);
}

template<typename YTensor>
CUTE_HOST_DEVICE auto unwrap_tensor(YTensor const& Y) {
    if constexpr (depth(YTensor{}) >= 1 && rank(YTensor{}.shape()) == 1) {
        return Y(make_coord(repeat<decltype(rank<0>(Y))::value>(_)));
    } else {
        return Y;
    }
}
CUTE_HOST_DEVICE auto slice_rest(auto const& X, auto const& L, auto const& idx) {
    return unwrap_tensor(X.compose(L)(_, idx));
}
CUTE_HOST_DEVICE auto slice_rest(auto const& X, auto const& idx) {
    return unwrap_tensor(X(_, idx));
}

// Tensor Creations
template<typename T>
auto make_managed_tensor(auto layout) {
    T* ptr;
    cudaMallocManaged(&ptr, cosize(layout) * sizeof(T));
    return make_tensor(ptr, layout);
}
template <typename T, typename Layout>
CUTE_HOST_DEVICE auto arange_tensor(Layout layout) {
    auto tensor = make_tensor<T>(layout);
    for (int i = 0; i < size(tensor); ++i) {
        tensor(i) = T(i);
    }
    return tensor;
}

template <typename T, typename Layout>
CUTE_HOST_DEVICE auto ones_tensor(Layout layout) {
    auto tensor = make_tensor<T>(layout);
    for (int i = 0; i < size(tensor); ++i) {
        tensor(i) = T(1);
    }
    return tensor;
}

// Operations with tensors

// Deprecated broadcast ops. No longer used in tprod
template<int match_dim, typename XTensor, typename YTensor>
CUTE_HOST_DEVICE void broadcast_multiply(const XTensor& X, YTensor& Y) {
    auto bcast_layout = broadcast_layout<match_dim>(X.layout(), Y.layout());
    auto X_bcast = composition(X, bcast_layout);
    for (int i=0; i<size(Y); ++i) {
        Y(i) = Y(i) * static_cast<typename YTensor::value_type>(X_bcast(i));
    }
}
template<int... match_dims, typename YTensor, typename... XTensors>
CUTE_HOST_DEVICE void chain_broadcast_multiply(int_sequence<match_dims...>, YTensor& Y, const XTensors&... Xs) {
    static_assert(sizeof...(match_dims) == sizeof...(XTensors), "Number of dimensions must match number of tensors");
    (broadcast_multiply<match_dims>(Xs, Y), ...);
}

template<typename YTensor, typename... XTensor>
CUTE_HOST_DEVICE void add_tensor(YTensor& Y, const XTensor&... Xs) {
    // all tensors must have the same shape
    for (int i=0; i<size(Y); ++i) {
        Y(i) = static_cast<typename YTensor::value_type>((Y(i) + ... + Xs(i)));
    }
}
template<typename YTensor, typename Scalar>
CUTE_HOST_DEVICE void add_tensor_scalar(YTensor& Y, Scalar s) {
    for (int i=0; i<size(Y); ++i) {
        Y(i) = static_cast<typename YTensor::value_type>(Y(i) + s);
    }
}

template<typename YTensor, typename Scalar>
CUTE_HOST_DEVICE void tensor_scalar_div(YTensor& Y, Scalar s) {
    for (int i=0; i<size(Y); ++i) {
        Y(i) = static_cast<typename YTensor::value_type>(Y(i) / s);
    }
}

template<typename YTensor, typename Scalar>
CUTE_HOST_DEVICE void tensor_scalar_prod(YTensor& Y, Scalar s) {
    for (int i=0; i<size(Y); ++i) {
        Y(i) = Y(i) * s;
    }
}

CUTE_HOST_DEVICE void tensor_inner_prods(auto& y, auto& a, auto& b) {
    assert(size(y) == size<1>(a));
    assert(size(y) == size<1>(b));
    assert(size<0>(a) == size<0>(b));
    for (int batch = 0; batch < size(y); ++batch) {
        y(batch) = 0;
        for (int i = 0; i < size<0>(a); ++i) {
            y(batch) += a(make_coord(i, batch)) * b(make_coord(i, batch));
        }
    }
}



template<int... Is, typename Tensor>
CUTE_HOST_DEVICE auto transpose_tensor(Tensor const& tensor) {
    auto layout = transpose_layout<Is...>(tensor.layout());
    return make_tensor(tensor.data(), layout);
}

template<int match_dim, typename XTensor, typename YTensor>
CUTE_HOST_DEVICE void broadcast_set(const XTensor& X, YTensor& Y) {
    auto bcast_layout = broadcast_layout<match_dim>(X.layout(), Y.layout());
    auto X_bcast = composition(X, bcast_layout);
    for (int i = 0; i < size(Y); ++i) {
        Y(i) = static_cast<typename YTensor::value_type>(X_bcast(i));
    }
}

template <typename TensorA, typename TensorB>
bool check_tensors_match(const TensorA& A, const TensorB& B, float tol = 0.0f, bool print_match = true) {
    if (size(A) != size(B)) {
        if(print_match) std::cerr << "Tensor sizes don't match: " << size(A) << " vs " << size(B) << std::endl;
        return false;
    }
    bool match = true;
    int mismatch_count = 0;
    for (int i = 0; i < size(A); ++i) {
        float a = float(A(i));
        float b = float(B(i));
        bool abs_tol_check = (std::abs(a - b) <= tol);
        float scale = (std::abs(a) + std::abs(b))/2.0f;
        bool rel_tol_check = (std::abs(a - b) <= tol * scale);
        bool values_match = abs_tol_check || rel_tol_check;
        if (!values_match) {
            match = false;
            if (print_match && mismatch_count < 10) {
                std::cerr << "Mismatch at index " << i << ":  " 
                         << float(A(i)) << " != " << float(B(i)) 
                         << "  (diff: " << std::abs(float(A(i)) - float(B(i))) << ")" << std::endl;
            } else if (print_match && mismatch_count == 10) {
                std::cerr << "Ignoring the rest of mismatches..." << std::endl;
            }
            mismatch_count++;
        }
    }
    if (print_match) {
        if (match) {
            std::cout << "\033[32mTensors match" << (tol > 0.0f ? " within tolerance" : "") << "\033[0m" << std::endl;
        } else {
            std::cout << "\033[31mTensors do not match" << (tol > 0.0f ? " within tolerance" : "") << "\033[0m" << std::endl;
        }
    }
    return match;
}

template<typename XEngine, typename XLayout>
void randomize_tensor(Tensor<XEngine, XLayout>& X) {
    using T = TensorType(X);
    std::random_device rd;  // Obtain a random number from hardware
    std::mt19937 gen(rd()); // Seed the generator
    std::uniform_real_distribution<T> distrib(0.0, 1.0); // Define the range [0.0, 1.0)
    for (int i = 0; i < size(X); ++i) X(i) = distrib(gen);
}

// --------------- Compile-time Math ---------------
// Compile-time square root using Newton's method
constexpr int static_sqrt_impl(int x, int guess, int iter = 0) {
    // For 32-bit integers, 16 iterations is more than enough:
    // - Each iteration roughly doubles precision
    // - 2^16 is already way larger than any possible number of iterations needed
    if (iter >= 16) return guess;
    
    int next_guess = (x / guess + guess) / 2;
    // Return when we find the exact root or when we can't get any closer
    return (next_guess >= guess) ? guess : static_sqrt_impl(x, next_guess, iter + 1);
}

constexpr int static_sqrt(int x) {
    return x <= 0 ? 0 : static_sqrt_impl(x, x/2 + 1);
}

constexpr int is_square(int x) {
    int y = static_sqrt(x);
    return y*y == x ? true : false;
}

// Helper for adding factors to the tuple
template<int N, int Current = 1, typename Accum = tuple<>>
constexpr auto factor_impl() {
    if constexpr (Current > N) {
        return Accum{};
    } else if constexpr (N % Current == 0) {
        return factor_impl<N, Current + 1, decltype(append(Accum{}, Int<Current>{}))>();
    } else {
        return factor_impl<N, Current + 1, Accum>();
    }
}

// Helper for adding prime factors to the tuple
template<int N, int Current = 2, typename Accum = tuple<>>
constexpr auto prime_factor_impl() {
    if constexpr (N == 1) {
        return Accum{};
    } else if constexpr (Current * Current > N) {
        return append(Accum{}, Int<N>{});
    } else if constexpr (N % Current == 0) {
        return prime_factor_impl<N / Current, Current, decltype(append(Accum{}, Int<Current>{}))>();
    } else {
        return prime_factor_impl<N, Current + 1, Accum>();
    }
}

// Helper for factorizing into a pair of factors
template<int N, int Current = 1>
constexpr auto factor_pairs_impl() {
    if constexpr (Current * Current > N) {
        return tuple<>{};
    } else if constexpr (N % Current == 0) {
        using pair = tuple<Int<Current>, Int<N/Current>>;
        if constexpr (Current == N/Current) {
            return tuple<pair>{};
        } else {
            return append(factor_pairs_impl<N, Current + 1>(), pair{});
        }
    } else {
        return factor_pairs_impl<N, Current + 1>();
    }
}

// Returns all factors of N as a tuple of Int<Factor>
template<int N>
constexpr auto factor() {
    static_assert(N > 0, "Cannot factorize non-positive number");
    return factor_impl<N>();
}

// Returns all prime factors of N (including duplicates) as a tuple of Int<PrimeFactor>
template<int N>
constexpr auto prime_factors() {
    static_assert(N > 0, "Cannot factorize non-positive number");
    return prime_factor_impl<N>();
}

// Returns all factor pairs (a,b) where a*b=N as a tuple of tuple<Int<a>, Int<b>>
template<int N>
constexpr auto factor_pairs() {
    static_assert(N > 0, "Cannot factorize non-positive number");
    return factor_pairs_impl<N>();
}

template<int x>
constexpr int static_log2() {
    static_assert(x > 0, "log2 of non-positive number is undefined");
    if constexpr (x == 1) {
        return 0;
    } else {
        return 1 + static_log2<x/2>();
    }
}

template<typename T>
constexpr T static_min(T a, T b) {
    if constexpr (a < b) {
        return a;
    } else {
        return b;
    }
}

using index_t = int64_t;
constexpr index_t n_choose_k(index_t n, index_t k) {
    if (k > n) return 0;
    if (k == 0) return 1;
    index_t result = 1;
    for(index_t i = 1; i <= k; ++i) {
        result *= (n - i + 1);
        result /= i;
    }
    return result;
}
constexpr index_t factorial(index_t n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}
template<int n, typename T>
constexpr T static_pow(T x) {
    static_assert(n > 0, "n must be positive");
    if constexpr (n == 1) return x;
    else return x * static_pow<n-1>(x);
}

// --------------- Complex Layout Utilities ---------------

// if N >= size(L) return make_layout(L, _1)
// if N < size(L) 
//     if N divides size(L), return a layout Y s.t. size<0>(Y) == N and size<1>(Y) == size(L) / N 
//     else raise compile-time error
template<int N, typename Shape, typename Stride>
constexpr auto size_divide(Layout<Shape, Stride> L) {
    if constexpr (N >= size(L)) {
        return make_layout(L, make_layout(_1{}));
    } else {
        static_assert(size(L) % N == 0, "N does not divide size(L)");
        using L_flat = decltype(flatten(L.layout()));
        constexpr auto l_flat = L_flat{};
        constexpr auto init = make_tuple(make_layout(make_shape(_1{})), L_flat{});
        constexpr auto result = fold(zip(l_flat.shape(), l_flat.stride()), init, [](auto carry, auto mode_i) {
            constexpr auto cur = get<0>(carry);
            constexpr auto l_remain = get<1>(carry);

            if constexpr (size(cur) == N) { // terminal case
                return make_tuple(cur, l_remain);
            } else if constexpr (size(cur) * size<0>(mode_i) <= N) { // add one more mode if not reaching N
                return make_tuple(append(cur, make_layout(get<0>(mode_i), get<1>(mode_i))), take<1, rank(l_remain)>(l_remain));
            } else { // try to split the mode into two
                static_assert(N % size(cur) == 0, "N is not divisible by the current size, not possible to split");
                constexpr auto left_split = Int<N / size(cur)>{};
                constexpr auto factors = factor<get<0>(mode_i)>();
                constexpr auto found = any_of(factors, [&](auto x) { return get<0>(x) == left_split; });
                static_assert(found, "Not possible to split the mode into two factors such that N is divisible by the current size");
                constexpr auto right_split = get<0>(mode_i) / left_split;
                constexpr auto right_stride = get<1>(mode_i) * left_split;
                constexpr auto left_mode = make_layout(left_split, get<1>(mode_i));
                constexpr auto right_mode = make_layout(right_split, right_stride);
                if constexpr (rank(l_remain) == 1) {
                    return make_tuple(append(cur, left_mode), right_mode);
                } else {
                    return make_tuple(append(cur, left_mode), prepend(take<1, rank(l_remain)>(l_remain), right_mode));
                }
            }
        });
        return coalesce_each(make_layout(get<0>(result), get<1>(result)));
    }
}

// Returns the largest contiguous patch in the codomain of a layout
template<typename Shape, typename Stride>
constexpr auto largest_contiguous_cosize(Layout<Shape, Stride> L) {
    constexpr auto sorted_L = sort_layout_by(L.stride(), L);
    return get<0>(fold(zip(decltype(sorted_L.shape()){}, decltype(sorted_L.stride()){}), make_tuple(_1{}, _1{}), [](auto carry, auto mode_i) {
        if constexpr (get<1>(mode_i) != get<1>(carry)) {
            return make_tuple(get<0>(carry), get<1>(mode_i));
        } else {
            return make_tuple(get<0>(carry)*get<0>(mode_i), get<1>(carry)*get<0>(mode_i));
        }
    }));
}


// --------------- Print Utilities ---------------
CUTE_HOST_DEVICE void th0_print(auto... xs) {
    if (thread0()) {
        (print(xs), ...);
    }
}
CUTE_HOST_DEVICE void th0_print_tensor(auto& tensor) {
    if (thread0()) {
        print_tensor(tensor);
    }
}
CUTE_HOST_DEVICE void th0_println(auto... xs) {
    th0_print(xs...);
    th0_print("\n");
}
template<typename Shp, typename FrgThr>
__device__ void FrgThr_print(Shp, FrgThr, auto& x_frg, int tid) {
    using T = TensorType(x_frg);
    __shared__ T smem[int(size(Shp{}))];
    auto sx = make_tensor(make_smem_ptr(smem), make_layout(Shp{}));
    if (tid < size<1>(FrgThr{}))
        copy(x_frg, slice_rest(sx, FrgThr{}, tid));
    __syncthreads();
    if (thread0()) {
        print_tensor(sx);
    }
}

} // namespace mosaic