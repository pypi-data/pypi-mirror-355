# LAM
LAM is a data transformation tool designed for Laminar's API integration platform.

## Overview
LAM enables you to write efficient transformations for your API data using either JavaScript (Bun) or Python. It's designed to be secure, fast, and easy to integrate into your Laminar workflows.

## Features
- **Dual Engine Support**: Choose between JavaScript (Bun runtime) for fast execution or Python for complex data processing
- **Built-in Libraries**: Access lodash and date-fns in JavaScript, comprehensive Python standard library modules
- **Security**: Runs in sandboxed environments with strict resource limits and security restrictions
- **Performance**: Uses Bun runtime for JavaScript and sandboxed Python interpreter
- **Monitoring**: Built-in execution statistics and error tracking

## Execution Environments

### Bun JavaScript Runtime (js)
**Configuration**:
- **Engine**: Bun
- **Timeout**: 5 seconds
- **Execution**: Isolated with `--no-fetch --smol --silent` flags
- **Storage**: No localStorage/sessionStorage support
- **Modules**: Shared node_modules directory

**Available Libraries**:
- **lodash** (^4.17.21): Utility library for array/object manipulation, data transformations (Global: `_`)
- **date-fns** (^2.30.0): Modern date utility library with `format`, `parseISO` functions

**Transform Function Signature**:
```js
(input) => { /* transform logic */ return result; }
```

### Python Interpreter with Sandboxing (py)
**Configuration**:
- **Engine**: Python interpreter
- **Timeout**: 5 seconds
- **Memory Limit**: 100MB
- **CPU Limit**: 5 seconds (RLIMIT_CPU)
- **Virtual Memory**: 100MB (RLIMIT_AS)
- **Execution**: Isolated with `-I` flag (ignores environment/site packages)

**Security Restrictions**:
- **Blocked Modules**: subprocess, sys, os, shutil, pathlib, importlib, builtins, _thread, ctypes, socket, pickle, multiprocessing
- **Blocked Functions**: __import__, eval, exec, globals, locals, getattr, setattr, delattr, compile, open
- **Blocked Patterns**: __subclasses__, dunder attributes access

**Available Standard Library Modules**:
- **json**: JSON encoder and decoder
- **datetime**: Date and time handling
- **time**: Time-related functions
- **math**: Mathematical functions and constants
- **statistics**: Statistical functions (mean, median, mode, standard deviation)
- **collections**: Counter, defaultdict, OrderedDict, deque
- **itertools**: Efficient looping, combinations, permutations
- **functools**: reduce, partial, lru_cache
- **re**: Regular expression operations
- **copy**: Shallow and deep copy operations
- **decimal**: Precise decimal calculations
- **csv**: CSV file reading and writing
- **io**: StringIO, BytesIO for in-memory files
- **dataclasses**: Data classes for storing data
- **typing**: Type hints support
- **enum**: Support for enumerations
- **random**: Random number generation
- **uuid**: UUID generation
- **hashlib**: Secure hash and message digest algorithms
- **base64**: Base64 encoding and decoding
- **urllib**: URL handling modules
- **urllib.parse**: URL parsing utilities
- **html**: HTML processing utilities
- **xml**: XML processing
- **xml.etree**: XML ElementTree API
- **xml.etree.ElementTree**: XML parsing and creation
- **string**: String constants and classes
- **textwrap**: Text wrapping and filling
- **operator**: Standard operators as functions
- **bisect**: Array bisection algorithm
- **heapq**: Heap queue algorithm
- **array**: Efficient arrays of numeric values
- **unicodedata**: Unicode character database
- **locale**: Internationalization services
- **calendar**: Calendar-related functions
- **zoneinfo**: Time zone support (Python 3.9+)
- **struct**: Pack and unpack binary data
- **binascii**: Binary/ASCII conversions
- **codecs**: Encode and decode data
- **difflib**: Sequence comparison utilities
- **pprint**: Pretty-printer for data structures
- **reprlib**: Alternate repr() implementation
- **abc**: Abstract base classes
- **contextlib**: Context management utilities
- **secrets**: Cryptographically secure random numbers
- **fractions**: Rational numbers
- **numbers**: Numeric abstract base classes

**Safe Built-in Functions**:
`abs`, `all`, `any`, `bool`, `chr`, `dict`, `divmod`, `enumerate`, `filter`, `float`, `format`, `frozenset`, `hash`, `hex`, `int`, `isinstance`, `issubclass`, `iter`, `len`, `list`, `map`, `max`, `min`, `next`, `oct`, `ord`, `pow`, `print`, `range`, `repr`, `reversed`, `round`, `set`, `slice`, `sorted`, `str`, `sum`, `tuple`, `type`, `zip`

**Transform Function Signature**:
```py
def transform(input_data):
    # transform logic
    return result
```

## Examples

### JavaScript (Bun) Transformations
Perfect for fast data manipulation with familiar syntax:

```javascript
(input) => {
    // Use lodash for data manipulation
    const processed = _.map(input.data, item => ({
        id: item.id,
        formattedDate: format(parseISO(item.date), 'MMM dd, yyyy'),
        value: item.value * 2
    }));

    return {
        processed,
        summary: {
            total: _.sumBy(processed, 'value'),
            count: processed.length
        }
    };
}
```

### Python Transformations
Ideal for complex data processing and statistical analysis:

```python
def transform(input_data):
    import statistics
    from collections import Counter
    
    # Process numerical data
    values = [item["value"] for item in input_data["data"] if "value" in item]
    
    return {
        "statistics": {
            "mean": statistics.mean(values) if values else 0,
            "median": statistics.median(values) if values else 0,
            "count": len(values)
        },
        "frequency": dict(Counter(item["category"] for item in input_data["data"])),
        "processedAt": datetime.now().isoformat()
    }
```

## Integration with Laminar
LAM is designed to work seamlessly with Laminar's integration platform:

1. **Flows**: Add data transformations to your API flows
2. **Automation**: Schedule and automate data processing
3. **Monitoring**: Track execution statistics and errors

## Getting Started

### Using LAM in Laminar
1. Create a new flow in [Laminar](https://app.laminar.run)
2. Add a transformation step
3. Choose your engine (JavaScript or Python)
4. Write your transformation function
5. Deploy and monitor

## Resources
- [Laminar Documentation](https://docs.laminar.run)
- [Sign up for Laminar](https://app.laminar.run)

## Support
Get help with LAM:
- [Contact Support](mailto:connect@laminar.run)