#pragma once

#include <cute/tensor.hpp>
#include "utilities.cuh"
#include <type_traits>

namespace mosaic {

// -------------- Tensor Product Layout Operations --------------
template <typename... Shapes>
CUTE_HOST_DEVICE constexpr auto tprod_shape(Shapes... shapes) {
    static_assert(sizeof...(Shapes) > 0, "At least one shape must be provided");
    static_assert(((rank(shapes) == 2) && ...), "All shapes must have rank 2");
    constexpr auto batch =(get<1>(shapes), ...);
    static_assert( ((get<1>(shapes) == batch) && ...), "The second dimensions of the input shapes must be the same");
    auto feature_shape = make_shape(get<0>(shapes)...);
    return make_shape(feature_shape, batch);
}
CUTE_HOST_DEVICE auto colayout(auto coshape, auto L) {
    // coshape is [[d, d, ...], b]
    auto Lflat = flatten(L); // [d_tile, d_tile, ..., b_tile]
    auto LL = make_layout(coshape).compose(Lflat);
    auto Lnat = natural_composition(make_layout(coshape), Lflat);  // [d_tile, d_tile, ..., b_tile], but on the canonical layout of the coshape
    auto L_nat_trans = make_layout(zip_nested_tuple(coshape, Lnat.shape()),
                                   zip_nested_tuple(coshape, Lnat.stride()));
    DEBUG_ASSERT(weakly_congruent(coshape, L_nat_trans));
    return coalesce(L_nat_trans, coshape);
}
template<int dim>
CUTE_HOST_DEVICE auto tprod_layout_factor(auto coshape, auto L) {
    // coshape: [[d, d, ...], b]
    // L: [[[d_tile, d_tile, ...], b_tile], and a layout
    auto coL = colayout(coshape, L);
    auto proj_shape = make_shape(get<0,dim>(coL.shape()),
                                 get<1>(coL.shape()));
    auto feat_coshape = get<0>(coshape);
    auto x = size(take<0,dim>(feat_coshape)); // size of the features left to dim
    auto proj_feat_stride = safe_div(get<0,dim>(coL.stride()),x);
    auto y = safe_div(size(feat_coshape),get<dim>(feat_coshape)); // size of features excluded from the projection
    auto proj_batch_stride = safe_div(get<1>(coL.stride()), y);
    return make_layout(proj_shape, make_stride(proj_feat_stride, proj_batch_stride));
}
template<int dim>
CUTE_HOST_DEVICE auto set_zero_except(auto t) {
    static_assert(dim >= 0 && dim < rank(t), "dim is out of bounds");
    auto zero_t = transform_leaf(t, [](auto x) { return _0{}; });
    return replace<dim>(zero_t, get<dim>(t));
}
template<int dim>
CUTE_HOST_DEVICE auto tprod_layout_projection(auto _coshape, auto L) {
    // coshape is [[f1, f2, ...], b]  where f1, f2, ... and b are all static integers
    auto coshape = make_shape(transform(get<0>(_coshape), [](auto x) { return size(x); }),
                              size<1>(_coshape));
    auto coL = colayout(coshape, L);
    auto feat_coshape = get<0>(coshape);
    auto proj_feat_stride1 = set_zero_except<dim>(stride<0>(coL));
    auto x = size(take<0,dim>(feat_coshape)); // size of the features left to dim
    auto proj_feat_stride = safe_div(proj_feat_stride1, x);
    auto y = safe_div(size(feat_coshape),get<dim>(feat_coshape)); // size of features excluded from the projection
    auto proj_batch_stride = safe_div(get<1>(coL.stride()), y);
    auto coProj = make_layout(coL.shape(), make_stride(proj_feat_stride, proj_batch_stride));
    // coProj.shape() is coshape. We want to return a projection layout with the same shapes as L
    auto proj = coProj.compose(left_inverse(coL).compose(L));
    return proj;
}
template<int dim>
CUTE_HOST_DEVICE auto TV_layout_factor(auto coshape, auto TV) {
    return make_layout(tprod_layout_projection<dim>(coshape, get<0>(TV)),
                       tprod_layout_factor<dim>(coshape, get<1>(TV)));
}
template<int dim>
CUTE_HOST_DEVICE auto tprod_factor_project(auto const& coshape, auto const& factoredLayout, auto const& ProjectedLayout) {
    // coshape: [[d, d, ...], b]
    // factoredLayout: [[d_tile, d_tile, ...], b_tile]
    // ProjectedLayout: [[d_rest, d_rest, ...], b_rest]
    return make_layout(tprod_layout_factor<dim>(coshape, factoredLayout),
                       tprod_layout_projection<dim>(coshape, ProjectedLayout));
}
template<int dim>
CUTE_HOST_DEVICE auto tprod_factor_project(auto const& coshape, auto const& Layout) {
    // coshape: [[d, d, ...], b]
    // Layout: [[[d_tile, d_tile, ...], b_tile], [[d_rest, d_rest, ...], b_rest]], and a layout
    return tprod_factor_project<dim>(coshape, get<0>(Layout), get<1>(Layout));
}
// Deprecated functions. TODO: transfrom their tests into batched tests and remove
template<int dim>
CUTE_HOST_DEVICE auto tprod_layout_factor_batchless(auto coshape, auto L) {
    auto coL = colayout(coshape, L);
    auto proj_shape = get<dim>(coL.shape());
    auto proj_stride = safe_div(get<dim>(coL.stride()), size(take<0,dim>(coshape)));
    return make_layout(proj_shape, proj_stride);
}
template<int dim>
CUTE_HOST_DEVICE auto tprod_layout_projection_batchless(auto coshape, auto L) {
    auto coL = colayout(coshape, L);
    auto one_hot = one_hot_int_tuple<rank(coshape), dim>(); // tuple of 0s with 1 at dim
    auto proj_stride1 = elem_scale(coL.stride(), one_hot);
    auto proj_stride = safe_div(proj_stride1, size(take<0,dim>(coshape)));
    return make_layout(coL.shape(), proj_stride);
}

// --------------- tprod Operations on cute Tensors ---------------
template <int dim, typename YTensor, typename XTensor>
CUTE_HOST_DEVICE void tprod_bcast_multiply(YTensor& Y, const XTensor& X) {
    auto X_bcast_layout = tprod_layout_projection<dim>(Y.shape(), make_layout(Y.shape()));
    auto X_bcast = X.compose(X_bcast_layout);
    static_assert(compatible(decltype(Y.layout()){}, decltype(X_bcast.layout()){}));
    for (int i = 0; i < size(Y); ++i)
        Y(i) = Y(i) * static_cast<TensorType(Y)>(X_bcast(i));
}
template <int dim, typename YTensor, typename XTensor>
CUTE_HOST_DEVICE void tprod_bcast_divide(YTensor& Y, const XTensor& X) {
    auto X_bcast_layout = tprod_layout_projection<dim>(Y.shape(), make_layout(Y.shape()));
    auto X_bcast = X.compose(X_bcast_layout);
    static_assert(compatible(decltype(Y.layout()){}, decltype(X_bcast.layout()){}));
    for (int i = 0; i < size(Y); ++i)
        Y(i) = Y(i) / static_cast<TensorType(Y)>(X_bcast(i));
}
template <typename YTensor, typename XTensor, typename... XTensors>
CUTE_HOST_DEVICE void tprod_impl(YTensor& Y, const XTensor& X, const XTensors&... Xs) {
    constexpr int bcast_dim = rank<0>(decltype(Y.layout()){}) -1 -sizeof...(XTensors);
    tprod_bcast_multiply<bcast_dim>(Y, X);
    if constexpr (sizeof...(XTensors) > 0)
        tprod_impl(Y, Xs...);
}
template <typename YTensor, typename... XTensors>
CUTE_HOST_DEVICE void tprod(YTensor&& Y, const XTensors&... Xs) {
    fill(Y, static_cast<TensorType(Y)>(1.));
    tprod_impl(Y, Xs...);
}

// -------------- Tensor Power --------------
template<int... Is>
auto tpow_shape_impl(auto shape, int_sequence<Is...>) {
    // same as tprod_shape(shape, shape, ....) p times
    return tprod_shape(((void)Is, shape)...);
}
template<int p>
auto tpow_shape(auto shape) {
    return tpow_shape_impl(shape, make_int_sequence<p>{});
}

template <auto p, auto... Is, typename YT, typename... XT>
CUTE_HOST_DEVICE void tpow_impl(index_sequence<Is...>, YT&& Y, tuple<XT...> X) {
    tprod(Y, get<Is>(X)...);
}
template <auto p, typename YT, typename XT>
CUTE_HOST_DEVICE void tpow(YT&& Y, XT&& X) {
    tpow_impl<p>(make_index_sequence<p>{}, Y, repeat<p>(X));
}
 

} // namespace mosaic 
