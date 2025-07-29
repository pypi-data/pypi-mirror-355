"""
wire has the basic extended types useful for creating logic.

Types defined in this file include:

* `WireVector` -- the base class for ordered collections of wires
* `Input` -- a wire vector that receives an input for a block
* `Output` -- a wire vector that defines an output for a block
* `Const` -- a wire vector fed by a constant
* `Register` -- a wire vector that is latched each cycle
"""

from __future__ import annotations

import numbers
import re
import sys
from typing import Union

from . import core  # needed for _setting_keep_wirevector_call_stack

from .pyrtlexceptions import PyrtlError, PyrtlInternalError
from .core import working_block, LogicNet, _NameIndexer, Block

# ----------------------------------------------------------------
#        ___  __  ___  __   __
#  \  / |__  /  `  |  /  \ |__)
#   \/  |___ \__,  |  \__/ |  \
#


_wvIndexer = _NameIndexer("tmp")
_constIndexer = _NameIndexer("const_")


def _reset_wire_indexers():
    global _wvIndexer, _constIndexer
    _wvIndexer = _NameIndexer("tmp")
    _constIndexer = _NameIndexer("const_")


def next_tempvar_name(name=""):
    if name == '':  # sadly regex checks are sometimes too slow
        wire_name = _wvIndexer.make_valid_string()
        callpoint = core._get_useful_callpoint_name()
        if callpoint:  # returns none if debug mode is false
            filename, lineno = callpoint
            safename = re.sub(r'[\W]+', '', filename)  # strip out non alphanumeric characters
            wire_name += '_%s_line%d' % (safename, lineno)
        return wire_name
    else:
        if name.lower() in ['clk', 'clock']:
            raise PyrtlError('Clock signals should never be explicit')
        return name


