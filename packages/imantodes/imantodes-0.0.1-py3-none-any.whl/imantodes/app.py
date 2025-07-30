"""
imantodes: light-weight python code for interactive scivis
Copyright © 2025. University of Chicago
SPDX-License-Identifier: LGPL-3.0-only

app.py:
1) Minimalist way of working with dependency graphs representing the parms
   and internal state of some computational process, to facilitate making
   little "applications".
2) the Widgetish abstract class, which is part of a strategy for removing
   immediate dependency between application logic and widget/window toolkit
"""
# version history
# 2024 Oct 5: initial version

import sys as _sys
import argparse as _argparse
import inspect as _inspect
import textwrap as _textwrap
import collections.abc as _abc

# from copy import deepcopy
import copy

# will need to: pip install frozendict
from frozendict import frozendict as _frozendict
import cffi as _cffi

_ffi = _cffi.FFI()
VERB = 0   # set to 0 to be quiet


def _deep_freeze(thing):
    """Make something really read-only; h/t https://stackoverflow.com/a/66729248/"""
    if thing is None or isinstance(thing, str):
        return thing
    if isinstance(thing, _abc.Mapping):
        return _frozendict({k: _deep_freeze(v) for k, v in thing.items()})
    if isinstance(thing, _abc.Collection):
        return tuple(_deep_freeze(i) for i in thing)
    if not isinstance(thing, _abc.Hashable):
        raise TypeError(f"unfreezable type: '{type(thing)}'")
    # else
    return thing


def parm_spec_freeze(parm_spec):
    """Validate a parm_spec dict, returning a frozen version of it if all ok"""
    if not isinstance(parm_spec, dict):
        raise ValueError(f'Parm spec type {type(parm_spec)} not the expected dict')
    short_names = {}
    for name, spec in parm_spec.items():
        for key in spec:
            if key.startswith('_'):
                allowed = [
                    '_short',
                    '_guitype',
                    '_range',
                    '_noninput',
                ]   # things in a spec allowed to start with '_'
                if not key in allowed:
                    raise KeyError(
                        f"Parm {name=} {key=} starts with '_' but isn't one of: {allowed}"
                    )
        if '_short' in spec:
            short = spec['_short']
            if short in short_names:
                raise ValueError(
                    f"Parm {name=} _short='{short}' same as that of '{short_names[short]}'"
                )
            short_names[short] = name
        for need in ['metavar', 'help']:
            if not need in spec:
                raise KeyError(f"Spec['{name}'] missing required key '{need}'")
        # pairs of things we enforce having exactly one of
        # type vs cls: cls is only way found to get e.g. one Vec3 out of 3 strings
        # default vs required: (like hest) we get a value either way, from user or default
        for oneof in [('type', 'cls', 'tenum'), ('default', 'required')]:
            ins = sum([oo in spec for oo in oneof])
            if ins != 1:
                raise KeyError(f"Spec['{name}'] needs exactly one of {oneof}', not {ins}")
        for betrue in ['required', '_noninput']:
            if betrue in spec and not spec[betrue]:
                raise ValueError(f"Spec['{name}'] has '{betrue}' but it isn't True")
        nmet = ('nargs' in spec) + isinstance(spec['metavar'], tuple)
        if nmet == 2:
            if spec['nargs'] != '*' and spec['nargs'] != len(spec['metavar']):
                raise KeyError(
                    f"Spec['{name}'] nargs={spec['nargs']} != "
                    f"len(metavar)={len(spec['metavar'])}"
                )
        if nmet == 1:
            raise KeyError(
                "Parm specs should have *both* 'nargs' and a tuple-valued "
                f"'metavar', or *neither*. Spec['{name}'] has one of the two."
            )
    # else we got through without any problems
    return _deep_freeze(parm_spec)


