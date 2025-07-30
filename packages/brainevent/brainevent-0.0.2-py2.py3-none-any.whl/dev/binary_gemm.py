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
import torch
import triton
import triton.language as tl

# -----------------------------------------------------------------------------
# Triton Kernel: 二值 A（打包后 uint8）× 浮点 B → float C
# -----------------------------------------------------------------------------
@triton.jit
def binary_gemm_kernel(
    A_ptr, B_ptr, C_ptr,
    M, N, K,
    stride_am, stride_ak,            # A packing: row-major: (M, K/8)
    stride_bk, stride_bn,
    stride_cm, stride_cn,
    BLOCK_M: tl.constexpr, BLOCK_N: tl.constexpr, BLOCK_K: tl.constexpr
):
    pid_m = tl.program_id(0)  # blocks in M
    pid_n = tl.program_id(1)  # blocks in N

    # 计算这个 block 的起始位置
    offs_m = pid_m * BLOCK_M + tl.arange(0, BLOCK_M)
    offs_n = pid_n * BLOCK_N + tl.arange(0, BLOCK_N)
    acc = tl.zeros((BLOCK_M, BLOCK_N), dtype=tl.float32)

    # 对 k 维度分块
    for k0 in range(0, K // 8, BLOCK_K):
        # 每个子块：
        # 加载 A_packed: shape [BLOCK_M, BLOCK_K]
        A_block = tl.load(
            A_ptr + (offs_m[:, None] * stride_am + (k0 + tl.arange(0, BLOCK_K)) * stride_ak),
            mask=(offs_m[:, None] < M),
        )  # uint8

        # 加载 B: shape [BLOCK_K*8, BLOCK_N]
        # 先展开到 byte，再加载 float
        # 每个 uint8 包含 8 bits，所以要拉 8 倍到浮点
        # 这里简化：先 unpackbits 到 8×BLOCK_K，再乘以 B 瓦片
        B_block = tl.load(
            B_ptr + ((k0*8 + tl.arange(0, BLOCK_K*8))[:, None] * stride_bk
                     + offs_n[None, :] * stride_bn),
            mask=(offs_n[None, :] < N),
        )  # float32

        # 将 A_block unpack 到 {0,1} float
        # tl.unpack_bits 需要 Triton >=2.1；若版本较低，用 tl.arange 提取
        bits = tl.unpack_bits(A_block, bit_width=8, signed=False)  # (BLOCK_M, BLOCK_K*8)
        # 映射 {0,1} → {-1,+1}
        bits = bits * 2.0 - 1.0  # float32

        # 计算局部点积
        acc += tl.dot(bits, B_block)

    # 写回 C
    C = acc.to(tl.float32)
    tl.store(
        C_ptr + (offs_m[:, None] * stride_cm + offs_n[None, :] * stride_cn),
        C,
        mask=(offs_m[:, None] < M) & (offs_n[None, :] < N)
    )


# -----------------------------------------------------------------------------
# 驱动代码：打包、调用、验证
# -----------------------------------------------------------------------------
def binary_gemm_triton(A, B, BLOCK_M=64, BLOCK_N=64, BLOCK_K=16):
    """
    A: torch.Tensor, shape [M,K], dtype=torch.int8, values in {-1,+1}
    B: torch.Tensor, shape [K,N], dtype=torch.float32
    """
    M, K = A.shape
    K, N = B.shape
    assert K % 8 == 0, "K must be multiple of 8"

    # 1. CPU 上打包 A: map {-1,+1} → {0,1}, packbits
    A01 = ((A >= 0).to(torch.uint8))
    A_packed = torch.packbits(A01, dim=1)  # shape [M, K/8], uint8

    # 2. 分配输出
    C = torch.empty((M, N), device='cuda', dtype=torch.float32)

    # 3. 调用 Triton 内核
    grid = (triton.cdiv(M, BLOCK_M), triton.cdiv(N, BLOCK_N))
    binary_gemm_kernel[grid](
        A_packed, B, C,
        M, N, K,
        # strides for A_packed
        A_packed.stride(0), A_packed.stride(1),
        # strides for B
        B.stride(0), B.stride(1),
        # strides for C
        C.stride(0), C.stride(1),
        BLOCK_M=BLOCK_M, BLOCK_N=BLOCK_N, BLOCK_K=BLOCK_K
    )
    return C

# -----------------------------------------------------------------------------
# 运行示例
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    torch.manual_seed(0)
    M, K, N = 256, 256, 256
    # 随机生成 A ∈ {-1,+1}, B ∈ float32
    A = torch.randint(0, 2, (M, K), device='cpu', dtype=torch.int8) * 2 - 1
    B = torch.randn((K, N), device='cuda').float()

    # Triton 版本
    C_triton = binary_gemm_triton(A, B)
    # PyTorch 参考
    A_f = A.to(torch.float32)
    C_ref = torch.matmul(A_f, B)

    # 验证最大误差
    max_err = (C_triton - C_ref).abs().max().item()
    print(f"Max error: {max_err:.6f}")