class WireVector(object):
    """The main class for describing the connections between operators.

    WireVectors act much like a list of wires, except that there is no
    "contained" type, each slice of a WireVector is itself a WireVector (even
    if it just contains a single "bit" of information). The least significant
    bit of the wire is at index 0 and normal list slicing syntax applies (i.e.
    ``myvector[0:5]`` makes a new vector from the bottom 5 bits of
    ``myvector``, ``myvector[-1]`` takes the most significant bit, and
    ``myvector[-4:]`` takes the 4 most significant bits).

    ===============  ================  =======================================================
    Operation        Syntax            Function
    ===============  ================  =======================================================
    Addition         ``a + b``         Creates an unsigned adder, returns WireVector
    Subtraction      ``a - b``         Creates an unsigned subtracter, returns WireVector
    Multiplication   ``a * b``         Creates an unsigned multiplier, returns WireVector
    Xor              ``a ^ b``         Bitwise XOR, returns WireVector
    Or               ``a | b``         Bitwise OR, returns WireVector
    And              ``a & b``         Bitwise AND, returns WireVector
    Invert           ``~a``            Bitwise invert, returns WireVector
    Less Than        ``a < b``         Unsigned less than, return 1-bit WireVector
    Less or Eq.      ``a <= b``        Unsigned less than or equal to, return 1-bit WireVector
    Greater Than     ``a > b``         Unsigned greater than, return 1-bit WireVector
    Greater or Eq.   ``a >= b``        Unsigned greater or equal to, return 1-bit WireVector
    Equality         ``a == b``        Hardware to check equality, return 1-bit WireVector
    Not Equal        ``a != b``        Inverted equality check, return 1-bit WireVector
    Bitwidth         ``len(a)``        Return bitwidth of the WireVector
    Assignment       ``a <<= b``       Connect from b to a (see note below)
    Bit Slice        ``a[3:6]``        Selects bits from WireVector, in this case bits 3,4,5
    ===============  ================  =======================================================

    A note on ``<<=`` asssignment: This operator is how you "drive" an already
    created wire with an existing wire. If you were to do ``a = b`` it would
    lose the old value of ``a`` and simply overwrite it with a new value, in
    this case with a reference to WireVector ``b``. In contrast ``a <<= b``
    does not overwrite ``a``, but simply wires the two together.

    -------------------
    WireVector Equality
    -------------------

    WireVector's :meth:`.__eq__` generates logic that dynamically reports if two wires
    carry the same values. WireVector's :meth:`.__eq__` returns a 1-bit WireVector, not
    a ``bool``, and attempting to convert a WireVector to a ``bool`` throws a
    ``PyrtlError``. This behavior is incompatible with `Python's data model
    <https://docs.python.org/3/reference/expressions.html#value-comparisons>`_, which
    can cause problems.

    For example, you *can not* statically check if two WireVectors are equal with
    ``==``. Statically checking for WireVector equality can be useful while constructing
    or analyzing circuits::

        >>> w1 = pyrtl.WireVector(name="w1", bitwidth=1)
        >>> w2 = pyrtl.WireVector(name="w2", bitwidth=2)
        >>> if w1 == w2:
        ...     print('same')
        ...
        Traceback (most recent call last):
        ...
        pyrtl.pyrtlexceptions.PyrtlError: cannot convert WireVector to compile-time
        boolean.  This error often happens when you attempt to use WireVectors with "=="
        or something that calls "__eq__", such as when you test if a WireVector is "in"
        something

    The error about converting WireVector to ``bool`` results from Python attempting to
    convert the 1-bit WireVector returned by :meth:`.__eq__` to ``True`` or ``False``
    while evaluating the ``if`` statement's condition.

    Instead, you *can* statically check if two WireVectors refer to the same object with
    ``is``::

        >>> if w1 is not w2:
        ...     print('not the same')
        ...
        not the same
        >>> temp = w1
        >>> temp is w1
        True
        >>> temp is w2
        False

    Be careful when using Python features that depend on ``==`` with WireVectors. This
    often comes up when checking if a WireVector is in a list with ``in``, which does
    not work because ``in`` falls back on checking each item in the ``list`` for
    equality with ``==``::

        >>> l = [w1]
        >>> w2 in l
        Traceback (most recent call last):
        ...
        pyrtl.pyrtlexceptions.PyrtlError: cannot convert WireVector to compile-time
        boolean.  This error often happens when you attempt to use WireVectors with "=="
        or something that calls "__eq__", such as when you test if a WireVector is "in"
        something

    Most other ``list`` operations work, so you can store WireVectors in a ``list`` if
    you avoid using the ``in`` operator::

        >>> len(l)
        1
        >>> l[0] is w1
        True
        >>> [(w.name, w.bitwidth) for w in l]
        [('w1', 1)]

    WireVectors define a standard ``__hash__`` method, so if you need to check if a
    WireVector is in a container, use a ``set`` or ``dict``. This works because these
    containers use ``__hash__`` to skip unnecessary equality checks::

        >>> s = {w1}
        >>> w1 in s
        True
        >>> w2 in s
        False

        >>> d = {w1: 'hello'}
        >>> w1 in d
        True
        >>> w2 in d
        False
        >>> d[w1]
        'hello'

    """

    # "code" is a static variable used when output as string.
    # Each class inheriting from WireVector should overload accordingly
    _code = 'W'

    def __init__(self, bitwidth: int = None, name: str = '',
                 block: Block = None):
        """Construct a generic WireVector.

        :param bitwidth: If no bitwidth is provided, it will be set to the
            minimum number of bits to represent this wire
        :param block: The block under which the wire should be placed.
            Defaults to the working block
        :param name: The name of the wire referred to in some places.
            Must be unique. If none is provided, one will be autogenerated

        Examples::

            # Visible in trace as "data".
            data = pyrtl.WireVector(bitwidth=8, name='data')
            # `ctrl` is assigned a temporary name, and will not be visible in
            # traces by default.
            ctrl = pyrtl.WireVector(bitwidth=1)
            # `temp` is a temporary with bitwidth specified later.
            temp = pyrtl.WireVector()
            # `temp` gets the bitwidth of 8 from data.
            temp <<= data

        """
        self._name = None

        # used only to verify the one to one relationship of wires and blocks
        self._block = working_block(block)
        self.name = next_tempvar_name(name)
        self._validate_bitwidth(bitwidth)

        if core._setting_keep_wirevector_call_stack:
            import traceback
            self.init_call_stack = traceback.format_stack()

    @property
    def name(self) -> str:
        """A property holding the name (a string) of the WireVector.

        The name can be read or written. Examples::

            a = WireVector(bitwidth=1, name='foo')
            print(a.name)  # Prints 'foo'.
            a.name = 'mywire'

        """
        return self._name

    @name.setter
    def name(self, value: str):
        if not isinstance(value, str):
            raise PyrtlError('WireVector names must be strings')
        self._block.wirevector_by_name.pop(self._name, None)
        self._name = value
        self._block.add_wirevector(self)

    def __hash__(self):
        return id(self)

    def __str__(self):
        """A string representation of the wire in 'name/bitwidth code' form."""
        return f'{self.name}/{self.bitwidth}{self._code}'

    def __repr__(self):
        return str(self)

    def _validate_bitwidth(self, bitwidth):
        if bitwidth is not None:
            if not isinstance(bitwidth, numbers.Integral):
                raise PyrtlError('bitwidth must be from type int or unspecified, instead "%s"'
                                 ' was passed of type %s' % (str(bitwidth), type(bitwidth)))
            elif bitwidth == 0:
                raise PyrtlError('bitwidth must be greater than or equal to 1')
            elif bitwidth < 0:
                raise PyrtlError('you are trying a negative bitwidth? awesome but wrong')
        self.bitwidth = bitwidth

    def _build(self, other):
        # Actually create and add WireVector to logic block
        # This might be called immediately from ilshift, or delayed from conditional assignment
        net = LogicNet(
            op='w',
            op_param=None,
            args=(other,),
            dests=(self,))
        working_block().add_net(net)

    def _prepare_for_assignment(self, rhs):
        # Convert right-hand-side to wires and propagate bitwidth if necessary
        from .corecircuits import as_wires
        rhs = as_wires(rhs, bitwidth=self.bitwidth)
        if self.bitwidth is None:
            self.bitwidth = rhs.bitwidth
        return rhs

    def __ilshift__(self, other):
        """ Wire assignment operator (assign other to self).

        Example::

            i = pyrtl.Input(8, 'i')
            t = pyrtl.WireVector(8, 't')
            t <<= i
        """
        other = self._prepare_for_assignment(other)
        self._build(other)
        return self

    def __ior__(self, other):
        """Conditional assignment operator (only valid under Conditional Update)."""
        from .conditional import _build, currently_under_condition
        if not self.bitwidth:
            raise PyrtlError('Conditional assignment only defined on '
                             'WireVectors with pre-defined bitwidths')
        other = self._prepare_for_assignment(other)
        if currently_under_condition():
            _build(self, other)
        else:
            self._build(other)
        return self

    def _two_var_op(self, other, op):
        from .corecircuits import as_wires, match_bitwidth

        # convert constants if necessary
        a, b = self, as_wires(other)
        a, b = match_bitwidth(a, b)
        resultlen = len(a)  # both are the same length now

        # some operations actually create more or less bits
        if op in '+-':
            resultlen += 1  # extra bit required for carry
        elif op == '*':
            resultlen = resultlen * 2  # more bits needed for mult
        elif op in '<>=':
            resultlen = 1

        s = WireVector(bitwidth=resultlen)
        net = LogicNet(
            op=op,
            op_param=None,
            args=(a, b),
            dests=(s,))
        working_block().add_net(net)
        return s

    def __bool__(self):
        """ Use of a WireVector in a statement like "a or b" is forbidden."""
        # python provides no way to overload these logical operations, and thus they
        # are very much not likely to be doing the thing that the programmer would be
        # expecting.
        raise PyrtlError('cannot convert WireVector to compile-time boolean.  This error '
                         'often happens when you attempt to use WireVectors with "==" or '
                         'something that calls "__eq__", such as when you test if a '
                         'WireVector is "in" something')

    __nonzero__ = __bool__  # for Python 2 and 3 compatibility

    def __and__(self, other):
        """Bitwise ANDs two wires together into a single wire.

        :rtype: WireVector
        :return: the result wire of the operation

        Example::

                temp = a & b
        """
        return self._two_var_op(other, '&')

    def __rand__(self, other):
        return self._two_var_op(other, '&')

    def __iand__(self, other):
        raise PyrtlError('error, operation not allowed on WireVectors')

    def __or__(self, other):
        """Bitwise ORs two wires together into a single wire.

        :rtype: WireVector
        :return: the result wire of the operation

        Example::

            temp = a | b
        """
        return self._two_var_op(other, '|')

    def __ror__(self, other):
        return self._two_var_op(other, '|')

    # __ior__ used for conditional assignment above

    def __xor__(self, other):
        """Bitwise XORs two wires together into a single wire.

        :rtype: WireVector
        :return: the result wire of the operation
        """
        return self._two_var_op(other, '^')

    def __rxor__(self, other):
        return self._two_var_op(other, '^')

    def __ixor__(self, other):
        raise PyrtlError('error, operation not allowed on WireVectors')

    def __add__(self, other):
        """Adds two wires together into a single WireVector.

        Addition is *unsigned*. Use :func:`.signed_add` for signed addition.

        :rtype: WireVector
        :return: Returns the result wire of the operation. The resulting wire
            has one more bit than the longer of the two input wires.

        Examples::

            temp = a + b  # simple addition of two WireVectors
            temp = a + 5  # you can use integers
            temp = a + 0b110  # you can use other integers
            temp = a + "3'h7"  # compatible verilog constants work too

        """
        return self._two_var_op(other, '+')

    def __radd__(self, other):
        return self._two_var_op(other, '+')

    def __iadd__(self, other):
        raise PyrtlError('error, operation not allowed on WireVectors')

    def __sub__(self, other):
        """Subtracts the right wire from the left one.

        Subtraction is *unsigned*. Use :func:`.signed_sub` for signed
        subtraction.

        :rtype: WireVector
        :return: Returns the result wire of the operation. The resulting wire
            has one more bit than the longer of the two input wires.

        """
        return self._two_var_op(other, '-')

    def __rsub__(self, other):
        from .corecircuits import as_wires
        other = as_wires(other)  # '-' op is not symmetric
        return other._two_var_op(self, '-')

    def __isub__(self, other):
        raise PyrtlError('error, operation not allowed on WireVectors')

    def __mul__(self, other):
        """Multiplies two WireVectors.

        Multiplication is *unsigned*. Use :func:`.signed_mult` for signed
        multiplication.

        :rtype: WireVector
        :return: Returns the result wire of the operation. The resulting wire's
            bitwidth is the sum of the two input wires' bitwidths.

        """
        return self._two_var_op(other, '*')

    def __rmul__(self, other):
        return self._two_var_op(other, '*')

    def __imul__(self, other):
        raise PyrtlError('error, operation not allowed on WireVectors')

    def __lt__(self, other):
        """Calculates whether a wire is less than another.

        The comparison is *unsigned*. Use :func:`.signed_lt` for a signed
        comparison.

        :rtype: WireVector
        :return: a one bit result wire of the operation

        """
        return self._two_var_op(other, '<')

    def __le__(self, other):
        """Calculates whether a wire is less than or equal to another.

        The comparison is *unsigned*. Use :func:`.signed_le` for a signed
        comparison.

        :rtype: WireVector
        :return: a one bit result wire of the operation

        """
        return ~ self._two_var_op(other, '>')

    def __eq__(self, other):
        """Calculates whether a wire is equal to another.

        :rtype: WireVector
        :return: a one bit result wire of the operation

        """
        return self._two_var_op(other, '=')

    def __ne__(self, other):
        """Calculates whether a wire is not equal to another.

        :rtype: WireVector
        :return: a one bit result wire of the operation

        """
        return ~ self._two_var_op(other, '=')

    def __gt__(self, other):
        """Calculates whether a wire is greater than another.

        The comparison is *unsigned*. Use :func:`.signed_gt` for a signed
        comparison.

        :rtype: WireVector
        :return: a one bit result wire of the operation

        """
        return self._two_var_op(other, '>')

    def __ge__(self, other):
        """Calculates whether a wire is greater than or equal to another.

        The comparison is *unsigned*. Use :func:`.signed_ge` for a signed
        comparison.

        :rtype: WireVector
        :return: a one bit result wire of the operation

        """
        return ~ self._two_var_op(other, '<')

    def __invert__(self):
        """Bitwise inverts a wire.

        :rtype: WireVector
        :return: a result wire for the operation

        """
        outwire = WireVector(bitwidth=len(self))
        net = LogicNet(
            op='~',
            op_param=None,
            args=(self,),
            dests=(outwire,))
        working_block().add_net(net)
        return outwire

    def __getitem__(self, item):
        """Grabs a subset of the wires.

        :rtype: WireVector
        :return: a result wire for the operation

        """
        if self.bitwidth is None:
            raise PyrtlError('You cannot get a subset of a wire with no bitwidth')
        allindex = range(self.bitwidth)
        if isinstance(item, int):
            selectednums = (allindex[item], )  # this method handles negative numbers correctly
        else:  # slice
            selectednums = tuple(allindex[item])
        if not selectednums:
            raise PyrtlError('selection %s must have at least one selected wire' % str(item))
        outwire = WireVector(bitwidth=len(selectednums))
        net = LogicNet(
            op='s',
            op_param=selectednums,
            args=(self,),
            dests=(outwire,))
        working_block().add_net(net)
        return outwire

    def __lshift__(self, other):
        raise PyrtlError('Shifting using the << and >> operators are not supported '
                         'in PyRTL. '
                         'If you are trying to select bits in a wire, use '
                         'the indexing operator (wire[indexes]) instead.\n\n'
                         'For example: wire[2:9] selects the wires from index 2 to '
                         'index 8 to make a new length 7 wire. \n\n If you are really '
                         'trying to *execution time* shift you can use "shift_left_arithmetic", '
                         '"shift_right_arithmetic", "shift_left_logical", "shift_right_logical"')

    __rshift__ = __lshift__

    def __mod__(self, other):
        raise PyrtlError("Masking with the % operator is not supported"
                         "in PyRTL. "
                         "Instead if you are trying to select bits in a wire, use"
                         "the indexing operator (wire[indexes]) instead.\n\n"
                         "For example: wire[2:9] selects the wires from index 2 to "
                         "index 8 to make a new length 7 wire.")

    def __len__(self) -> int:
        """Get the bitwidth of a WireVector.

        :return: Returns the length (i.e. bitwidth) of the WireVector in bits.

        Note that WireVectors do not need to have a bitwidth defined when they
        are first allocated. They can get it from a ``<<=`` assignment later.
        However, if you check the ``len`` of WireVector with undefined bitwidth
        it will throw ``PyrtlError``.

        """
        if self.bitwidth is None:
            raise PyrtlError('length of WireVector not yet defined')
        else:
            return self.bitwidth

    def __enter__(self):
        """ Use wires as contexts for conditional assignments. """
        from .conditional import _push_condition
        _push_condition(self)

    def __exit__(self, *execinfo):
        from .conditional import _pop_condition
        _pop_condition()

    # more functions for wires
    def nand(self, other):
        """Bitwise NANDs two WireVectors together to a single WireVector.

        :rtype: WireVector
        :return: Returns WireVector of the nand operation.

        """
        return self._two_var_op(other, 'n')

    @property
    def bitmask(self) -> int:
        """A property holding a bitmask of the same length as this WireVector.

        Specifically it is an integer with a number of bits set to 1 equal to
        the bitwidth of the WireVector.

        It is often times useful to "mask" an integer such that it fits in the
        the number of bits of a WireVector. As a convenience for this, the
        ``bitmask`` property is provided. As an example, if there was a 3-bit
        WireVector ``a``, a call to ``a.bitmask()`` should return ``0b111`` or
        ``0x7``.

        """
        if "_bitmask" not in self.__dict__:
            self._bitmask = (1 << len(self)) - 1
        return self._bitmask

    def truncate(self, bitwidth: int):
        """Generate a new truncated WireVector derived from self.

        :param bitwidth: Number of bits to truncate to.
        :rtype: WireVector
        :return: Returns a new WireVector equal to the original WireVector but
            truncated to the specified bitwidth.

        If the bitwidth specified is larger than the bitwidth of self, then
        ``PyrtlError`` is thrown.

        """
        if not isinstance(bitwidth, int):
            raise PyrtlError('Can only truncate to an integer number of bits')
        if bitwidth > self.bitwidth:
            raise PyrtlError('Cannot truncate a WireVector to have more bits than it started with')
        return self[:bitwidth]

    def sign_extended(self, bitwidth):
        """Generate a new sign extended WireVector derived from self.

        :rtype: WireVector
        :return: Returns a new WireVector equal to the original WireVector sign
            extended to the specified bitwidth.

        If the bitwidth specified is smaller than the bitwidth of self, then
        ``PyrtlError`` is thrown.

        """
        return self._extend_with_bit(bitwidth, self[-1])

    def zero_extended(self, bitwidth):
        """Generate a new zero extended WireVector derived from self.

        :rtype: WireVector
        :return: Returns a new WireVector equal to the original WireVector zero
            extended to the specified bitwidth.

        If the bitwidth specified is smaller than the bitwidth of self, then
        ``PyrtlError`` is thrown.

        """
        return self._extend_with_bit(bitwidth, 0)

    def _extend_with_bit(self, bitwidth, extbit):
        numext = bitwidth - self.bitwidth
        if numext == 0:
            return self
        elif numext < 0:
            raise PyrtlError(
                'Neither zero_extended nor sign_extended can'
                ' reduce the number of bits')
        else:
            from .corecircuits import concat
            if isinstance(extbit, int):
                extbit = Const(extbit, bitwidth=1)
            extvector = WireVector(bitwidth=numext)
            net = LogicNet(
                op='s',
                op_param=(0,) * numext,
                args=(extbit,),
                dests=(extvector,))
            working_block().add_net(net)
            return concat(extvector, self)


