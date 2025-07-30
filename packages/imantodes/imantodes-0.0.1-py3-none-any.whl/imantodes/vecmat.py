"""
imantodes: light-weight python code for interactive scivis
Copyright © 2025. University of Chicago
SPDX-License-Identifier: LGPL-3.0-only

vecmat.py: Simple classes,ops for {2,3}D vectors,matrices with{out,} homog. coords
Follows https://peps.python.org/pep-0465/ in using '@' for matrix/matrix and
matrix/vector multiplication; '*' is just for multiplication with a scalar
"""
# some guidance for pylint
# - accept single-letter variables names,
# - prevent false positives flagging "-self.x"
# - allow clunky-but-functional if True/if False tests at end
# - don't try to infer what is and isn't subscriptable
# pylint: disable=invalid-name, invalid-unary-operand-type, using-constant-test, unsubscriptable-object

# This code started by copying http://pythonfiddle.com/vector-class-python/
# and https://stackoverflow.com/q/15774804 but then went its own way.
# In two places (noted) ChatGPT proved useful.


import math as _math
import collections.abc as _abc
import argparse as _argparse
import cffi as _cffi

_ffi = _cffi.FFI()


def _isnum(v):
    """Utility for testing if v is numeric"""
    return isinstance(v, (int, float))


def _isnan(v):
    """Utility for testing if v is NaN"""
    return _isnum(v) and _math.isnan(v)


class _Cptr:
    """make a CFFI array or pointer behave more like a Python list"""

    # Note: this class is based on code from ChatGPT, which dubiously claims that
    # this is all based on info at https://cffi.readthedocs.io/en/latest/

    def __init__(self, cptr, length):
        # cptr: CFFI array or pointer to array
        self.ptr = cptr
        if len(cptr) != length:
            # may want to disable this if we ever routinely need to create
            # a Vec or Mat around a *subset* of a C array, but currently for
            # this need we can use the limited (explicit start and stop) slice
            # support that CFFI arrays do have
            raise ValueError(f'CFFI {len(cptr)=} but asking for {length=}')
        self.length = length

    def __getitem__(self, index):
        # Support for single index or slice
        if isinstance(index, slice):
            # Handle slicing
            start, stop, step = index.indices(self.length)
            return [self.ptr[i] for i in range(start, stop, step)]
        if isinstance(index, int):
            # Handle single element access
            if not 0 <= index < self.length:
                raise IndexError(f'Array {index=} out of range [0, {self.length-1}]')
            return self.ptr[index]
        raise IndexError(f'Array {index=} not understood')

    def __setitem__(self, index, value):
        # Support for single index or slice assignment
        if isinstance(index, slice):
            start, stop, step = index.indices(self.length)
            if len(range(start, stop, step)) != len(value):
                raise ValueError('Length of values does not match length of slice')
            for i, v in zip(range(start, stop, step), value):
                self.ptr[i] = v
        elif isinstance(index, int):
            if not 0 <= index < self.length:
                raise IndexError(f'Array {index=} out of range [0, {self.length-1}]')
            self.ptr[index] = value
        else:
            raise IndexError(f'Array {index=} not understood')

    def __len__(self):
        # Length of the array
        return self.length

    def __repr__(self):
        # Representation of the array
        return repr([self.ptr[i] for i in range(self.length)])

    def __iter__(self):
        # Allow iteration over the array
        for i in range(self.length):
            yield self.ptr[i]