def create_cli_parm_parser(desc, parm_spec):
    """Create an argparse parser and add arguments to it so that our parameters
    can be parsed from the command-line"""
    parser = _argparse.ArgumentParser(description=desc)
    for name, _spec in parm_spec.items():
        # ignore (key,value) if key starts with underscore
        spec = {key: val for key, val in _spec.items() if not key.startswith('_')}
        # the 'x' of CLI option '-x' is _spec[_short] if its there, else name
        opt = _spec['_short'] if '_short' in _spec else name
        # seems right to include --name with the more legible longer name,
        # but not obvious that it actually improves usability
        # if '_short' in _spec:
        #    parser.add_argument('-' + opt, '--' + name, **spec)
        # else:
        parser.add_argument('-' + opt, **spec)
    return parser


def create_incr_cli_parm_parser(desc, parm_spec):
    """Create an argparse parser that changes required arguments to non-required,
    with no default values, so that we can parse partial command lines for batch-mode
    scripting, with the only non-None values being those just parsed"""
    parser = _argparse.ArgumentParser(description=f'INCREMENTAL VERSION OF: {desc}')
    for name, _spec in parm_spec.items():
        # HEY lots of copy-pasta from above
        spec = {key: val for key, val in _spec.items() if not key.startswith('_')}
        opt = _spec['_short'] if '_short' in _spec else name
        # previous validation has ensured that we have either required or default,
        # and not both, but we clear both for good measure
        if 'required' in spec:
            del spec['required']
        if 'default' in spec:
            del spec['default']
        parser.add_argument('-' + opt, **spec)
    return parser


def get_parsed_cli_parms(parm_spec, clargs):
    """given the clargs parsed from the command-line by arparse, collect
    in a dict the values for the parameters described in parm_spec"""
    ret = {}
    for name, _spec in parm_spec.items():
        opt = _spec['_short'] if '_short' in _spec else name
        # get value for -opt, and set value of that node in graph
        vl = getattr(clargs, opt)
        if 'cls' in _spec and not isinstance(vl, _spec['cls']):
            # for user-defined types (via cls), value might come out of
            # argparse (e.g. via the default) as something other than that
            # type (e.g. a string), so convert the value now
            vl = _spec['cls'](vl)
        if isinstance(vl, tuple):
            print('get_parsed_cli_parms: HEY WHY did argparse make a tuple?!? making list...')
            vl = list(vl)
        print(f'get_parsed_cli_parms: {opt=}: learned {vl=}')
        ret[name] = vl
    return ret


def list_calc_funcs(mod_name):
    """Help list "calc_" functions, for help instantiating AppState. Returns a
    list of (name, [deps], func) 3-tuples."""
    # Note: ChatGPT helped by demonstrating this use of the "inspect" module
    calcs = [
        func  # functions named "calc_*" defined in module mod_name
        for name, func in _inspect.getmembers(_sys.modules[mod_name], _inspect.isfunction)
        if func.__module__ == mod_name and name.startswith('calc_')
    ]
    # sort functions according to when they appeared in module
    calcs.sort(key=lambda func: _inspect.getsourcelines(func)[1])
    # build up (name, deps, func) tuple list
    ret = []
    for func in calcs:
        node_name = func.__name__.removeprefix('calc_')
        signature = _inspect.signature(func)
        param_names = tuple(param.name for param in signature.parameters.values())
        # ret.append({'name': func.__name__, 'parameters': param_names, 'function': func})
        ret.append((node_name, param_names, func))
    return ret


def _isiter(wut):
    """Test if something is iterable in the way that matters for value updating in a DepNode.
    Needed because weirdly CFFI reports some things as iterable (e.g. struct pointers) that
    are not actually iterable"""
    # HEY why isn't this something like _iscontainer? why necessarily an ordered iterable?
    return (
        not isinstance(wut, str)
        and not isinstance(wut, _ffi.CData)  # HEY what about real[2]???
        and isinstance(wut, _abc.Iterable)
    )


class Changed:   # pylint: disable=too-few-public-methods
    """Tiny wrapper around value (likely a CFFI pointer) to explicitly indicate that
    it should be considered changed, even if the value itself is unchanged."""

    def __init__(self, val):
        self.val = val