# -----------------------------------------------------------------------
#  ___     ___  ___       __   ___  __           ___  __  ___  __   __   __
# |__  \_/  |  |__  |\ | |  \ |__  |  \    \  / |__  /  `  |  /  \ |__) /__`
# |___ / \  |  |___ | \| |__/ |___ |__/     \/  |___ \__,  |  \__/ |  \ .__/
#

class Input(WireVector):
    """A WireVector type denoting inputs to a block (no writers)."""
    _code = 'I'

    def __init__(self, bitwidth: int = None, name: str = '',
                 block: Block = None):
        super(Input, self).__init__(bitwidth=bitwidth, name=name, block=block)

    def __ilshift__(self, _):
        """ This is an illegal op for Inputs. They cannot be assigned to in this way """
        raise PyrtlError(
            'Connection using <<= operator attempted on Input. '
            'Inputs, such as "%s", cannot have values generated internally. '
            "aka they can't have other wires driving it"
            % str(self.name))

    def __ior__(self, _):
        """ This is an illegal op for Inputs. They cannot be assigned to in this way """
        raise PyrtlError(
            'Connection using |= operator attempted on Input. '
            'Inputs, such as "%s", cannot have values generated internally. '
            "aka they can't have other wires driving it"
            % str(self.name))


class Output(WireVector):
    """A WireVector type denoting outputs of a block (no readers).

    Even though Output seems to have valid ops such as ``__or__`` , using
    them will throw an error.

    """
    _code = 'O'

    def __init__(self, bitwidth: int = None, name: str = '',
                 block: Block = None):
        super(Output, self).__init__(bitwidth, name, block)