class _Base:
    """Captures things that are common between Vec and Mat and general over dimension;
    mainly initialization of, and operations on, the .val list of values"""

    def __init__(self, length, dim=0):
        """Bare-bones initializer, taking init args for value length and space dimension."""
        # Note that the various Vec and Mat subclasses have very different ways of interpreting
        # the __init__ args, but we give dim a default value above only so that pylint does not
        # get confused and think a constructor call is missing the dim argument
        self.tname = type(self).__name__
        self.val = None  # values stored
        self.L = length  # length, or number of values stored
        self.D = dim     # dimension we believe ourselves to be in
        # real init happens in init(), next

    def init(self, *args):
        """More useful initializer. Returns False if the subclass __init__ needs to do
        more work to interpret *args in a way specific to that subclass type. The
        _Base.__init__ above would itself take the extra *args and also handle more
        initialization situations, but that's precluded by __init__s unable to return
        any value."""
        if len(args) == 1 and isinstance(args[0], _ffi.CData):
            # wrapping a C array
            self.val = _Cptr(args[0], self.L)
            return True
        # else not wrapping a C array, so initialize value list to all NaNs
        self.val = [_math.nan] * self.L
        ret = True   # meaning init() is done and caller needs to do no further init work
        if not args:
            # caller okay with NaN initialization
            return True
        # else have some args to interpret
        # some flags to help with (too?) clever initialization logic
        vec2 = self.D == 2 and self.L == 2
        vec3 = self.D == 3 and self.L == 3
        mat3 = self.D == 3 and self.L == 9
        mat4 = self.D == 4 and self.L == 16
        if len(args) == 1:
            a0 = args[0]
            if _isnan(a0):
                # caller wants to keep the NaNs already there
                pass
            elif a0 == 0.0:
                # caller wants all 0 values
                self.val[:] = [0.0] * self.L
            elif isinstance(a0, str):
                # was given string, we try to parse space and/or comma separated values
                # along with [] or () or {} for separating rows in case of matrix (L != D)
                # NOTE: no effort made to parse structure from whatever [],(),{} delimit
                trs = (',', ' ') if self.L == self.D else (',[](){}', '       ')
                val = a0.translate(str.maketrans(*trs)).split()
                if mat3 and len(val) == 6:
                    # sneaky hack: 3x3 affine matrix but only 6 values in string
                    val += ['0', '0', '1']
                elif mat4 and len(val) == 12:
                    # sneaky hack: 4x4 affine matrix but only 12 values in string
                    val += ['0', '0', '0', '1']
                if self.L != len(val):
                    raise RuntimeError(
                        f'From {self.tname} init arg string "{a0}", '
                        f'parsed {len(val)} not {self.L} values'
                    )
                self.val[:] = map(float, val)
            elif isinstance(a0, type(self)):
                # we got an instance of our own type
                self.val[:] = a0[:]
            elif isinstance(a0, _abc.Iterable):
                # catches list or tuple (of anything that can be passed through float()),
                # or one of our own type, but *not* CFFI C array
                if mat3 and len(a0) == 6:
                    # sneaky hack: 3x3 affine matrix but only 6 values were in iterable
                    self.val[0:6] = map(float, a0)
                    self.val[6:9] = [0.0, 0.0, 1.0]
                elif mat4 and len(a0) == 12:
                    # sneaky hack: 4x4 affine matrix but only 12 values were in iterable
                    self.val[0:12] = map(float, a0)
                    self.val[13:16] = [0.0, 0.0, 0.0, 1.0]
                elif vec2 and len(a0) == 3:
                    # sneaky hack: want a vec2 but got 3, will handle in Vec2.__init__ (HOMOG3)
                    ret = False
                elif vec3 and len(a0) == 4:
                    # sneaky hack: want a vec3 but got 4, will handle in Vec3.__init__ (HOMOG4)
                    ret = False
                elif self.L == len(a0):
                    self.val[:] = map(float, a0)
                else:
                    raise RuntimeError(
                        f'{self.tname} init arg Iterable {a0} has {len(a0)} values; '
                        f'expected {self.L}'
                    )
            else:
                # we didn't know how to handle single arg; not done
                ret = False
        elif mat3 and len(args) == 6 and all(map(_isnum, args)):
            # sneaky hack: 3x3 affine matrix and only 6 args were passed
            self.val[0:6] = map(float, args)
            self.val[6:9] = [0.0, 0.0, 1.0]
        elif mat4 and len(args) == 12 and all(map(_isnum, args)):
            # sneaky hack: 4x4 affine matrix and only 12 args were passed
            self.val[0:12] = map(float, args)
            self.val[12:16] = [0.0, 0.0, 0.0, 1.0]
        elif len(args) == self.L:
            # got one arg per value, set them all
            if not all(map(_isnum, args)):
                raise RuntimeError(
                    f'Expected all {self.L} {self.tname} init args to be numeric but got {args})'
                )
            self.val[:] = map(float, args)
        else:
            ret = False   # init not done
        return ret

    def __repr__(self):
        return f'{self.tname}(' + ', '.join(map(str, self.val)) + ')'

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.val[:] == other.val[:]

    def __iter__(self):
        for idx in range(self.L):
            yield self[idx]

    def __len__(self):
        # but does this iteration actually make sense for matrices?
        """Alas, not mathematically useful: just the number of components,
        as apparently needed for making something iterable. Use abs()
        to get vector Euclidean length or matrix Frobenius norm"""
        return self.L

    def __neg__(self):
        """Unary negation"""
        return type(self)(list(map(lambda x: -x, self.val)))

    def __pos__(self):
        """Surprise! Unary positive is shorthand for deepcopy"""
        return type(self)(self.val[:])

    def __add__(self, other):
        if not isinstance(other, type(self)):
            raise self.op_except('+', other)
        # map add over both self and other value arrays
        return type(self)(list(map(lambda sv, ov: sv + ov, self.val, other.val)))

    def __iadd__(self, other):
        if not isinstance(other, type(self)):
            raise self.op_except('+=', other)
        if self is other:
            raise self.self_except('+=')
        for idx in range(self.L):
            self.val[idx] += other.val[idx]
        return self

    def __sub__(self, other):
        if not isinstance(other, type(self)):
            raise self.op_except('-', other)
        # map subtract over both self and other value arrays
        return type(self)(list(map(lambda sv, ov: sv - ov, self.val, other.val)))

    def __isub__(self, other):
        if not isinstance(other, type(self)):
            raise self.op_except('-=', other)
        if self is other:
            raise self.self_except('-=')
        # print(f'{self.tname}.__isub__: {self.val=}   -=   {other.val=}')
        for idx in range(self.L):
            self.val[idx] -= other.val[idx]
        # print(f'{self.tname}.__isub__:    ---> {self.val=}')
        return self

    def __mul__(self, other):
        """Scalar right multiplication"""
        if not _isnum(other):
            raise self.op_except('*', other)
        # else interpreting other as scalar to multiply with
        return (type(self))(list(map(lambda v: v * other, self.val)))

    def __imul__(self, other):
        if not _isnum(other):
            raise self.op_except('*=', other)
        # (not possible: self is other)
        for idx in range(self.L):
            self.val[idx] *= other
        return self

    def __rmul__(self, other):
        """Scalar left multiplication"""
        if not _isnum(other):
            raise self.op_except('*', other, False)
        return self * other

    def __truediv__(self, other):
        """Dividing by a scalar"""
        if not _isnum(other):
            raise self.op_except('/', other)
        return type(self)(list(map(lambda x: x / other, self.val)))

    def __itruediv__(self, other):
        """Division (by a scalar) assignment"""
        if not _isnum(other):
            raise self.op_except('/=', other)
        # (not possible: self is other)
        for idx in range(self.L):
            self.val[idx] /= other
        return self

    def __abs__(self):
        """(FIXED LATER) Euclidean vector length or Frobenius matrix norm"""
        # see how .__abs__.__doc__ is set later
        return _math.sqrt(sum(map(lambda v: v**2, self.val)))

    def op_except(self, op: str, other, right=True):
        """Utility for making descriptive exception about operand types"""
        wut = {
            '*': 'factor',  # (multi-line please)
            '@': 'factor',
            '+': 'term',
            '-': 'operand',
            '/': 'divisor',
        }[
            op[0]  # so += and + treated same
        ]
        side = 'right' if right else 'left'
        parts = [self.tname, f'({other}: {type(other)})']
        lside = parts[1 - int(right)]
        rside = parts[int(right)]
        return TypeError(f'Confusing {side}-side {wut} in: {lside} {op} {rside}')

    def self_except(self, op: str):
        """Utility for making descriptive exception about 'self is other'"""
        return ValueError(
            f'Will not {self.tname}{op}{self.tname} with 2 references to same thing '
            '(use unary + to create deep copies)'
        )

    def args_except(self, *args):
        """Utility for making descriptive exception about bad init args"""
        return ValueError(f'Cannot understand {self.tname} init args: {args}')


