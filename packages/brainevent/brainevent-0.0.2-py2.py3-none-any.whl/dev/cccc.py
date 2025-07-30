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

def csr_spmm_symbolic(a_indptr, a_indices, b_indptr, b_indices):
    """
    Symbolic phase on CPU: computes c_indptr for C = A*B in CSR format.
    """
    N = a_indptr.numel() - 1
    c_indptr = torch.zeros_like(a_indptr)
    ptr = 0
    for i in range(N):
        row_cols = set()
        for idx in range(a_indptr[i].item(), a_indptr[i+1].item()):
            a_j = a_indices[idx].item()
            # walk B row a_j
            for k in range(b_indptr[a_j].item(), b_indptr[a_j+1].item()):
                b_col = b_indices[k].item()
                row_cols.add(b_col)
        nnz = len(row_cols)
        ptr += nnz
        c_indptr[i+1] = ptr
    return c_indptr

@triton.jit
def csr_spmm_numeric(
    a_indptr,    # [N+1]
    a_indices,   # [nnzA]
    a_data,      # [nnzA]
    b_indptr,    # [M+1]
    b_indices,   # [nnzB]
    b_data,      # [nnzB]
    c_indptr,    # [N+1]
    c_indices,   # [nnzC]
    c_data,      # [nnzC]
    N, M,        # dimensions
    **meta
):
    """
    Numeric phase on GPU: multi‐program, one row per program.
    """
    row = tl.program_id(0)
    # pointers into A
    a_start = a_indptr[row]
    a_end   = a_indptr[row + 1]
    # pointers into C
    c_start = c_indptr[row]
    # We'll scatter into c_indices[c_start + p] and c_data[c_start + p]
    offset = 0
    # local hash map in registers: for simplicity, linear search
    # (for large rows you'd want a shared‐memory hash or sort+reduce)
    col_list = tl.zeros([1024], tl.int32)      # assume max nnz per row ≤1024
    val_list = tl.zeros([1024], tl.float32)
    for ai in range(a_start, a_end):
        j = a_indices[ai]       # column in A, i.e. row in B
        a_val = a_data[ai]
        # walk B[j, :]
        bj_start = b_indptr[j]
        bj_end   = b_indptr[j + 1]
        for bi in range(bj_start, bj_end):
            col = b_indices[bi]
            prod = a_val * b_data[bi]
            # accumulate into local lists
            found = 0
            for p in range(offset):
                if col_list[p] == col:
                    val_list[p] += prod
                    found = 1
                    break
            if not found:
                col_list[offset] = col
                val_list[offset]  = prod
                offset += 1
    # write back
    for p in range(offset):
        c_indices[c_start + p] = col_list[p]
        c_data   [c_start + p] = val_list [p]

def csr_spmm_triton(A, B):
    """
    Multiply two CSR matrices A, B (as PyTorch sparse CSR tensors)
    and return C in CSR via Triton.
    """
    # extract CSR components
    a_indptr, a_indices, a_data = A.crow_indices(), A.col_indices(), A.values()
    b_indptr, b_indices, b_data = B.crow_indices(), B.col_indices(), B.values()
    # Symbolic phase
    c_indptr = csr_spmm_symbolic(a_indptr, a_indices, b_indptr, b_indices)
    nnzC = c_indptr[-1].item()
    # allocate output arrays
    c_indices = torch.empty([nnzC], dtype=a_indices.dtype, device=a_indices.device)
    c_data    = torch.empty([nnzC], dtype=a_data.dtype,    device=a_data.device)
    # launch Triton kernel: N programs, one per row
    N, M = A.size(0), B.size(1)
    grid = (N, )
    csr_spmm_numeric[grid](
        a_indptr, a_indices, a_data,
        b_indptr, b_indices, b_data,
        c_indptr, c_indices, c_data,
        N, M
    )
    # wrap back into a PyTorch CSR tensor
    return torch.sparse_csr_tensor(c_indptr, c_indices, c_data, size=(N, M))

# Example usage
if __name__ == '__main__':
    # create two random sparse CSR matrices
    A = torch.randn(128, 256)
    A[A.abs() < 0.95] = 0.0
    A = A.to_sparse_csr()
    B = torch.randn(256, 64)
    B[B.abs() < 0.95] = 0.0
    B = B.to_sparse_csr()


    C = csr_spmm_triton(A, B)
    # verify against PyTorch dense matmul
    diff = (C.to_dense() - A.to_dense() @ B.to_dense()).abs().max()
    print(f"Max error = {diff:.6e}")
