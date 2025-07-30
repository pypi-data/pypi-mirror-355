import time
import functools

class Profiler:
    def __init__(self):
        self.results = {}

    def measure(self, func_name=None):
        """
        A decorator to measure the execution time of a function.
        Results are stored in the 'results' dictionary.
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                name = func_name or func.__name__
                start_time = time.perf_counter()
                result = func(*args, **kwargs)
                end_time = time.perf_counter()
                execution_time = (end_time - start_time) * 1000  # in milliseconds
                
                self.results[name] = f"{execution_time:.4f} ms"
                print(f"Profiled '{name}': {execution_time:.4f} ms")
                
                return result
            return wrapper
        return decorator

    def print_results(self):
        """Prints all stored profiling results."""
        print("\n--- Performance Profile ---")
        if not self.results:
            print("No functions have been profiled yet.")
        else:
            for name, timing in self.results.items():
                print(f"{name}: {timing}")
        print("-------------------------\n")

# Singleton instance
profiler = Profiler() 