class _Vec(_Base):
    """Common things for Vec of any dimension"""

    def __getitem__(self, index):
        return self.val[index]

    def __setitem__(self, index, v):
        self.val[index] = v

    def __str__(self):
        return ' '.join(map(str, self.val))

    def __matmul__(self, other):
        """Dot product of two vectors"""
        if not isinstance(other, type(self)):
            raise self.op_except('@', other)
        # else other is also a vector: interpret as a dot product
        return sum(map(lambda sv, ov: sv * ov, self.val, other.val))

    @property
    def x(self):
        """Get x (1st) coordinate"""
        return self.val[0]

    @x.setter
    def x(self, v):
        self.val[0] = float(v)

    @property
    def y(self):
        """Get y (2nd) coordinate"""
        return self.val[1]

    @y.setter
    def y(self, v):
        self.val[1] = float(v)


class _Mat(_Base):
    """Common things for Mat of any dimension"""

    def __getattr__(self, key):
        """Concise/cute way to get transpose (copied from NumPy)"""
        if key == 'T':
            return self.transpose()
        raise AttributeError(f'{self.tname} has no attribute "{key}"')

    def cols(self):
        """Return list of columns (each as Vec)"""
        return self.T.rows()

    def _index2int(self, index):
        """utility to check that 2-tuple index is as we expect"""
        if len(index) != 2:
            raise IndexError(f'{self.tname} tuple {index=} length {len(index)} not 2')
        ridx, cidx = index
        if not (isinstance(ridx, int) and isinstance(cidx, int)):
            raise IndexError(
                f'{self.tname}: Sorry currently need 2 ints in tuple index, not {index}'
            )
        if not 1 <= ridx <= self.D:
            raise IndexError(f'{self.tname} row index {ridx=} out of range [1,{self.D}]')
        if not 1 <= cidx <= self.D:
            raise IndexError(f'{self.tname} col index {cidx=} out of range [1,{self.D}]')
        return (ridx, cidx)

    # (GLK: slice support info at e.g. https://stackoverflow.com/q/2936863 )
    def __getitem__(self, index):
        if isinstance(index, slice):
            start, stop, step = index.indices(self.L)
            return [self.val[i] for i in range(start, stop, step)]
        if isinstance(index, int):
            if not 0 <= index < self.L:
                raise IndexError(f'{self.tname} {index=} out of range [0,{self.L-1}]')
            return self.val[index]
        if isinstance(index, tuple):
            ridx, cidx = self._index2int(index)
            return self.val[(cidx - 1) + self.D * (ridx - 1)]
        raise IndexError(f'{self.tname} {index=} not understood')

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            start, stop, step = index.indices(self.L)
            rng = range(start, stop, step)
            if len(rng) != len(value):
                raise ValueError(
                    f'{self.tname}: {value=} len {len(value)} != slice len {len(rng)}'
                )
            for i, v in zip(rng, value):
                self.val[i] = float(v)
        elif isinstance(index, int):
            if not 0 <= index < self.L:
                raise IndexError(f'{self.tname} {index=} out of range [0,{self.L-1}]')
            self.val[index] = float(value)
        elif isinstance(index, tuple):
            ridx, cidx = self._index2int(index)
            self.val[(cidx - 1) + self.D * (ridx - 1)] = float(value)
        else:
            raise IndexError(f'Array {index=} not understood')


