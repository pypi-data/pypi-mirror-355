import glob
import os


def get_file_paths(dir_path: str, ext=".cif") -> list[str]:
    """Return a list of file paths with a given extension in the specified
    directory.

    Parameters
    ----------
    dir_path : str
        The path to the directory to search.
    ext : str, optional
        The file extension to look for (default is ".cif").

    Returns
    -------
    list of str
        List of full file paths matching the given extension.

    Examples
    --------
    >>> get_file_paths("/path/to/dir", ext=".cif")
    ['/path/to/dir/sample1.cif', '/path/to/dir/sample2.cif']
    """
    return glob.glob(os.path.join(dir_path, f"*{ext}"))


def contains_file_type(dir_path: str, ext=".cif") -> bool:
    """Check if the specified directory contains at least one file with the
    given extension.

    Parameters
    ----------
    dir_path : str
        The path to the directory to check.
    ext : str, optional
        The file extension to look for (default is ".cif").

    Returns
    -------
    bool
        True if at least one file with the given extension exists
        in the directory, False otherwise.

    Examples
    --------
    >>> contains_file_type("/path/to/dir", ext=".cif")
    True

    >>> contains_file_type("/empty/dir", ext=".txt")
    False
    """
    for file in os.listdir(dir_path):
        if file.endswith(ext) and os.path.isfile(os.path.join(dir_path, file)):
            return True
    return False
