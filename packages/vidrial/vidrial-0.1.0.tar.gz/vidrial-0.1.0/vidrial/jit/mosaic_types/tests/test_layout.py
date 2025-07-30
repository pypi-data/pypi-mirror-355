from vidrial.jit.mosaic_types import Shape, Stride, Layout, UniversalCopy, CopyAtom, CudaDType, Int, compact_major, _32, _64, _128, _256, _8

def test_basic_shapes():
    simple_shape = Shape(_32, _32)
    assert simple_shape.to_cpp() == "Shape<Int<32>, Int<32>>"

def test_nested_shapes():
    nested_shape = Shape(Shape(_32, _32), _64)
    assert nested_shape.to_cpp() == "Shape<Shape<Int<32>, Int<32>>, Int<64>>"

def test_complex_nested_shapes():
    complex_shape = Shape(Shape(_32, Shape(_64, _128)), Shape(_256, _32))
    assert complex_shape.to_cpp() == "Shape<Shape<Int<32>, Shape<Int<64>, Int<128>>>, Shape<Int<256>, Int<32>>>"

def test_basic_layouts():
    simple_shape = Shape(_32, _32)
    simple_layout = Layout(simple_shape)
    assert simple_layout.to_cpp() == "Layout<Shape<Int<32>, Int<32>>, Stride<Int<1>, Int<32>>>"

def test_right_layout():
    simple_shape = Shape(_32, _32)
    simple_layout = Layout(simple_shape, compact_major(simple_shape, left=False))
    assert simple_layout.to_cpp() == "Layout<Shape<Int<32>, Int<32>>, Stride<Int<32>, Int<1>>>"

def test_layouts_with_strides():
    simple_shape = Shape(_32, _32)
    custom_stride = Stride(_64, _32)
    layout_with_stride = Layout(simple_shape, custom_stride)
    assert layout_with_stride.to_cpp() == "Layout<Shape<Int<32>, Int<32>>, Stride<Int<64>, Int<32>>>"

def test_nested_layouts():
    simple_shape = Shape(_32, _32)
    nested_layout = Layout(Shape(simple_shape, _64))
    assert nested_layout.to_cpp() == "Layout<Shape<Shape<Int<32>, Int<32>>, Int<64>>, Stride<Stride<Int<1>, Int<32>>, Int<1024>>>"

def test_basic_traits():
    float_trait = UniversalCopy(CudaDType.FLOAT)
    assert float_trait.to_cpp() == "UniversalCopy<float>"

def test_copy_atoms():
    float_trait = UniversalCopy(CudaDType.FLOAT)
    float_copy_atom = CopyAtom(float_trait)
    assert float_copy_atom.to_cpp() == "Copy_Atom<UniversalCopy<float>, float>"

def test_complex_structure():
    complex_structure = Layout(
        Shape(
            Shape(_32, _64),
            Shape(_128, _256)
        ),
        Stride(
            _32,
            Stride(_64, _128)
        )
    )
    assert complex_structure.to_cpp() == "Layout<Shape<Shape<Int<32>, Int<64>>, Shape<Int<128>, Int<256>>>, Stride<Int<32>, Stride<Int<64>, Int<128>>>>"

def test_complex_trait_structure():
    complex_trait_structure = CopyAtom(
        UniversalCopy(CudaDType.UINT8)
    )
    assert complex_trait_structure.to_cpp() == "Copy_Atom<UniversalCopy<uint8_t>, uint8_t>"


def test_compact_major():
    shape = Shape(_32, _32)
    stride_left = compact_major(shape)
    assert stride_left.to_cpp() == "Stride<Int<1>, Int<32>>"
    stride_right = compact_major(shape, left=False)
    assert stride_right.to_cpp() == "Stride<Int<32>, Int<1>>"
    shape1 = Shape(Shape(Shape(_8, _8), Int(3)), _8)
    layout_left = Layout(shape1)
    assert layout_left.to_cpp() == "Layout<Shape<Shape<Shape<Int<8>, Int<8>>, Int<3>>, Int<8>>, Stride<Stride<Stride<Int<1>, Int<8>>, Int<64>>, Int<192>>>"