# fixing a per-subclass docstring; h/t https://stackoverflow.com/a/78428736
_Vec.__abs__.__doc__ = 'Euclidean vector length'
_Mat.__abs__.__doc__ = 'Frobenius matrix norm'


class Vec2(_Vec):
    """Minimal 2-vector class"""

    def __init__(self, *args):
        super().__init__(2, 2)
        if super().init(*args):
            return
        # else do more work to interpret *args for initialization
        match args[0]:
            case Vec3():
                # got a Vec3 but creating a Vec2; assume homogenous coordinates (HOMOG3)
                v3 = args[0]
                if v3.z:
                    # it's a position
                    self.val[:] = [v3.x / v3.z, v3.y / v3.z]
                else:
                    self.val[:] = [v3.x, v3.y]
            case _:
                # we don't accept a more general length-3 iterable because that's too permissive;
                # should confine the homog. coord. cleverness above to explicit Vec3s
                raise self.args_except(args)

    def cross(self, other):
        """scalar-valued \"cross product\" """
        return self.x * other.y - other.x * self.y


class Vec3(_Vec):
    """Minimal 3-vector class"""

    def __init__(self, *args):
        super().__init__(3, 3)
        if super().init(*args):
            return
        # else do more work to interpret *args for initialization
        x = args[0]
        y = args[1] if len(args) >= 2 else None
        z = args[2] if len(args) >= 3 else None
        match x:
            case Vec2():
                if not _isnum(y):
                    raise ValueError(
                        f'After {x.tname}, need 2nd {self.tname} init arg '
                        f'to be number (not {type(y)})'
                    )
                if not z is None:
                    raise ValueError(f'Was not expecting 3rd {self.tname} init arg {z})')
                self.val[:] = [x[0], x[1], float(y)]
            case Vec4():
                # got a Vec4 but creating a Vec3; assume homogenous coordinates (HOMOG4)
                v4 = args[0]
                if v4.w:
                    # it's a position
                    self.val[:] = [v4.x / v4.w, v4.y / v4.w, v4.z / v4.w]
                else:
                    self.val[:] = [v4.x, v4.y, v4.z]
            case _:
                raise self.args_except(args)

    def cross(self, other):
        """Cross product"""
        return Vec3(
            self.y * other.z - other.y * self.z,
            other.x * self.z - self.x * other.z,
            self.x * other.y - other.x * self.y,
        )

    @property
    def z(self):
        """Get z (3rd) coordinate"""
        return self.val[2]

    @z.setter
    def z(self, v):
        self.val[2] = float(v)


class Vec4(_Vec):
    """Minimal 4-vector class"""

    def __init__(self, *args):
        super().__init__(4, 4)
        if super().init(*args):
            return
        # else do more work to interpret *args for initialization
        x = args[0]
        y = args[1] if len(args) >= 2 else None
        z = args[2] if len(args) >= 3 else None
        match x:
            case Vec3():
                if not _isnum(y):
                    raise ValueError(
                        f'After {x.tname}, need 2nd {self.tname} init arg '
                        f'to be number (not {type(y)})'
                    )
                if not z is None:
                    raise ValueError(f'Was not expecting 3rd {self.tname} init arg {z})')
                self.val[:] = [x[0], x[1], x[2], float(y)]
            case _:
                raise self.args_except(args)

    @property
    def z(self):
        """Get z (3rd) coordinate"""
        return self.val[2]

    @z.setter
    def z(self, v):
        self.val[2] = float(v)

    @property
    def w(self):
        """Get w (4th) coordinate"""
        return self.val[3]

    @w.setter
    def w(self, v):
        self.val[3] = float(v)


