"""
AuctioNation2 multiprocessing resources.
"""

from multiprocessing import Process, Pool
from typing import Callable


class MultiprocessManager:
    """
    Static class to contain multiprocessing-oriented functions.
    """

    @staticmethod
    def mark(func):
        """
            Decorator to mark a func to be handled using multiprocessing.

        """
        def wrapper(*args, **kwargs):

            p = Process(
                target=func,
                args=(args),
                kwargs=(kwargs)
            )

            p.start()

        return wrapper


    @staticmethod
    def compute_reads(
        func1:  Callable,
        func2:  Callable, 
        func3:  Callable, 
        func4:  Callable, 
        data:   list
    ):
        pool = Pool()

        result_dict = {
            'lowest':   None,
            'mean':     None,
            'median':   None,
            'count':    None
        }

        def lowest(result):
            result_dict['lowest'] = result

        def mean(result):
            result_dict['mean'] = result
        
        def median(result):
            result_dict['median'] = result
        
        def count(result):
            result_dict['count'] = result


        for target_callback, func in (
            (lowest,  func1),
            (mean,    func2),
            (median,  func3),
            (count,   func4)
        ):
            pool.apply_async(
                func=       func,
                args=       (data,),
                callback=   target_callback
            )

        pool.close()
        pool.join()

        return result_dict