class DepNode:
    """One node in dependency graph"""

    def __init__(self, ndict, name, deps, func=None):
        # (LOTS of error checking while we're figuring out how to make this work)
        if not isinstance(ndict, dict):
            raise ValueError(f'ndict {ndict} not a dict')
        if name in ndict:
            raise ValueError(f'name {name} already in node dictionary')
        if not isinstance(deps, list):
            # Yes, sure, it might be more pythonic to not require a list here, but
            # to instead look for something/anything iterable. But considering the
            # places where this is intending to be used: something has gone wrong
            # if we don't get a list for the dependencies and we want to say so.
            raise ValueError(f'deps {deps} not a list')
        for idx, dp in enumerate(deps):
            if not isinstance(dp, type(self)):
                raise ValueError(f'deps[{idx}] "{dp}" is not a {self.__class__.__name__}')
            if name == dp.name:
                raise ValueError(f'own name {name} is included as dependency')
            if not dp in ndict.values():
                raise ValueError(f'dependency {dp.name} not in ndict')
        if deps == [] and func:
            raise ValueError('have no dependencies so did not expected updater func')
        if deps != [] and not func:
            raise ValueError('have dependencies so need an updater func')
        # ... and now finally error checking is done
        # name of this node (e.g. parm name for initial parameters)
        self.name = name
        # value stored at this node
        self._val = None
        # is true when own value has changed (as signal to things depending on us)
        self.flag = False
        # remember list of nodes we depend on
        self.deps = deps[:]
        # the updater function
        self.func = func

    def __repr__(self):
        """string representation of self"""
        ret = f'{self.name} ' + ('^' if self.flag else '_') + f' = {self.val()}'
        if self.deps:
            ret += ' : ' + ', '.join(dep.name for dep in self.deps)
        return ret

    def val(self, vl=None):
        """Get or Set value at this node"""
        if vl is None:
            # caller is getting the value
            return self._val
        # else caller is setting the value
        # unwrap Changed wrapper, if used
        if val_changed := isinstance(vl, Changed):
            vl = vl.val
        if self._val is None:
            # we change value by setting it for the first time (iterable or not)
            self._val = vl
            self.flag = True
            if VERB:
                print(f'   {self.name} has INITIAL value {self._val}')
            return self
        # else self._val has a value already
        isitr = _isiter(vl)
        isitr0 = _isiter(self._val)
        if isitr != isitr0:
            raise ValueError(
                f'{self.name} new val {vl} iterable={isitr} != old {self._val} iterable={isitr0}'
            )
        if isitr:
            ln = len(vl)
            ln0 = len(self._val)
            if ln != ln0:
                raise ValueError(f'{self.name} new val {vl} len={ln} != old {self._val} len={ln0}')
            # HA ha ha we assume that if value is iterable, then it is slice-able!
            # No, that is not true, but, nor is there a simple slice-ability test.
            # So we just barge ahead and try slicing
            self.flag = val_changed or self._val[:] != vl[:]
            if self.flag:
                # by setting the slice this way, the existing compound object called
                # _val is left unchanged and only the values within it are updated
                self._val[:] = vl[:]
        else:
            # value not iterable, just copy it
            self.flag = val_changed or self._val != vl
            if self.flag:
                self._val = vl
        if VERB:
            if self.flag:
                print(
                    f'  {self.name} has '
                    + ('(forcibly) ' if val_changed else '')
                    + f'NEW value {self._val}'
                )
            else:
                print(f'    ({self.name} value {self._val} unchanged)')
        return self

    def update(self):
        """updates the value in node as needed"""
        if not any(dep.flag for dep in self.deps):
            # nothing we depend on has changed, so nothing to do
            return
        if VERB:
            print(
                f'{self.name}.update: deps changed: '
                + ', '.join(dp.name for dp in filter(lambda dp: dp.flag, self.deps))
            )
        # built up arguments to updater function
        kwargs = {dp.name: dp.val() for dp in self.deps}
        # update our own value (which may raise our flag)
        self.val(self.func(**kwargs))
        # (flags will be pulled down later)


