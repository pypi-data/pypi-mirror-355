import os
try:
    import lz4
except ImportError:
    print("LZ4 module not found. Install it using 'pip install lz4'.")
    os.system("pip install lz4")

import lz4.frame
import tarfile
import io

try:
    import tqdm
except ImportError:
    print("tqdm module not found. Install it using 'pip install tqdm'.")
    os.system("pip install tqdm")

from tqdm import tqdm

def get_unit(total):
    if total >= 1024**3:
        return 'GB', 1024**3
    elif total >= 1024**2:
        return 'MB', 1024**2
    elif total >= 1024:
        return 'KB', 1024
    else:
        return 'B', 1

def fast_compress(input_dir, output_file=None):
    if output_file is None:
        output_file = input_dir + '.tar.lz4'
    tar_buffer = io.BytesIO()
    file_list = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, os.path.dirname(input_dir))
            file_list.append((full_path, rel_path))
    with tarfile.open(fileobj=tar_buffer, mode='w') as tar:
        for full_path, rel_path in tqdm(file_list, desc='Tar', unit='file'):
            tar.add(full_path, arcname=rel_path)
    tar_data = tar_buffer.getvalue()
    total_size = len(tar_data)
    chunk_size = 1024 * 1024
    unit, unit_div = get_unit(total_size)
    with lz4.frame.open(output_file, 'wb') as f, tqdm(total=total_size // unit_div, desc='Write', unit=unit, unit_scale=True) as pbar:
        for i in range(0, total_size, chunk_size):
            f.write(tar_data[i:i+chunk_size])
            pbar.update(min(chunk_size, total_size - i) // unit_div)
    print(f"Compressed to: {output_file}")

def fast_decompress(input_file, output_dir=None):
    if output_dir is None:
        output_dir = '.'
    with lz4.frame.open(input_file, 'rb') as f:
        tar_data = bytearray()
        chunk_size = 1024 * 1024
        f.seek(0, 2)
        total_size = f.tell()
        f.seek(0)
        unit, unit_div = get_unit(total_size)
        with tqdm(total=total_size // unit_div, desc='Reading', unit=unit, unit_scale=True) as pbar:
            read = 0
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                tar_data.extend(chunk)
                read += len(chunk)
                pbar.update(len(chunk) // unit_div)
    tar_buffer = io.BytesIO(tar_data)
    with tarfile.open(fileobj=tar_buffer, mode='r') as tar:
        members = tar.getmembers()
        for member in tqdm(members, desc='Extracting', unit='file'):
            tar.extract(member, output_dir)
    print(f"Decompressed to: {os.path.join(output_dir, os.path.basename(input_file).replace('.tar.lz4', ''))}")

if __name__ == "__main__":
    ### Example usage
    input_directory = "__pycache__"
    fast_compress(input_directory)
    output_lz4_file = input_directory + '.tar.lz4'
    fast_decompress(output_lz4_file, output_dir='decompressed_output')
    # or
    # fast_decompress(output_lz4_file) # Default to current directory
    