class Const(WireVector):
    """A WireVector representation of a constant value.

    Converts from bool, integer, or Verilog-style strings to a constant
    of the specified bitwidth.  If the bitwidth is too short to represent
    the specified constant, then an error is raised.  If a positive
    integer is specified, the bitwidth can be inferred from the constant.
    If a negative integer is provided in the simulation, it is converted
    to a two's complement representation of the specified bitwidth.

    """

    _code = 'C'

    def __init__(self, val: Union[int, bool, str], bitwidth: int = None,
                 name: str = '', signed: bool = False, block: Block = None):
        """Construct a constant implementation at initialization.

        :param val: the value for the const WireVector
        :param bitwidth: the desired bitwidth of the resulting const
        :param name: The name of the wire referred to in some places.
            Must be unique. If none is provided, one will be autogenerated
        :param signed: specify if bits should be used for two's complement

        Descriptions for all parameters not listed above can be found at
        :meth:`.WireVector.__init__`

        For details of how constants are converted from int, bool, and strings
        (for Verilog constants), see documentation for the helper function
        :py:func:`.infer_val_and_bitwidth`. Please note that a constant
        generated with ``signed=True`` is still just a raw bitvector and all
        arthimetic on it is unsigned by default. The ``signed=True`` argument
        is only used for proper inference of WireVector size and certain
        bitwidth sanity checks assuming a two's complement representation of
        the constants.

        """
        self._validate_bitwidth(bitwidth)
        from .helperfuncs import infer_val_and_bitwidth
        num, bitwidth = infer_val_and_bitwidth(val, bitwidth, signed)

        if num < 0:
            raise PyrtlInternalError(
                'Const somehow evaluating to negative integer after checks')
        if (num >> bitwidth) != 0:
            raise PyrtlInternalError(
                'constant %d returned by infer_val_and_bitwidth somehow not fitting in %d bits'
                % (num, bitwidth))

        name = name if name else _constIndexer.make_valid_string() + '_' + str(val)

        super(Const, self).__init__(bitwidth=bitwidth, name=name, block=block)
        # add the member "val" to track the value of the constant
        self.val = num

    def __ilshift__(self, other):
        """ This is an illegal op for Consts. Their value is set in the __init__ function"""
        raise PyrtlError(
            'ConstWires, such as "%s", should never be assigned to with <<='
            % str(self.name))

    def __ior__(self, _):
        """ This is an illegal op for Consts. They cannot be assigned to in this way """
        raise PyrtlError(
            'Connection using |= operator attempted on Const. '
            'ConstWires, such as "%s", cannot have values generated internally. '
            "aka they cannot have other wires driving it"
            % str(self.name))


