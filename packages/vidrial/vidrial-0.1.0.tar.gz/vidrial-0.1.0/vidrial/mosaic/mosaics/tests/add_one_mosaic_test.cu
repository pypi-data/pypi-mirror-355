#include "utilities.cuh"
#include "add_one_kernels.cuh"
#include <gtest/gtest.h>

TEST(AddOneMosaicTest, SimpleAddition) {
    using SlabShape = Shape<_32, _32>;
    using ASlab = Layout<SlabShape>;
    using TileShape = Shape<_16,_16>;
    auto gA = make_managed_tensor<float>(ASlab{});
    for (int i = 0; i < size(gA); i++) { gA(i) = i; }
    launch_add_one_inplace<float, 32, SlabShape, TileShape, ASlab>(gA.data());
    cudaDeviceSynchronize();
    auto gA_ref = make_managed_tensor<float>(ASlab{});
    for (int i = 0; i < size(gA); i++) { gA_ref(i) = i+1; }
    bool match = check_tensors_match(gA, gA_ref, 0., false);
    EXPECT_TRUE(match);
}

int main(int argc, char **argv) {
    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
} 