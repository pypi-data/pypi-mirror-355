# Copyright 2025 BDP Ecosystem Limited. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

# -*- coding: utf-8 -*-
import triton
import triton.language as tl
import torch
import time

# ——— Triton Kernel ———
@triton.jit
def ternary_matmul_mm_kernel(
    X_ptr, P_ptr, N_ptr, Y_ptr,
    M, N, K,
    sx0, sx1, sp0, sp1, sn0, sn1, sy0, sy1,
    BLOCK_M: tl.constexpr, BLOCK_N: tl.constexpr, BLOCK_K: tl.constexpr
):
    row_start = tl.program_id(0) * BLOCK_M
    col_start = tl.program_id(1) * BLOCK_N

    offs_m = row_start + tl.arange(0, BLOCK_M)
    offs_n = col_start + tl.arange(0, BLOCK_N)
    mask_m = offs_m < M
    mask_n = offs_n < N

    acc = tl.zeros([BLOCK_M, BLOCK_N], dtype=tl.float32)

    for k_start in range(0, K, BLOCK_K):
        offs_k = k_start + tl.arange(0, BLOCK_K)
        mask_k = offs_k < K

        # Load blocks
        x = tl.load(
            X_ptr + offs_k[:, None] * sx0 + offs_n[None, :] * sx1,
            mask=(mask_k[:, None] & mask_n[None, :]), other=0.0
        )                              # [BLOCK_K, BLOCK_N]
        p = tl.load(
            P_ptr + offs_m[:, None] * sp0 + offs_k[None, :] * sp1,
            mask=(mask_m[:, None] & mask_k[None, :]), other=0
        ).to(tl.float32)               # [BLOCK_M, BLOCK_K]
        n = tl.load(
            N_ptr + offs_m[:, None] * sn0 + offs_k[None, :] * sn1,
            mask=(mask_m[:, None] & mask_k[None, :]), other=0
        ).to(tl.float32)               # [BLOCK_M, BLOCK_K]

        # Vectorized accumulation (no Python loops!)
        coef = p - n                    # [BLOCK_M, BLOCK_K]
        acc += tl.sum(coef[:, :, None] * x[None, :, :], axis=1)

    # Store result
    tl.store(
        Y_ptr + offs_m[:, None] * sy0 + offs_n[None, :] * sy1,
        acc,
        mask=(mask_m[:, None] & mask_n[None, :])
    )



def ternary_matmul_mm_triton(X, P, N,
                             BLOCK_M=64, BLOCK_N=64, BLOCK_K=128):
    """
    X: [K, N] float32
    P: [M, K] uint8 mask for +1
    N: [M, K] uint8 mask for -1
    returns Y: [M, N] float32
    """
    M, K = P.shape
    K2, N2 = X.shape
    assert K == K2
    Y = torch.empty((M, N2), device=X.device, dtype=torch.float32)
    grid = (triton.cdiv(M, BLOCK_M), triton.cdiv(N2, BLOCK_N))
    ternary_matmul_mm_kernel[grid](
        X, P, N, Y,
        M, N2, K,
        X.stride(0), X.stride(1),
        P.stride(0), P.stride(1),
        N.stride(0), N.stride(1),
        Y.stride(0), Y.stride(1),
        BLOCK_M=BLOCK_M, BLOCK_N=BLOCK_N, BLOCK_K=BLOCK_K
    )
    return Y

# ——— Benchmark 脚本 ———
device = "cuda"
M, K, N = 1024, 2048, 1024
W = torch.randint(-1, 2, (M, K), device=device, dtype=torch.int8)
X = torch.randn((K, N), device=device)

P_mask = (W == 1).to(torch.uint8)
N_mask = (W == -1).to(torch.uint8)

# Warmup
_ = torch.mm(W.float(), X)
_ = ternary_matmul_mm_triton(X, P_mask, N_mask)

def timer(fn, *args, repeat=50):
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    for _ in range(repeat):
        _ = fn(*args)
    torch.cuda.synchronize()
    t1 = time.perf_counter()
    return t1 - t0

t_torch = timer(lambda A, B: torch.mm(A, B), W.float(), X)
t_triton = timer(ternary_matmul_mm_triton, X, P_mask, N_mask)

print(f"Torch  dense  mm: {t_torch:.4f}s")
print(f"Triton ternary mm: {t_triton:.4f}s")