class Register(WireVector):
    """A WireVector with an embedded register state element.

    Registers only update their outputs on the rising edges of an implicit clock signal.
    The "value" in the current cycle can be accessed by referencing the Register itself.
    To set the value for the next cycle (after the next rising clock edge), set the
    :attr:`.Register.next` property with the ``<<=`` operator.

    Registers reset to zero by default, and reside in the same clock domain.

    Example::

        counter = pyrtl.Register(bitwidth=8)
        counter.next <<= counter + 1

    This builds a zero-initialized 8-bit counter. The second line sets the counter's
    value in the next cycle (``counter.next``) to the counter's value in the current
    cycle (``counter``), plus one.

    """
    _code = 'R'

    # When a register's next value is assigned, the following occurs:
    #
    # 1. The register's `.next` property is retrieved. Register.next returns an instance
    #    of Register._Next.
    # 2. __ilshift__ is invoked on the returned instance of Register._Next.
    #
    # So `reg.next <<= foo` effectively does the following:
    #
    #     reg.next = Register._Next(reg)
    #     reg.next.__ilshift__(reg, foo)
    #
    # The following behavior is expected:
    #
    #     reg.next <<= 5  # good
    #     a <<= reg       # good
    #     reg <<= 5       # error
    #     a <<= reg.next  # error
    #     reg.next = 5    # error
    class _Next(object):
        """Type returned by the ``Register.next`` property.

        This class allows unconditional assignments (``<<=``, ``__ilshift__``) and
        conditional assignments (``|=``, ``__ior__``) on ``Register.next``. Registers
        themselves do not support assignments, so ``Register.__ilshift__`` and
        ``Register.__ior__`` throw errors.

        ``__ilshift__`` and ``__ior__`` must both return ``self`` because::

            x <<= y

        is equivalent to::

            x = x.__ilshift__(y)

        Note how ``__ilshift__``'s return value is assigned to ``x``, see
        https://docs.python.org/3/library/operator.html#in-place-operators

        ``__ilshift__`` and ``__ior__`` both return ``self`` and Register's @next.setter
        checks that Register.next is assigned to an instance of _Next.

        """
        def __init__(self, reg):
            self.reg = reg

        def __ilshift__(self, other):
            from .corecircuits import as_wires
            other = as_wires(other, bitwidth=self.reg.bitwidth)
            if self.reg.bitwidth is None:
                self.reg.bitwidth = other.bitwidth

            if self.reg.reg_in is not None:
                raise PyrtlError('error, .next value should be set once and only once')
            self.reg._build(other)

            return self

        def __ior__(self, other):
            from .conditional import _build
            from .corecircuits import as_wires
            other = as_wires(other, bitwidth=self.reg.bitwidth)
            if not self.reg.bitwidth:
                raise PyrtlError('Conditional assignment only defined on '
                                 'Registers with pre-defined bitwidths')

            if self.reg.reg_in is not None:
                raise PyrtlError('error, .next value should be set once and only once')
            _build(self.reg, other)

            return self

        def __bool__(self):
            """ Use of a _next in a statement like "a or b" is forbidden."""
            raise PyrtlError('cannot convert Register.next to compile-time boolean.  This error '
                             'often happens when you attempt to use a Register.next with "==" or '
                             'something that calls "__eq__", such as when you test if a '
                             'Register.next is "in" something')

        __nonzero__ = __bool__  # for Python 2 and 3 compatibility

    def __init__(self, bitwidth: int, name: str = '', reset_value: int = None,
                 block: Block = None):
        """Construct a register.

        :param bitwidth: Number of bits to represent this register.
        :param name: The name of the register's current value (``reg``, not
            ``reg.next``). Must be unique. If none is provided, one will be
            autogenerated.
        :param reset_value: Value to initialize this register to during
            simulation and in any code (e.g. Verilog) that is exported.
            Defaults to 0. Can be overridden at simulation time.
        :param block: The block under which the wire should be placed. Defaults
            to the working block.

        It is an error if the ``reset_value`` cannot fit into the specified
        bitwidth for this register.

        """
        from pyrtl.helperfuncs import infer_val_and_bitwidth

        super(Register, self).__init__(bitwidth=bitwidth, name=name, block=block)
        self.reg_in = None  # wire vector setting self.next
        if reset_value is not None:
            reset_value, rst_bitwidth = infer_val_and_bitwidth(
                reset_value,
                bitwidth=bitwidth,
            )
            if rst_bitwidth > bitwidth:
                raise PyrtlError(
                    'reset_value "%s" cannot fit in the specified %d bits for this register'
                    % (str(reset_value), bitwidth)
                )
        self.reset_value = reset_value

    @property
    def next(self):
        """Sets the Register's value for the next cycle (it is before the D-Latch)."""
        return Register._Next(self)

    def __ilshift__(self, other):
        raise PyrtlError('error, you cannot set registers directly, net .next instead')

    def __ior__(self, other):
        raise PyrtlError('error, you cannot set registers directly, net .next instead')

    @next.setter
    def next(self, other):
        if not isinstance(other, Register._Next):
            raise PyrtlError('error, .next should be set with "<<=" or "|=" operators')

    def _build(self, next):
        # Actually build the register. This happens immediately when setting the `next`
        # property. Under conditional assignment, register build is delayed until the
        # conditional assignment is _finalized.
        self.reg_in = next
        net = LogicNet('r', None, args=(self.reg_in,), dests=(self,))
        working_block().add_net(net)


