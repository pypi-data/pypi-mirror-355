"""
This submodule provides functionality for parallelizing image processing.
"""

import multiprocessing as mp


__all__ = ["mp_starmap"]


def _star_wrapper(arg):
    """
    Internal helper function used to allow multiple arguments for functions
    called by `mp_starmap`.
    """
    (func, args) = arg
    return func(*args)


def mp_starmap(func, argss, process_count=None, chunksize=1, pbar_func=None, pbar_kwargs=None):
    """
    Run `func(*argss[0])`, `func(*argss[1])`, ... in parallel and return the
    results as list in the same order.

    This function internally uses `multiprocessing.Pool.map` or
    `multiprocessing.Pool.imap` (depending on whether a progress bar is to be
    used), but supports multiple function arguments (similar to
    `multiprocessing.Pool.starmap`).

    The progress bar function argument `pbar_func` is compatible with `tqdm`,
    i.e. `tqdm.tqdm` (without parentheses!) is a valid choice. If it is `None`,
    no progress bar is used. Optional progress bar keyword arguments (e.g.,
    "unit") can be supplied via the `pbar_kwargs` argument.

    Parameters
    ----------
    func : callable
        The function to apply to each item in `argss`.
    argss : iterable of tuples
        An iterable of tuples containing the arguments to be passed to `func`.
        Each tuple is unpacked and passed to `func` as multiple arguments.
    process_count : int or None, optional
        The number of processes to use. Default is None (which means that the
        number of processes is set to the number of CPU cores available).
    chunksize : int, optional
        The size of the chunks in which to divide the iterable. Default is 1.
        See `multiprocessing.Pool.map` for details.
    pbar_func : callable or None, optional
        The progress bar function to use. If it is `None`, no progress bar is
        used. Default is None. Example: `tqdm.tqdm` (without parentheses).
    pbar_kwargs : dict or None, optional
        Optional keyword arguments to pass to the progress bar function.

    Returns
    -------
    list
        A list of the results of applying `func` to the items in `argss`.

    Notes
    -----
    The order of the returned items is guaranteed to be the same as the order
    of the corresponding input items in `argss`.

    See Also
    --------
    `multiprocessing.Pool.map` : Function used internally if no progress bar should be used.
    `multiprocessing.Pool.imap` : Function used internally if a progress bar should be used.
    """

    argss_for_star_wrapper = tuple((func, args) for args in argss)
    
    with mp.Pool(processes=process_count) as pool:
        if pbar_func is None:
            # case 1: no progress bar
            return pool.map(func=_star_wrapper, iterable=argss_for_star_wrapper, chunksize=chunksize)
        else:
            # case 2: tqdm-compatible progress bar
            results = []
            if pbar_kwargs is None:
                pbar_kwargs = {}
            with pbar_func(total=len(argss), **pbar_kwargs) as pbar:
                for result in pool.imap(func=_star_wrapper, iterable=argss_for_star_wrapper, chunksize=chunksize):
                    pbar.update()
                    results.append(result)
            return results
