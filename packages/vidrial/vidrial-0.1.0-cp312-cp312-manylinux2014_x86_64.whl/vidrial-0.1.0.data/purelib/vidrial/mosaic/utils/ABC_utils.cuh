#pragma once

#include <cute/tensor.hpp>

using namespace cute;

struct A_t{}; struct B_t{}; struct C_t{};

// get_MNK
auto ABC_get_MNK(A_t, auto MNK) {
    return select<0,2>(MNK);
}
auto ABC_get_MNK(B_t, auto MNK) {
    return select<1,2>(MNK);
}
auto ABC_get_MNK(C_t, auto MNK) {
    return select<0,1>(MNK);
}

// get_MNKP
auto ABC_get_MNKP(A_t, auto MNKP) {
    return select<0,2,3>(MNKP);
}
auto ABC_get_MNKP(B_t, auto MNKP) {
    return select<1,2,3>(MNKP);
}
auto ABC_get_MNKP(C_t, auto MNKP) {
    return select<0,1,3>(MNKP);
}

// get_TV_layout
template<typename MmaAtom>
auto ABC_get_TV_layout(A_t, MmaAtom) {
    return typename MmaAtom::LayoutA_TV{};
}
template<typename MmaAtom>
auto ABC_get_TV_layout(B_t, MmaAtom) {
    return typename MmaAtom::LayoutB_TV{};
}
template<typename MmaAtom>
auto ABC_get_TV_layout(C_t, MmaAtom) {
    return typename MmaAtom::LayoutC_TV{};
} 

// project_MNK
template<typename MNK>
auto ABC_project_MNK(A_t, MNK) {
    static_assert(rank(MNK{}) == 3, "MNK must have 3 dimensions");
    return make_layout(MNK{},
                       make_stride(_1{}, _0{}, get<0>(MNK{})));
}
template<typename MNK>
auto ABC_project_MNK(B_t, MNK) {
    static_assert(rank(MNK{}) == 3, "MNK must have 3 dimensions");
    return make_layout(MNK{},
                       make_stride(_0{}, _1{}, get<1>(MNK{})));
}
template<typename MNK>
auto ABC_project_MNK(C_t, MNK) {
    static_assert(rank(MNK{}) == 3, "MNK must have 3 dimensions");
    return make_layout(MNK{},
                       make_stride(_1{}, get<0>(MNK{}), _0{}));
}


template<typename ABC_t, typename MmaAtom>
struct ABC_FrgType { using type = false_type; };
template<typename MmaAtom>
struct ABC_FrgType<A_t, MmaAtom> { using type = typename MmaAtom::FrgTypeA; };
template<typename MmaAtom>
struct ABC_FrgType<B_t, MmaAtom> { using type = typename MmaAtom::FrgTypeB; };
template<typename MmaAtom>
struct ABC_FrgType<C_t, MmaAtom> { using type = typename MmaAtom::FrgTypeC; };