class WrappedWireVector:
    '''Wraps a WireVector. Forwards all method calls and attribute accesses.

    WrappedWireVector is useful for dynamically choosing a WireVector base
    class at runtime. If the base class is statically known, do not use
    WrappedWireVector, and just inherit from the base class normally.

    @wire_struct and wire_matrix use WrappedWireVector to implement the
    ``concatenated_type`` option, so an instance can dynamically choose its
    desired base class.

    '''
    wire = None

    def __init__(self, wire: WireVector):
        self.__dict__['wire'] = wire

    def __getattr__(self, name: str):
        '''Forward all attribute accesses to the wrapped WireVector.

        This does not work for special methods like ``__hash__``. Special
        methods are handled separately below.

        '''
        return getattr(self.wire, name)

    def __setattr__(self, name, value):
        '''Forward all attribute assignments to the wrapped WireVector.

        This is needed to make ``reg.next <<= foo`` work, because that expands to::

            reg.next = reg.next.__ilshift__(foo)

        See https://docs.python.org/3/library/operator.html#in-place-operators

        This attribute assignment must be forwarded to the underlying Register.

        '''
        self.wire.__setattr__(name, value)

    def __hash__(self):
        return hash(self.wire)

    def __str__(self):
        return str(self.wire)

    def __repr__(self):
        return repr(self.wire)

    def __ilshift__(self, other):
        self.wire <<= other
        return self

    def __ior__(self, other):
        self.wire |= other
        return self

    def __bool__(self):
        return bool(self.wire)

    def __and__(self, other):
        return self.wire & other

    def __rand__(self, other):
        return other & self.wire

    def __iand__(self, other):
        self.wire &= other
        return self

    def __or__(self, other):
        return self.wire | other

    def __ror__(self, other):
        return other | self.wire

    def __xor__(self, other):
        return self.wire ^ other

    def __rxor__(self, other):
        return other ^ self.wire

    def __ixor__(self, other):
        self.wire ^= other
        return self

    def __add__(self, other):
        return self.wire + other

    def __radd__(self, other):
        return other + self.wire

    def __iadd__(self, other):
        self.wire += other
        return self

    def __sub__(self, other):
        return self.wire - other

    def __rsub__(self, other):
        return other - self.wire

    def __isub__(self, other):
        self.wire -= other
        return self

    def __mul__(self, other):
        return self.wire * other

    def __rmul__(self, other):
        return other * self.wire

    def __imul__(self, other):
        self.wire *= other
        return self

    def __lt__(self, other):
        return self.wire < other

    def __le__(self, other):
        return self.wire <= other

    def __eq__(self, other):
        return self.wire == other

    def __ne__(self, other):
        return self.wire != other

    def __gt__(self, other):
        return self.wire > other

    def __ge__(self, other):
        return self.wire >= other

    def __invert__(self):
        return ~self.wire

    def __getitem__(self, item):
        return self.wire[item]

    def __lshift__(self, other):
        return self.wire << other

    def __rshift__(self, other):
        return self.wire >> other

    def __mod__(self, other):
        return self.wire % other

    def __len__(self):
        return len(self.wire)

    def __enter__(self):
        self.wire.__enter__()

    def __exit__(self, *execinfo):
        self.wire.__exit__(*execinfo)