class DepGraph:
    """Represents a whole dependency graph"""

    def __init__(self):
        # the collection of nodes, as dict from node name to node object
        self.ndict = {}
        # the topological sort of nodes
        self.nlist = []

    def add(self, name, deps=None, func=None):
        """Adds one node to dependency graph"""
        if deps is None:
            deps = []
        # print(f'DepNode.add: {name=} {deps=} {func=}')
        ret = DepNode(self.ndict, name, deps, func)
        # add new node to node dictionary
        self.ndict[name] = ret
        # facilitate method chaining
        return ret

    # For getting nodes, we blur the line between attributes and items
    def __getattr__(self, name):
        if name in self.ndict:
            return self.ndict[name]
        # else name not known
        raise KeyError(f'"{name}" not known node in graph')

    def __getitem__(self, name):
        return self.__getattr__(name)

    def edges_find(self):
        """Find edges in dependency graph"""
        # (Returning a list, not a set, so that results are deterministic. Python
        # sets give different element ordering everytime they're used, which is
        # principled but extremely confusing for debugging.)
        ret = []
        for name, node in self.ndict.items():
            for dep in node.deps:
                # name depends on dep.name ==> *from* dep.name (src) *to* name (dst)
                ret.append((dep.name, name))
        return ret

    def tsort(self):
        """Finds a topological sort of nodes (sets self.nlist)"""
        # For this implementation of
        # https://en.wikipedia.org/wiki/Topological_sorting#Kahn's_algorithm
        #  - if B depends on A (A is in B.deps),
        #    we initialize a directed edge *from* A *to* B
        #  - the set of edges will be pruned down as they are processed,
        #    but nothing is changed in any nodes's .deps

        edges = self.edges_find()
        # nodes that have no incoming edges, triggering further processing
        todo0 = list(filter(lambda nd: not nd.deps, self.ndict.values()))
        itr = 0   # which iteration of loop (for debugging)
        while todo0:
            itr += 1
            # fmt: off
            if VERB > 1:
                print(f'==== tsort(i {itr}): todo = ', [nd.name for nd in todo0])
                print(f'     tsort(i {itr}): edges = ', edges)
                print(f'     tsort(i {itr}): nlist = ', [nd.name for nd in self.nlist])
            # fmt: on
            todo1 = []
            for nd in todo0:
                # can add n to topo-sorted list
                self.nlist.append(nd)
                src = nd.name
                # eouts = list of all edges (src,_) from src
                # using s=src to quiet pylint https://stackoverflow.com/a/25314665
                eouts = list(filter(lambda ed, sr=src: ed[0] == sr, edges))
                # for dst in all destinations of edges from src
                for dst in map(lambda e: e[1], eouts):
                    edges.remove((src, dst))
                    if VERB > 1:
                        print(f'     {src=} -> {dst=}')
                        print('     and now edges = ', edges)
                    # if there are no edges like (,dst)
                    if not any(map(lambda ed, ds=dst: ed[1] == ds, edges)):
                        todo1.append(self.ndict[dst])
                        if VERB > 1:
                            print(f'    now {todo1=}')
            todo0 = todo1
        # make sure there are no edges (else a cycle?)
        assert not edges
        if VERB > 1:
            nnames = [n.name for n in self.nlist]
            print('==== tsort done: ', nnames)
            print('     checking edges...')
            for edge in self.edges_find():
                si = nnames.index(edge[0])
                di = nnames.index(edge[1])
                print(f'   {edge}: {si},{di}', ' NO! BAD!' if si >= di else '')

    def update(self):
        """Traverses dependency graph, updating as needed"""
        if not self.nlist:
            # oops, haven't learned topological sort yet
            if VERB:
                print('Doing topo sort')
            self.tsort()
        # update all nodes in topological (dependency) order
        for node in self.nlist:
            node.update()
        # pull down all the flags
        for node in self.nlist:
            node.flag = False

    def save_graph(self, fname):
        """Save graph to a .dot file (see https://graphviz.org/ ) for later
        visualization with a separate program like 'dot', e.g.
            dot dag.dot -Tpdf -o dag.pdf"""
        # see also https://www.graphviz.org/pdf/dotguide.pdf
        if not self.nlist:
            self.tsort()
        with open(fname, 'w', encoding='utf-8') as ff:
            parms = []
            for node in self.nlist:
                if not node.deps and '_once' != node.name:
                    parms.append(node.name)
            print(
                f'// dot {fname} -Tpdf -o {fname.removesuffix(".dot")}.pdf',
                file=ff,
            )
            print('digraph G {', file=ff)
            print('  concentrate=true;', file=ff)
            print('  remincross=true;', file=ff)
            print('  rankdir="TB";', file=ff)  # or BT for bottom-to-top
            print('  ranksep="1.3 equally";', file=ff)
            print('  node [ fontname="Courier New" ];', file=ff)
            # print('  edge [  arrowhead="vee" ];', file=ff)
            print('  { rank = source; ' + '; '.join(parms) + '}', file=ff)
            for src, dst in self.edges_find():
                print(f'  {src} -> {dst};', file=ff)   # for BT: {dst} -> {src}
            print('}', file=ff)