class Mat2(_Mat):
    """Minimal 2x2 matrix class. Is not clever about affine matrices"""

    # values in matrix are:
    #   a=0=11  b=1=12
    #   c=2=21  d=3=22

    def __init__(self, *args):
        super().__init__(4, 2)
        if super().init(*args):
            return
        # else do more work to interpret *args for initialization
        a = args[0]
        b = args[1] if len(args) > 1 else None
        match a:
            case _ if a == 1.0 and len(args) == 1:
                # asking for identity matrix
                self.val[:] = map(float, [1, 0, 0, 1])
            case Vec2():
                if not isinstance(b, Vec2):
                    raise RuntimeError(
                        f'Need 2 Vec2s (1 per row) {self.tname} init args, not {b}: {type(b)}'
                    )
                self.val[0:2] = a[:]
                self.val[2:4] = b[:]
            case _:
                raise self.args_except(args)

    def __str__(self):
        srows = [
            ', '.join(map(str, self.val[0:2])),
            ', '.join(map(str, self.val[2:4])),
        ]
        sall = ', '.join([f'[{sr}]' for sr in srows])
        return f'[{sall}]'

    def rows(self):
        """Return list of rows (each as Vec2)"""
        return [Vec2(self.val[0:2]), Vec2(self.val[2:4])]

    def transpose(self):
        """Return matrix transpose"""
        v = self.val
        return Mat2(v[0], v[2], v[1], v[3])

    def det(self):
        """Return matrix determinant"""
        [a, b, c, d] = self.val[:]
        return a * d - b * c

    def inv(self):
        """Matrix inverse"""
        return Mat2(self.val[3], -self.val[1], -self.val[2], self.val[0]) / self.det()

    def __matmul__(self, other):
        """Matrix-matrix, matrix-vector, matrix-scalar multiplication"""
        if isinstance(other, type(self)):
            # other is also a Mat2 interpret as matrix-matrix mul A B
            [r1A, r2A] = self.rows()
            [c1B, c2B] = other.cols()
            return Mat2(r1A @ c1B, r1A @ c2B, r2A @ c1B, r2A @ c2B)
        if isinstance(other, Vec2):
            # other is a Vec2: interpret as matrix-vector mul A V
            [r1, r2] = self.rows()
            return Vec2(r1 @ other, r2 @ other)
        # else confused
        raise self.op_except('@', other)


class Mat3(_Mat):
    """Minimal 3x3 matrix class. Tries to be slightly more clever
    (currently, just .inv() and @/__matmul__) if affine."""

    # values in matrix are:
    #   a=0=11  b=1=12  c=2=13
    #   d=3=21  e=4=22  f=5=23
    #   g=6=31  h=7=32  i=8=33

    def __init__(self, *args):
        super().__init__(9, 3)
        if super().init(*args):
            return
        # else do more work to interpret *args for initialization
        a = args[0]
        b = args[1] if len(args) > 1 else None
        c = args[2] if len(args) > 2 else None
        match a:
            case _ if a == 1.0 and len(args) == 1:
                # asking for identity matrix
                self.val[0:9] = map(float, [1, 0, 0, 0, 1, 0, 0, 0, 1])
            case Vec3():
                if not isinstance(b, Vec3):
                    raise RuntimeError(
                        f'Need at least 2 Vec3 (1 per row) {self.tname} init args, '
                        f'not {b}: {type(b)}'
                    )
                self.val[0:3] = a[:]
                self.val[3:6] = b[:]
                if isinstance(c, Vec3):
                    self.val[6:9] = c[:]
                elif c is None:
                    self.val[6:9] = [0.0, 0.0, 1.0]
                else:
                    raise self.args_except(args)
            case _:
                raise self.args_except(args)

    def __str__(self):
        srows = [
            ', '.join(map(str, self.val[0:3])),
            ', '.join(map(str, self.val[3:6])),
            ', '.join(map(str, self.val[6:9])),
        ]
        sall = ', '.join([f'[{sr}]' for sr in srows])
        return f'[{sall}]'

    def rows(self):
        """Return list of rows (each as Vec3)"""
        return [Vec3(self.val[0:3]), Vec3(self.val[3:6]), Vec3(self.val[6:9])]

    def transpose(self):
        """Return matrix transpose"""
        v = self.val
        # fmt: off
        return Mat3(v[0], v[3], v[6],
                    v[1], v[4], v[7],
                    v[2], v[5], v[8])
        # fmt: on

    def det(self):
        """Return matrix determinant"""
        # fmt: off
        [a, b, c,
         d, e, f,
         g, h, i] = self.val[:]
        return a*e*i + b*f*g + c*d*h - c*e*g - b*d*i - a*f*h
        # fmt: on

    def inv(self):
        """Matrix inverse"""
        if self.val[6:9] == [0.0, 0.0, 1.0]:
            [a, b, c, d, e, f] = self.val[0:6]
            # (from GLK with Mathematica)
            det = a * e - b * d
            if not det:
                raise ValueError(f'Cannot invert affine {self.tname} with 0 determinant')
            # fmt: off
            return Mat3( e, -b, (b*f - c*e),
                        -d,  a, (c*d - a*f),
                         0,  0,     det   ) / det   # need last row to be 0 0 1
            # fmt: on
        # else
        det = self.det()
        if not det:
            raise ValueError(f'Cannot invert {self.tname} with 0 determinant')
        # fmt: off
        [a, b, c,
         d, e, f,
         g, h, i] = self.val[:]
        # (from GLK with Mathematica)
        return Mat3(e*i - f*h, c*h - b*i, b*f - c*e,
                    f*g - d*i, a*i - c*g, c*d - a*f,
                    d*h - e*g, b*g - a*h, a*e - b*d) / det
        # fmt: on

    def __matmul__(self, other):
        """Matrix-matrix or matrix-vector multiplication"""
        if isinstance(other, type(self)):
            # other is also a Mat3: interpret as matrix-matrix mul A B
            [r1A, r2A, r3A] = self.rows()
            [c1B, c2B, c3B] = other.cols()
            # fmt: off
            if self.val[6:9] == [0.0, 0.0, 1.0] and other.val[6:9] == [0.0, 0.0, 1.0]:
                return Mat3(
                    r1A @ c1B,  r1A @ c2B,  r1A @ c3B,
                    r2A @ c1B,  r2A @ c2B,  r2A @ c3B,
                )
            # fmt: on
            # else not affine
            # fmt: off
            return Mat3(r1A @ c1B,  r1A @ c2B,  r1A @ c3B,
                        r2A @ c1B,  r2A @ c2B,  r2A @ c3B,
                        r3A @ c1B,  r3A @ c2B,  r3A @ c3B)
            # fmt: on
        if isinstance(other, Vec3):
            # other is a Vec3: interpret as matrix-vector mul A V
            [r1, r2, r3] = self.rows()
            return Vec3(r1 @ other, r2 @ other, r3 @ other)
        if isinstance(other, Vec2):
            # other is a Vec2: matrix-vector mul with upper-left 2x2
            # e.g. for transforming 2D vectors with affine 3x3 matrix
            r1 = Vec2(self.val[0], self.val[1])
            r2 = Vec2(self.val[3], self.val[4])
            return Vec2(r1 @ other, r2 @ other)
        raise self.op_except('@', other)


