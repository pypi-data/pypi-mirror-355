from math import comb, factorial
import torch as th

def problem_dimensions(Z_shape, X_shape, power, d_tile=1):
    assert Z_shape == op_output_shape(X_shape, power, d_tile)
    bs, d = X_shape[:-1], X_shape[-1]
    assert d % d_tile == 0, f"d={d} must be divisible by d_tile={d_tile}"
    D = sympow_dim(d, power, d_tile)
    return bs, d, D

def sympow_dim(d, power, d_tile=1):
    if d_tile == 1:
        return comb(d + power - 1, power)
    return sympow_dim(d // d_tile, power) * d_tile**power

def op_output_shape(x_shape, power, d_tile=1):
    batch_dims, d = tuple(x_shape[:-1]), x_shape[-1]
    assert d % d_tile == 0, f"d={d} must be divisible by d_tile={d_tile}"
    d_tile_num = sympow_dim(d // d_tile, power)
    return th.Size(batch_dims + (d_tile_num,) + (d_tile,) * power)
   
def interface_output_shape(X_shape, power, d_tile=1, dim=-1):
    Z_shape = list(X_shape)
    Z_shape[dim] = sympow_dim(X_shape[dim], power, d_tile)
    return th.Size(Z_shape)

sympow_shape = interface_output_shape
sympow_op_shape = op_output_shape

def canonical_arguments(X):
    if len(X.shape) == 1: X = X.unsqueeze(0)
    assert len(X.shape) == 2, f"X_shape={X.shape} must be 2D. Generic batch dims not implemented yet"
    return X

class SympowCoords:
    def __init__(self, n, power):
        assert n >= 1 and power >= 1, f"n={n} and power={power} must be >= 1"
        self.n, self.power = n, power
        self.seq, self.idx = [0] * power, 0
        self.final = False
        
    def duplicate_count(self):
        hist = [0]*self.n
        for i in self.seq:
            hist[i] += 1
        count = factorial(self.power)
        for h in hist:
            count //= factorial(h)
        return count
        
    def increment(self, position):
        assert position >= 0 and position < self.power, f"position={position} must be >= 0 and < power={self.power}"
        if self.seq[position] < self.n-1:
            self.idx += 1
            self.seq[position:] = [self.seq[position]+1] * (self.power-position)
            return
        if position == 0:
            self.final = True
            return
        self.increment(position-1)
        
    def __iter__(self): return self
    
    def __next__(self):
        if self.final: raise StopIteration
        result = (self.idx, self.seq.copy(), self.duplicate_count())
        self.increment(self.power-1)
        return result
        
    def __len__(self):
        return sympow_dim(self.n, self.power)

