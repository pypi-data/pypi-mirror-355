import warp
import numpy as np

TILE_SIZE = 128


@warp.kernel
def kernel(
    a: warp.array(dtype=int),
    b: warp.array(dtype=float),
):
    data = warp.tile_load(a, TILE_SIZE)
    data0 = warp.untile(data)
    data1 = warp.where(data0, 1., 0.)
    data2 = warp.tile(data1)
    warp.tile_store(b, data2)


data_a = warp.array(np.random.rand(TILE_SIZE) < 0.3, dtype=int)
data_b = warp.array(np.zeros(TILE_SIZE), dtype=float)

warp.launch_tiled(kernel, dim=[1], inputs=[data_a, data_b], block_dim=128)

print(data_a.numpy())
print(data_b.numpy())