class Mat4(_Mat):
    """Minimal 4x4 matrix class. Tries to be slightly more clever
    (currently, just .inv()) if affine."""

    # values in matrix are:
    #    a=0=11   b=1=12   c=2=13   d=3=14
    #    e=4=21   f=5=22   g=6=23   h=7=24
    #    i=8=31   j=9=32  k=10=33  l=11=34
    #   m=12=41  n=13=42  o=14=43  p=15=44

    def __init__(self, *args):
        super().__init__(16, 4)
        if super().init(*args):
            return
        # else do more work to interpret *args for initialization
        a = args[0]
        b = args[1] if len(args) > 1 else None
        c = args[2] if len(args) > 2 else None
        d = args[3] if len(args) > 3 else None
        match a:
            case _ if a == 1.0 and len(args) == 1:
                # asking for identity matrix
                # fmt: off
                self.val[0:16] = map(float, [1, 0, 0, 0,
                                             0, 1, 0, 0,
                                             0, 0, 1, 0,
                                             0, 0, 0, 1])
                # fmt: on
            case Vec4():
                if not (isinstance(b, Vec4) and isinstance(c, Vec4)):
                    raise RuntimeError(
                        f'Need at least 3 Vec4s (1 per row) {self.tname} init args, '
                        f'not {b}:{type(b)}, {c}:{type(c)}'
                    )
                self.val[0:4] = a[:]
                self.val[4:8] = b[:]
                self.val[8:12] = c[:]
                if isinstance(d, Vec4):
                    self.val[12:16] = d[:]
                elif d is None:
                    self.val[12:16] = [0.0, 0.0, 0.0, 1.0]
                else:
                    raise self.args_except(args)
            case _:
                raise self.args_except(args)

    def __str__(self):
        srows = [
            ', '.join(map(str, self.val[0:4])),
            ', '.join(map(str, self.val[4:8])),
            ', '.join(map(str, self.val[8:12])),
            ', '.join(map(str, self.val[12:16])),
        ]
        sall = ', '.join([f'[{sr}]' for sr in srows])
        return f'[{sall}]'

    def rows(self):
        """Return list of rows (each as Vec4)"""
        return [
            Vec4(self.val[0:4]),
            Vec4(self.val[4:8]),
            Vec4(self.val[8:12]),
            Vec4(self.val[12:16]),
        ]

    def transpose(self):
        """Return matrix transpose"""
        v = self.val
        # fmt: off
        return Mat4(v[0],  v[4],  v[8], v[12],
                    v[1],  v[5],  v[9], v[13],
                    v[2],  v[6], v[10], v[14],
                    v[3],  v[7], v[11], v[15])
        # fmt: on

    def det(self):
        """Return matrix determinant"""
        # fmt: off
        [a, b, c, d,
         e, f, g, h,
         i, j, k, l,
         m, n, o, p] = self.val[:]
        # from GLK with Mathematica
        return (d*g*j*m - c*h*j*m - d*f*k*m + b*h*k*m + c*f*l*m - b*g*l*m - d*g*i*n + c*h*i*n +
                d*e*k*n - a*h*k*n - c*e*l*n + a*g*l*n + d*f*i*o - b*h*i*o - d*e*j*o + a*h*j*o +
                b*e*l*o - a*f*l*o - c*f*i*p + b*g*i*p + c*e*j*p - a*g*j*p - b*e*k*p + a*f*k*p)
        # fmt: on

    def inv(self):
        """Matrix inverse"""
        if self.val[12:16] == [0.0, 0.0, 0.0, 1.0]:
            # fmt: off
            [a, b, c, d,
             e, f, g, h,
             i, j, k, l] = self.val[0:12]
            # from GLK with Mathematica
            det = a*f*k + b*g*i + c*e*j  - c*f*i- a*g*j - b*e*k
            if not det:
                raise ValueError(f'Cannot invert affine {self.tname} with 0 determinant')
            return Mat4(-g*j + f*k,  c*j - b*k, -c*f + b*g,
                              d*g*j - c*h*j - d*f*k + b*h*k + c*f*l - b*g*l,
                         g*i - e*k, -c*i + a*k,  c*e - a*g,
                             -d*g*i + c*h*i + d*e*k - a*h*k - c*e*l + a*g*l,
                        -f*i + e*j,  b*i - a*j, -b*e + a*f,
                              d*f*i - b*h*i - d*e*j + a*h*j + b*e*l - a*f*l,
                        0,  0,  0,  det) / det
            # factor out /det but ensure last row is 0 0 0 1
            # fmt: on
        # else not affine
        m = self.val
        det = self.det()
        if not det:
            raise ValueError(f'Cannot invert {self.tname} with 0 determinant')
        # fmt: off
        [a, b, c, d,
         e, f, g, h,
         i, j, k, l,
         m, n, o, p] = self.val[:]
        # from GLK with Mathematica
        return Mat4(f*k*p + g*l*n + h*j*o - f*l*o - g*j*p - h*k*n,
                    b*l*o + c*j*p + d*k*n - b*k*p - c*l*n - d*j*o,
                    b*g*p + c*h*n + d*f*o - b*h*o - c*f*p - d*g*n,
                    b*h*k + c*f*l + d*g*j - b*g*l - c*h*j - d*f*k,
                    e*l*o + g*i*p + h*k*m - e*k*p - g*l*m - h*i*o,
                    a*k*p + c*l*m + d*i*o - a*l*o - c*i*p - d*k*m,
                    a*h*o + c*e*p + d*g*m - a*g*p - c*h*m - d*e*o,
                    a*g*l + c*h*i + d*e*k - a*h*k - c*e*l - d*g*i,
                    e*j*p + f*l*m + h*i*n - e*l*n - f*i*p - h*j*m,
                    a*l*n + b*i*p + d*j*m - a*j*p - b*l*m - d*i*n,
                    a*f*p + b*h*m + d*e*n - a*h*n - b*e*p - d*f*m,
                    a*h*j + b*e*l + d*f*i - a*f*l - b*h*i - d*e*j,
                    e*k*n + f*i*o + g*j*m - e*j*o - f*k*m - g*i*n,
                    a*j*o + b*k*m + c*i*n - a*k*n - b*i*o - c*j*m,
                    a*g*n + b*e*o + c*f*m - a*f*o - b*g*m - c*e*n,
                    a*f*k + b*g*i + c*e*j - a*g*j - b*e*k - c*f*i) / det
        # fmt: on

    def __matmul__(self, other):
        """Matrix-matrix or matrix-vector multiplication"""
        if isinstance(other, type(self)):
            # other is also a Mat4: interpret as matrix-matrix mul A B
            [r1A, r2A, r3A, r4A] = self.rows()
            [c1B, c2B, c3B, c4B] = other.cols()
            # fmt: off
            return Mat4(r1A @ c1B,  r1A @ c2B,  r1A @ c3B,  r1A @ c4B,
                        r2A @ c1B,  r2A @ c2B,  r2A @ c3B,  r2A @ c4B,
                        r3A @ c1B,  r3A @ c2B,  r3A @ c3B,  r3A @ c4B,
                        r4A @ c1B,  r4A @ c2B,  r4A @ c3B,  r4A @ c4B)
            # fmt: on
        if isinstance(other, Vec4):
            # other is a Vec4: interpret as matrix-vector mul A V
            [r1, r2, r3, r4] = self.rows()
            return Vec4(r1 @ other, r2 @ other, r3 @ other, r4 @ other)
        if isinstance(other, Vec3):
            # other is a Vec3: matrix-vector mul with upper-left 3x3
            # e.g. for transforming 3D vectors with affine 4x4 matrix
            r1 = Vec3(self[0:3])
            r2 = Vec3(self[4:7])
            r3 = Vec3(self[8:11])
            return Vec3(r1 @ other, r2 @ other, r3 @ other)
        raise self.op_except('@', other)


