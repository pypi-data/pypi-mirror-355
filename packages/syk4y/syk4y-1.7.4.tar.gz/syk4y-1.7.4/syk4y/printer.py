import sys
import os

try:
    import torch
except ImportError:
    print("PyTorch module not found. Install it using 'pip install torch'.")
    os.system("pip install torch")

try:
    import numpy as np
except ImportError:
    print("NumPy module not found. Install it using 'pip install numpy'.")
    os.system("pip install numpy")

try:
    import pandas as pd
except ImportError:
    print("Pandas module not found. Install it using 'pip install pandas'.")
    os.system("pip install pandas")

import torch
import numpy as np
import pandas as pd

def format_memory_size(size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"

def inspect(
    var,
    prefix: str = "Variable",
    indent: int = 1,
    file=sys.stdout,
    visited=None,
):
    if visited is None:
        visited = set()
    indent_str = "  " * indent
    var_id = id(var)

    if var_id in visited:
        print(f"{indent_str}{prefix}: <Cyclic Reference>", file=file)
        return

    if isinstance(var, (list, tuple, dict, set, frozenset)):
        visited.add(var_id)

    if isinstance(var, torch.Tensor):
        size = var.element_size() * var.nelement()
        print(f"{indent_str}{prefix}: Tensor(shape={tuple(var.shape)}, dtype={str(var.dtype)}, device={str(var.device)}, size={format_memory_size(size)})", file=file)
        return

    if isinstance(var, np.ndarray):
        size = var.nbytes
        print(f"{indent_str}{prefix}: ndarray(shape={var.shape}, dtype={var.dtype}, size={format_memory_size(size)})", file=file)
        return

    if isinstance(var, pd.DataFrame):
        print(f"{indent_str}{prefix}: DataFrame(shape={var.shape}, columns={list(var.columns)})", file=file)
        return

    if isinstance(var, pd.Series):
        print(f"{indent_str}{prefix}: Series(shape={var.shape}, name={var.name})", file=file)
        return

    if isinstance(var, list):
        print(f"{indent_str}{prefix}: List(length={len(var)})", file=file)
        for i, item in enumerate(var):
            inspect(item, f"[{i}]", indent + 1, file, visited)
        return

    if isinstance(var, tuple):
        print(f"{indent_str}{prefix}: Tuple(length={len(var)})", file=file)
        for i, item in enumerate(var):
            inspect(item, f"({i})", indent + 1, file, visited)
        return

    if isinstance(var, dict):
        print(f"{indent_str}{prefix}: Dict(length={len(var)})", file=file)
        for k, v in var.items():
            inspect(v, f"{k!r}", indent + 1, file, visited)
        return

    if isinstance(var, (set, frozenset)):
        print(f"{indent_str}{prefix}: {type(var).__name__}(length={len(var)})", file=file)
        for i, item in enumerate(var):
            inspect(item, f"{{{i}}}", indent + 1, file, visited)
        return

    # Custom class/object: print only keys of __dict__
    if hasattr(var, '__dict__'):
        print(f"{indent_str}{prefix}: Instance of {type(var).__name__} with keys {list(vars(var).keys())}", file=file)
        return

    if isinstance(var, (int, float, bool)):
        print(f"{indent_str}{prefix}: {type(var).__name__} = {var}", file=file)
        return

    if isinstance(var, str):
        if len(var) > 80:
            print(f"{indent_str}{prefix}: str(length={len(var)}) = '{var[:77]}...'", file=file)
        else:
            print(f"{indent_str}{prefix}: str = '{var}'", file=file)
        return

    print(f"{indent_str}{prefix}: {type(var).__name__}", file=file)

if __name__ == "__main__":
    ### Example usage
    ## List
    # sample_data = [
    #     torch.tensor([[1, 2], [3, 4]]),
    #     42,
    #     "hello world",
    #     [torch.tensor([1, 2]), 3, "nested"]
    # ]

    ##  Dictionary
    # sample_data = {
    #     "tensor": torch.tensor([[1, 2], [3, 4]]),
    #     "number": 42,
    #     "text": "hello world",
    #     "nested_list": [torch.tensor([1, 2]), 3, "nested"]
    # }

    ## Tuple
    # sample_data = (
    #     torch.tensor([[1, 2], [3, 4]]),
    #     42,
    #     "hello world",
    #     [torch.tensor([1, 2]), 3, "nested"]
    # )

    ## Pandas DataFrame
    # sample_data = [
    #     pd.DataFrame({
    #         'A': [1, 2, 3],
    #         'B': [4.0, 5.5, 6.1],
    #         'C': ['foo', 'bar', 'baz']
    #     }),
    #     torch.tensor([[1, 2], [3, 4]]),
    #     "Sample text",
    #     [1, 2, 3]
    # ]

    # Pandas Series
    # sample_data = [
    #     pd.Series([1, 2, 3], name='numbers'),
    #     torch.tensor([[1, 2], [3, 4]]),
    #     "Sample text",
    #     [1, 2, 3]
    # ]

    # Numpy Array
    # sample_data = [
    #     np.array([[1, 2], [3, 4]]),
    #     torch.tensor([[1, 2], [3, 4]]),
    #     "Sample text",
    #     [1, 2, 3]
    # ]

    ### Custom Class
    class SampleData:
        def __init__(self, tensor, number, text, nested_list):
            self.tensor = tensor
            self.number = number
            self.text = text
            self.nested_list = nested_list
    sample_data = SampleData(
        tensor=torch.tensor([[1, 2], [3, 4]]),
        number=42,
        text="hello world",
        nested_list=[torch.tensor([1, 2]), 3, "nested"]
    )
    inspect(sample_data, "SampleData")