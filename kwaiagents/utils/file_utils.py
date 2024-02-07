import hashlib
import os
def calculate_file_name_md5(filename):
    """
    Calculate a string's MD5 hash.

    :param input_string: The string to calculate MD5 hash.
    :return: The MD5 hash of the string.
    """
    md5 = hashlib.md5()
    md5.update(filename.encode())
    return md5.hexdigest()

def calculate_file_hash(filename, algorithm='sha256'):
    """
    Calculate a file's hash.

    :param filename: The path to the file.
    :param algorithm: The hash algorithm to use. Default is sha256.
    :return: The file's hash.
    """
    hash_algorithm = hashlib.new(algorithm)
    with open(filename, 'rb') as f:
        while chunk := f.read(8192):
            hash_algorithm.update(chunk)
    return hash_algorithm.hexdigest()


#遍历文件夹的所有文件
def traverse_files_in_directory(directory):
    """
    Traverse all files in a directory.

    :param directory: The directory to traverse.
    :return: None
    """
    fp = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            fp.append(os.path.join(root, file))
    return fp