class VecMatParseAction(_argparse.Action):
    """Custom action for parsing a Vec or Mat from the command-line"""

    # GLK got this approach (storing class cls to later disambiguate which type
    # of object is going to be parsed from the command-line) from ChatGPT, which
    # was unsurprisingly unable to provide a specific citation. More action info:
    # https://docs.python.org/3/library/argparse.html#action
    def __init__(self, option_strings, dest, cls, **kwargs):
        super().__init__(option_strings, dest, **kwargs)
        # Store the specific class to be instantiated
        self.cls = cls

    def __call__(self, _parser, namespace, strs, _option_string=None):
        # create instance of this class from the list of strings in strs
        # (note that _Base's init() can parse a list of strings)
        vm = self.cls(strs)
        # Set the parsed result in the namespace
        setattr(namespace, self.dest, vm)


if __name__ == '__main__':
    from random import random

    if True:
        print('----------------------------')
        print(f'{Vec2()=}')
        print(f'{Vec2("1 2")=}')
        print(f'{Vec2("1, 2")=}')
        print(f'{Vec2("1, 2,")=}')
        try:
            print(f'{Vec2("1 2 3")=}')
        except RuntimeError as e:
            print('  oops:', e)
        print(f'{Vec2(Vec3(1,2,0))=}')
        print(f'{Vec2(Vec3(1,2,3))=}')
        print(f'{Vec2(Vec2(1,2))=}')
        print(f'{Vec2((1,2))=}')
        print(f'{Vec2([1,2])=}')
        c2 = _ffi.new('float[2]', [1, 2])
        v2 = Vec2(c2)
        print(f'after v2=Vec2(c2=float[2]=[1,2]): {[c2[0],c2[1]]=} {v2=}')
        c2[0] = 11
        print(f'after c2[0]=11: {[c2[0],c2[1]]=} {v2=}')
        v2[1] = 22
        print(f'after v2[0]=22: {[c2[0],c2[1]]=} {v2=}')
        v2[:] = [111, 222]
        print(f'after v2[:] = [111,222]: {[c2[0],c2[1]]=} {v2=}')
        print(f'{Vec2(1,0).cross(Vec2(0,1))=}')
        print(f'{Vec2(0,1).cross(Vec2(1,0))=}')
        print(f'{Vec2(0,1).cross(Vec2(-1,0))=}')
    if True:
        print('----------------------------')
        print(f'{Vec3()=}')
        print(f'{Vec3("1 2 3")=}')
        print(f'{Vec3("1, 2, 3")=}')
        try:
            print(f'{Vec3("1 2")=}')
        except RuntimeError as e:
            print('  oops:', e)
        print(f'{Vec3(Vec2(1,2),9)=}')
        print(f'{Vec3(Vec3(1,2,3))=}')
        print(f'{Vec3((1,2,3))=}')
        print(f'{Vec3([1,2,3])=}')
        print(f'{Vec3(_ffi.new("float[3]", [1,2,3]))=}')
        print(f'{Vec3(1,0,0).cross(Vec3(0,1,0))=}')
        print(f'{Vec3(0,1,0).cross(Vec3(0,0,1))=}')
        print(f'{Vec3(0,0,1).cross(Vec3(1,0,0))=}')
        print(f'{-Vec3(1,2,3)=}')
        print(f'{+Vec3(1,2,3)=}')
    if True:
        print('-------- +  +  --------------------')
        V = Vec3(1, 2, 3)
        print(f'{V=}')
        U = V
        print(f'U=V: {U=}, {V=}')
        V.y = 100
        print(f'V.y=100: {U=}, {V=}')
        W = +V
        print(f'W=+V: {W=}, {V=}')
        V.y = 33
        print(f'V.y=33: {W=}, {V=}')
    if True:
        print('---- mat2 ------------------------')
        A = Mat2([random() for _ in range(4)])
        print(f'{A=}')
        print(f'{A.T=}')
        print(f'{A.inv()=}')
        print(f'{A.inv() @ A - Mat2(1)=}\n   frob = {abs(A.inv() @ A - Mat2(1))}')
        print(f'{A @ A.inv() - Mat2(1)=}\n   frob = {abs(A @ A.inv() - Mat2(1))}')
        print('---- mat3 affine ------------------------')
        B = Mat3([random() for _ in range(6)])
        print(f'{B=}')
        print(f'{B.T=}')
        print(f'{B.inv()=}')
        print(f'{B.inv() @ B - Mat3(1)=}\n   frob = {abs(B.inv() @ B - Mat3(1))}')
        print(f'{B @ B.inv() - Mat3(1)=}\n   frob = {abs(B @ B.inv() - Mat3(1))}')
        print('---- mat3 ------------------------')
        C = Mat3([random() for _ in range(9)])
        print(f'{C=}')
        print(f'{C.T=}')
        print(f'{C.inv()=}')
        print(f'{C.inv() @ C - Mat3(1)=}\n   frob = {abs(C.inv() @ C - Mat3(1))}')
        print(f'{C @ C.inv() - Mat3(1)=}\n   frob = {abs(C @ C.inv() - Mat3(1))}')
