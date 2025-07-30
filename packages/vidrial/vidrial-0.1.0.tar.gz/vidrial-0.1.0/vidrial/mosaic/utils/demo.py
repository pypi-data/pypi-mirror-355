# import torch as th
# from tyle.kernels.sympow.reference import *

# print("\nThe tpow and sympow functions");
# x = th.arange(3)
# y = tpow(x, 2)
# z = sympow(x, 2, duplicate_correction=False)
# print("x: ", x)
# print("y: ", y)
# print("z: ", z)
# print()
# x = th.arange(4)
# y = tpow(x, 2)
# z = sympow(x, 2, duplicate_correction=False)
# print("x: ", x)
# print("y: ", y)
# print("z: ", z)

# print("\nHigher powers");
# x = th.arange(4)
# y = tpow(x, 3)
# z = sympow(x, 3, duplicate_correction=False)
# print("x.shape: ", x.shape)
# print("y.shape: ", y.shape)
# print("z.shape: ", z.shape)

# print("\nWith batch dimension");
# x = th.arange(12*4).reshape(12,4) % 8
# y = tpow(x, 2)
# z = sympow(x, 2, duplicate_correction=False)
# print('x.shape: ', x.shape)
# print("y.shape: ", y.shape)
# print("z.shape: ", z.shape)

# print("\nHigh rank symmetric tensors:")
# print(y.sum(0))
# print(z.sum(0))

# print("\nArbitrary number of batch dimensions");
# x = th.randn(2,3,4)
# y = tpow(x, 2)
# z = sympow(x, 2, duplicate_correction=False)
# print('x.shape: ', x.shape)
# print("y.shape: ", y.shape)
# print("z.shape: ", z.shape)

# print("\nPreserving the norm of tpow instead of the elements");
# x = th.rand(4)
# print("norm(y): ", th.linalg.norm(tpow(x, 2)))
# print("With duplicate_correction=False:")
# print("norm(z): ", th.linalg.norm(sympow(x, 2, duplicate_correction=False)))
# print("With duplicate_correction=True:")
# print("norm(z): ", th.linalg.norm(sympow(x, 2, duplicate_correction=True)))

# print("\nRunning on the GPU:")
# x = th.randn(4, 8, device="cuda")
# z_gpu = sympow(x, power=2)
# z_cpu = sympow(x.cpu().clone(), power=2)
# print("allclose(z_gpu, z_cpu): ", th.allclose(z_gpu.cpu(), z_cpu))
# x = th.randn(4, 16, device="cuda")
# z_gpu = sympow(x, power=3)
# z_cpu = sympow(x.cpu().clone(), power=3)
# print("allclose(z_gpu, z_cpu): ", th.allclose(z_gpu.cpu(), z_cpu))


# print("\nTiled sympow: interpolating between sympow and tpow")
# x = th.randn(2,16)
# z = sympow(x, power=2)
# z_tile1 = sympow(x, power=2, d_tile=1)
# z_tile2 = sympow(x, power=2, d_tile=2)
# z_tile4 = sympow(x, power=2, d_tile=4)
# z_tile8 = sympow(x, power=2, d_tile=8)
# z_tile16 = sympow(x, power=2, d_tile=16)
# y = tpow(x, power=2)
# print("x.shape: ", list(x.shape))
# print("z.shape: ", list(z.shape))
# print("z_tile1.shape: ", list(z_tile1.shape))
# print("z_tile2.shape: ", list(z_tile2.shape))
# print("z_tile4.shape: ", list(z_tile4.shape))
# print("z_tile8.shape: ", list(z_tile8.shape))
# print("z_tile16.shape: ", list(z_tile16.shape))
# print("y.shape: ", list(y.shape))

# print("\nsympow_expand arbitary rank tensors")
# x = th.randn(2,3,4,5)
# print("x.shape: ", list(x.shape))
# for i in range(len(x.shape)):
#     ex = sympow_expand(x, expand_dim=i, power=2)
#     print(f"expand_dim={i}, ex.shape={list(ex.shape)}")

# print("\nsympow_expand works with tiled sympow")
# x = th.randn(2,4,8,16)
# print("x.shape: ", list(x.shape))
# for i in range(len(x.shape)):
#     ex = sympow_expand(x, expand_dim=i, power=2)
#     ex_tile_2 = sympow_expand(x, expand_dim=i, power=2, d_tile=2)
#     print(f"expand_dim={i}, ex.shape={list(ex.shape)}, ex_tile_2.shape={list(ex_tile_2.shape)}")

# print("\nFused sympow mma: expanding the -2 dimension of A")
# A = th.randn(2, 16, 16, device="cuda")
# B = th.randn(2, 16, 32, device="cuda")
# eA = sympow_expand(A.cpu(), -2, power=2, d_tile=4)
# C_ref = eA @ B.cpu()
# fused_C = sympow_expandA_mma(A, B, -2, power=2, d_tile=4)
# print("A.shape: ", list(A.shape))
# print("eA.shape: ", list(eA.shape))
# print("B.shape: ", list(B.shape))
# print("C.shape: ", list(C_ref.shape))
# tol = 1e-2
# print("allclose(fused_C, C_ref): ", th.allclose(fused_C.cpu(), C_ref, atol=tol, rtol=tol))
 
# print("\nFused sympow mma: expanding the -1 dimension of A")
# A = th.randn(2, 16, 16, device="cuda")
# B = th.randn(2, 160, 32, device="cuda")
# eA = sympow_expand(A.cpu(), -1, power=2, d_tile=4)
# C_ref = eA @ B.cpu()
# fused_C = sympow_expandA_mma(A, B, -1, power=2, d_tile=4)
# print("A.shape: ", list(A.shape))
# print("eA.shape: ", list(eA.shape))
# print("B.shape: ", list(B.shape))
# print("C.shape: ", list(C_ref.shape))
# tol = 1e-1
# print("allclose(fused_C, C_ref): ", th.allclose(fused_C.cpu(), C_ref, atol=tol, rtol=tol))
# print("fused_C: ", fused_C.flatten()[:500:10])
# print("C_ref: ", C_ref.flatten()[:500:10])
 