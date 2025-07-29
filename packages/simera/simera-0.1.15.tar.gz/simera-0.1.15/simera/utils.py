from collections import defaultdict, deque
import numpy as np
import re
from time import perf_counter
import sys
from types import ModuleType, FunctionType


class DataInputError(Exception):
    """Exception raised for errors in Excel file input.

    Attributes:
        message (str): Description of the error.
        solution (str, optional): Essence of how to solve the error.
        file_path (str, optional): The file path of the Excel document.
        sheet_name (str, optional): The worksheet where the error occurred.
        column (str, optional): The column that caused the issue.
        values (list, optional): The specific values that generated the error.
    """

    def __init__(self, message, solution=None, file_path=None, sheet_name=None, column=None, values=None):
        super().__init__(message)
        self.solution = solution
        self.file_path = file_path
        self.sheet_name = sheet_name
        self.column = column
        self.values = values

    def __str__(self):
        details = [
            f"Solution: {self.solution}" if self.solution else None,
            f"File:     {self.file_path}" if self.file_path else None,
            f"Sheet:    {self.sheet_name}" if self.sheet_name else None,
            f"Column:   {self.column}" if self.column else None,
            f"Values:   {self.values}" if self.values else None
        ]
        details_str = "\n".join(filter(None, details))  # Remove None values
        return f"\n{'-'*28}\n{self.args[0]}\n{details_str}\n{'-'*28}" if details_str else self.args[0]


def standardize_ratio_key(x: str):
    """
    Converts ratio key into a standardized format 'x/y'.
    Allowed inputs (where x and y are any of value units of measurement):
    'x per y', 'xpery', 'x/y', x / y'

    Examples:
    >>> standardize_ratio_key('m3 per lb')
    'm3/lb'
    >>> standardize_ratio_key('m3 / kg')
    'm3/kg'

    :param x: The ratio key as string. Exmaple: m3 per lb, kg/pal.
    :type x: str
    :return: A standardized ratio string.
    :rtype: str
    """
    return str(x).replace('per', '/').replace(' ', '')


def standardize_ratio_key_is_valid(ratio_key):
    return bool(re.match(r'^[^/]+/[^/]+$', ratio_key))


def compute_all_conversions_between_units_in_ratios(ratios, include_self=True, keep_none=True):
    """
    Generate a dictionary containing conversion ratios between all pairs of units.

    Parameters:
    - ratios (dict): Dictionary of direct conversion ratios with keys in the form 'unit_a/unit_b'.
    Input conventions for ratios: 'x/y' or 'x / y', 'x per y'
    - keep_none (bool): If True, include pairs with no possible conversion as None; if False, exclude them.
    - include_self (bool): If True, include ratios of units to themselves (always 1); if False, exclude them.

    Returns:
    - dict: Nested dictionary of conversion ratios.

    Example1:
    >>> ratios = {'kg/m3': 200}
    >>> compute_all_conversions_between_units_in_ratios(ratioss, keep_none=True)
    {'kg': {'kg': 1, 'm3': 200}, 'm3': {'kg': 0.005, 'm3': 1}}
    >>> ratios = {'kg/m3': 200}
    >>> compute_all_conversions_between_units_in_ratios(ratioss, keep_none=True, include_self=False)
    {'kg': {'m3': 200}, 'm3': {'kg': 0.005}}

    Example2:
    >>> ratios = {'kg/m3': 200, 'ol per ol': 1}
    >>> compute_all_conversions_between_units_in_ratios(ratios, keep_none=True)
    {'kg': {'kg': 1, 'm3': 200, 'ol': None},
     'm3': {'kg': 0.005, 'm3': 1, 'ol': None},
     'ol': {'kg': None, 'm3': None, 'ol': 1}}
    >>> compute_all_conversions_between_units_in_ratios(ratios, keep_none=False)
    {'kg': {'kg': 1, 'm3': 200},
     'm3': {'kg': 0.005, 'm3': 1},
     'ol': {'ol': 1}}

    Example3:
    >>> ratios = {'kg per m3': 200, 'm3 per pal': 1.5, 'eur per pln': 0.25}
    >>> compute_all_conversions_between_units_in_ratios(ratios, keep_none=False)
    {'eur': {'eur': 1, 'pln': 0.25},
     'kg': {'kg': 1, 'm3': 200, 'pal': 300.0},
     'm3': {'kg': 0.005, 'm3': 1, 'pal': 1.5},
     'pal': {'kg': 0.00333, 'm3': 0.6666, 'pal': 1},
     'pln': {'eur': 4.0, 'pln': 1}}
    """
    conversions = defaultdict(dict)

    # Populate direct conversions
    for ratio, value in ratios.items():
        ratio = standardize_ratio_key(ratio)  # Remove per and spaces
        unit_a, unit_b = ratio.split('/')
        if value is not None and value is not np.nan:
            conversions[unit_a][unit_b] = value
            conversions[unit_b][unit_a] = 1 / value

    units = set(conversions.keys())

    # Use BFS to find indirect conversions
    def find_ratio(start, end):
        if start == end:
            return 1
        visited = set()
        queue = deque([(start, 1)])

        while queue:
            current, acc_ratio = queue.popleft()
            if current == end:
                return acc_ratio
            visited.add(current)

            for neighbor, neighbor_ratio in conversions[current].items():
                if neighbor not in visited:
                    queue.append((neighbor, acc_ratio * neighbor_ratio))

        return None

    # Create full conversion dictionary
    result = defaultdict(dict)
    for unit_from in units:
        for unit_to in units:
            if not include_self and unit_from == unit_to:
                continue
            ratio = find_ratio(unit_from, unit_to)
            if keep_none or ratio is not None:
                result[unit_from][unit_to] = ratio

    return dict(result)


def console_msg(msg=None, execution_time=True):
    """Prints in console info about executed function.

    This decorator accepts arguments and thus requires execution with @printout().
    Arguments:
    - msg: short statement of what is happening. If None, name of function is used.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            print('\n', end='')
            title = msg if msg else f"Running function: <{func.__name__}>"
            print(f'= {title} '.ljust(80, '='))
            time_start = perf_counter()
            func_output = func(*args, **kwargs)
            if execution_time:
                print(f'Execution time: {perf_counter() - time_start:0.1f}sec.')
            print('-' * 80)
            return func_output
        return wrapper
    return decorator

def deep_sizeof(obj, seen=None):
    """Recursively calculates and returns human-readable size of an object."""
    def _sizeof(o, seen_ids):
        size = sys.getsizeof(o)
        obj_id = id(o)
        if obj_id in seen_ids:
            return 0
        seen_ids.add(obj_id)

        if isinstance(o, (str, bytes, bytearray, ModuleType, FunctionType)):
            return size

        if isinstance(o, dict):
            size += sum(_sizeof(k, seen_ids) + _sizeof(v, seen_ids) for k, v in o.items())
        elif isinstance(o, (list, tuple, set, frozenset)):
            size += sum(_sizeof(i, seen_ids) for i in o)

        return size

    if seen is None:
        seen = set()
    size_bytes = _sizeof(obj, seen)

    # Format human-readable size
    for unit in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"