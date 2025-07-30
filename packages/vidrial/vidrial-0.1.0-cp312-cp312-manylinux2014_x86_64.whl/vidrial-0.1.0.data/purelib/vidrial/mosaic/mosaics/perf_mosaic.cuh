#pragma once

#include <type_traits>
#include <utility>

namespace mosaic {

template<int smempipe_=2, int regpipe_=1, bool use_ldsm_=true, int swizzle_=0>
struct PerfMosaic {
    static constexpr int smempipe = smempipe_;
    static constexpr int regpipe = regpipe_;
    static constexpr bool use_ldsm = use_ldsm_;
    static constexpr int swizzle = swizzle_;
};

using DefaultPerf = PerfMosaic<2, 1, true, 0>;

} // namespace mosaic