class AppState:
    """Contains application state built upon a dependency graph"""

    # _done being False indicates to __setattr__ that __init__ is in progress
    _done = False

    def __init__(self, app_name, parm_spec, parm_val, ndfs):
        self.app_name = app_name
        self.parm_spec = parm_spec
        self.graph = DepGraph()
        # dict mapping from short option name ('-o') to full name ('output')
        self.unshort = {}
        # add special "_once" node with flag raised only once
        self.graph.add('_once')
        self.graph.ndict['_once'].val(1)
        # add first nodes for parameters, and learn unshort
        for name, spec in self.parm_spec.items():
            # no deps or func to set for the parms that start the graph
            self.graph.add(name)
            if '_short' in spec:
                self.unshort[spec['_short']] = name
        self.parm_val0 = parm_val
        self.reset_parms()
        # add nodes for everything downstream of parms
        # lndfs is a list (to enforce given order)
        # of 3-tuples (name, depns, func),
        # where name is a string naming the new node
        # and depns is the list of nodes (by name) it depends on
        for name, depns, func in ndfs:
            # print(f'AppState init:  {name=}   {depns=}   {func=}')
            if not isinstance(depns, tuple) and depns:
                raise ValueError(f'downstream {name} does not actually have dependencies?')
            self.graph.add(name, [self.graph[dpn] for dpn in depns], func)
        # now the new instance variable _done overrides the class variable
        self._done = True

    def command_line(self):
        """Return a command-line to regenerate our current parameter settings"""
        ret = ''
        for name, spec in self.parm_spec.items():
            if '_noninput' in spec:
                # this doesn't contribute to a reproducible command-line invocation
                continue
            # using __getitem__ to get current value of parameter named name
            val = self[name]
            match val:
                case list():
                    ss = ' '.join(map(str, val))
                case kern if (
                    # could be pltKernel, or mprKernel ...
                    str(kern).startswith("<cdata 'struct ")
                    and 'Kernel_t *' in str(kern)
                ):
                    ss = _ffi.string(kern.name).decode('utf8')
                case _:
                    ss = str(val)
            opt = spec['_short'] if '_short' in spec else name
            ret += f' -{opt} {ss}'
        ret = ret[1:]   # lose first space
        ret = ' \\\n'.join(_textwrap.wrap(ret, width=87, break_on_hyphens=False))
        return ret

    def reset_parms(self):
        """Reset parameters to those first passed to our constructor"""
        for name in self.parm_spec:
            vl = self.parm_val0[name]
            if _isiter(vl):
                # without the copy, compound objects referred to in node.val will be
                # exactly the same as those referred to from parm_val0, and we'll
                # end up modifying parm_val0. (GLK initially thought deepcopy was
                # needed here, but probably not?)
                vl = copy.copy(vl)
            self.graph[name].val(vl)
            # We unfortunately have to force the flag up: if visapp interactions are
            # creating changes anywhere downsteam of the input parameters, then the
            # parameters themselves are of course not changing, and so resetting the
            # parameters is also a no-op which does not trigger downstream changes.
            # Forcing the flag up triggers the downstream changes we expect from the
            # parameter reset. Would be interesting to consider having changes to
            # downstream nodes invalidate values in their dependencies, which would
            # remove the need for forcing flag up on *all* parameters.
            self.graph[name].flag = True

    def set_parms(self, parm_val):
        """Set those parameters described in parm_val dict"""
        for name, val in parm_val.items():
            self.graph[name].val(val)

    def update(self):
        """Wrapper around our graph.update"""
        self.graph.update()

    def __setattr__(self, name, value):
        """Allow new attributes during __init__, after that: only be a way to
        set values in the nodes within"""
        if not self._done:
            # self.__init__ is still in progress; pass through
            self.__dict__[name] = value
            return
        # else __init__ is done; now attributes are aliases for nodes
        if not name in self.graph.ndict:
            raise ValueError(f'No node in {self.app_name} named "{name}"')
        # else we can set the node value
        self.graph.ndict[name].val(value)

    def __getattr__(self, name):
        """Handle requests for attributes that don't really exist;
        currently the named nodes within our graph"""
        if not name in self.graph.ndict:
            raise ValueError(f'No node in {self.app_name} named "{name}"')
        # else not an alias
        return self.graph.ndict[name].val()

    # here too we blur line between attribute and value
    def __setitem__(self, name, value):
        return self.__setattr__(name, value)

    def __getitem__(self, name):
        return self.__getattr__(name)

    def run_script(self, fname):
        """Read in script from given filename and run it"""
        incr_parser = create_incr_cli_parm_parser(self.app_name, self.parm_spec)
        with open(fname, 'r', encoding='utf-8') as file:
            for line_nl in file.readlines():  # line_nl = line plus newline
                # ignore anything after '#', lose leading and trailing whitespace
                line = line_nl.split('#', 1)[0].strip()
                # maybe nothing left, in which case go to next line
                if not line:
                    continue
                # parse what is left of line, turn into dict
                args = vars(incr_parser.parse_args(line.split()))
                # drop all the keys for which val is None (i.e. not set in this line)
                args = {nam: val for nam, val in args.items() if not val is None}
                # if needed: unshorten from e.g. 'o' (as in '-o') to name 'output'
                args = {
                    self.unshort[nam] if nam in self.unshort else nam: val
                    for nam, val in args.items()
                }
                print(f'**** run_script: {line=}  -->  {args=}')
                self.set_parms(args)
                self.update()


