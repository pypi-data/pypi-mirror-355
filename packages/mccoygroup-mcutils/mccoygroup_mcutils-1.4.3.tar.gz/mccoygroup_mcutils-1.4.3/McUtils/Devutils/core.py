"""
Provides a set of singleton objects that can declare their purpose a little bit better than None can
"""
import itertools
# import enum
import types

__all__ = [
    "default",
    "is_default",
    "handle_default",
    "uninitialized",
    "is_uninitialized",
    "handle_uninitialized",
    "is_interface_like",
    "is_dict_like",
    "is_list_like",
    "cached_eval",
    "merge_dicts",
    "str_comp",
    "str_is",
    "str_in",
    "str_elide",
    "resolve_key_collision",
    "merge_dicts"
]

class SingletonType:
    """
    A base type for singletons
    """
    __slots__ = []

class DefaultType(SingletonType):
    """
    A type for declaring an argument should use its default value (for when `None` has meaning)
    """
    __is_default__ = True
default=DefaultType()

class UninitializedType(SingletonType):
    """
    A type for declaring an argument should use its default value (for when `None` has meaning)
    """
    __is_uninitialized__ = True
uninitialized = UninitializedType()

def is_interface_like(obj, interface_types, exlusion_types, implementation_attrs):
    return (
            (exlusion_types is None) or
            not isinstance(obj, exlusion_types)
    ) and (
            (interface_types is not None and isinstance(obj, interface_types))
            or all(hasattr(obj, a) for a in implementation_attrs)
    )

def is_dict_like(obj,
                 interface_types=(dict, types.MappingProxyType),
                 exlusion_types=None,
                 implementation_props=('items',)
                 ):
    return is_interface_like(obj, interface_types, exlusion_types, implementation_props)

def is_list_like(obj,
                 interface_types=(list, tuple),
                 exlusion_types=(dict,),
                 implementation_props=('__getitem__',)
                 ):
    return is_interface_like(obj, interface_types, exlusion_types, implementation_props)

def is_default(obj, allow_None=True):
    if allow_None and obj is None:
        return True

    return (
            obj is default
            or isinstance(obj, DefaultType)
            or (hasattr(obj, '__is_default__') and obj.__is_default__)
    )

def handle_default(opt, default_value, allow_None=True):
    if is_default(opt, allow_None=allow_None):
        return default_value
    else:
        return opt

def is_uninitialized(obj, allow_None=True):
    if allow_None and obj is None:
        return True

    return (
            obj is uninitialized
            or isinstance(obj, UninitializedType)
            or (hasattr(obj, '__is_uninitialized__') and obj.__is_uninitialized__)
    )

def handle_uninitialized(opt, initializer, allow_None=True, args=(), kwargs=None):
    if is_uninitialized(opt, allow_None=allow_None):
        return initializer(*args, **({} if kwargs is None else kwargs))
    else:
        return opt


def cached_eval(cache, key, generator, *,
                condition=None,
                args=(),
                kwargs=None):
    condition = (condition is None or condition(key))
    if not condition:
        if kwargs is None: kwargs = {}
        return generator(*args, **kwargs)

    if key in cache:
        return cache[key]

    if kwargs is None: kwargs = {}
    val = generator(*args, **kwargs)
    cache[key] = val

    return val

def str_comp(str_val, test, test_val):
    return isinstance(str_val, str) and test(str_val, test_val)
def str_is(str_val, test_val):
    return isinstance(str_val, str) and str_val == test_val
def str_in(str_val, test_vals):
    return isinstance(str_val, str) and str_val in test_vals
def str_elide(long_str, width=80, placeholder='...'):
    l = len(long_str)
    if l > width:
        total_width = width - len(placeholder)
        l = total_width // 2 + (total_width % 2)
        r = total_width // 2
        long_str = long_str[:l] + placeholder + long_str[-r:]
    return long_str

def resolve_key_collision(a, b, k):
    if is_dict_like(a[k]):
        if not is_dict_like(b[k]):
            raise ValueError(f"can't resolve key collision on key {k} between {a[k]} and {b[k]}")
        return merge_dicts(a[k], b[k], resolve_key_collision)
    elif is_list_like(a[k]):
        if not is_list_like(b[k]):
            return type(a[k])(
                itertools.chain(a[k], b[k])
            )
        else:
            return type(a[k])(
                itertools.chain(a[k], [b[k]])
            )
    else:
        if is_dict_like(b[k]):
            raise ValueError(f"can't resolve key collision on key {k} between {a[k]} and {b[k]}")
        elif is_list_like(b[k]):
            return type(b[k])(
                itertools.chain([a[k]], b[k])
            )
        else:
            return b[k]

def merge_dicts(a, b, collision_handler=None):
    key_inter = a.keys() & b.keys()
    diff_a = a.keys() - key_inter
    diff_b = b.keys() - key_inter
    dd = {k: a[k] for k in diff_a}
    dd.update((k, b[k]) for k in diff_b)
    if len(key_inter) > 0:
        if collision_handler is None:
            collision_handler = resolve_key_collision
        dd.update(
            (k, collision_handler(a, b, k))
            for k in key_inter
        )

    return dd