class Widgetish:
    """Abstract interface or bridge to things that widget toolkits actually do"""

    def resize_plz(self, width: int, height: int):
        # requests changing widget size to given (width, height)
        raise NotImplementedError

    def size_plz(self):
        # return current widget size as list of 2 ints
        raise NotImplementedError

    def repaint_plz(self, **kwargs):
        # repaint self
        raise NotImplementedError

    def close_plz(self):
        # please close (quit) me
        raise NotImplementedError


if __name__ == '__main__':

    def apb(**kwa):
        """example updater"""
        # get all values passed, sum them up
        return sum(kwa.values())

    VERB = 1
    graph = DepGraph()
    A = graph.add('a').val(1)
    B = graph.add('b').val(2)
    C = graph.add('c').val(3)
    D = graph.add('d').val(4)
    U = graph.add('u', [A, C, D], apb)
    S = graph.add('s', [A, B, U], apb)
    T = graph.add('t', [S, D], apb)
    V = graph.add('v', [U, C, T], apb)
    graph.tsort()
    print('topo-sorted: ', [n.name for n in graph.nlist], '\n')
    graph.update()
    print(f'{V.val()=}\n')
    print(f'{V.val=}\n')
    A.val(-1)
    graph.update()
    print(f'{V.val()=}\n')
    print(f'{V.val=}\n')
    A.val(-2)
    C.val(4)
    graph.update()
    print(f'{V.val()=}\n')
    print(f'{V.val=}\n')
