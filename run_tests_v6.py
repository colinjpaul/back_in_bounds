#!/usr/bin/env python3
import sys
import time
import traceback
import importlib

# Add current directory to path
sys.path.insert(0, '.')

def run_test_suite():
    print("=" * 70)
    print(" GOLF PERFORMANCE ANALYTICS - CUSTOM TEST RUNNER (PYTEST-STYLE)")
    print("=" * 70)
    print("Scanning 'test_golf_app_v6.py' for test assertions...")
    
    try:
        # Dynamically import the test module
        test_module = importlib.import_module('test_golf_app_v6')
    except Exception as e:
        print(f"\n[\033[91mCRITICAL ERROR\033[0m] Failed to import 'test_golf_app_v6.py':\n")
        traceback.print_exc()
        sys.exit(1)
        
    # Discover all functions starting with 'test_'
    test_functions = [
        attr for attr in dir(test_module) 
        if attr.startswith('test_') and callable(getattr(test_module, attr))
    ]
    
    if not test_functions:
        print("No test functions starting with 'test_' were found.")
        sys.exit(1)
        
    print(f"Discovered {len(test_functions)} automated test cases. Executing suite...\n")
    print("-" * 70)
    
    passed_count = 0
    failed_count = 0
    total_start = time.time()
    
    # Simple fixture emulation
    from test_golf_app_v6 import raw_date_series_with_slashes, mock_arccos_distances, mock_arccos_distances_missing_iron
    fixtures = {
        'raw_date_series_with_slashes': raw_date_series_with_slashes(),
        'mock_arccos_distances': mock_arccos_distances(),
        'mock_arccos_distances_missing_iron': mock_arccos_distances_missing_iron()
    }
    
    for test_name in test_functions:
        test_func = getattr(test_module, test_name)
        
        # Determine fixture arguments needed by the test function
        import inspect
        sig = inspect.signature(test_func)
        args = []
        for param_name in sig.parameters:
            if param_name in fixtures:
                args.append(fixtures[param_name])
            else:
                # If a test requires no fixtures (like callbacks), pass nothing
                pass
                
        # Run the test and record results
        start_time = time.time()
        try:
            test_func(*args)
            duration = (time.time() - start_time) * 1000 # milliseconds
            print(f"[\033[92mPASS\033[0m] {test_name:<50} ({duration:.1f}ms)")
            passed_count += 1
        except AssertionError as ae:
            duration = (time.time() - start_time) * 1000
            print(f"[\033[91mFAIL\033[0m] {test_name:<50} ({duration:.1f}ms)")
            print(f"\n      >>> Assertion Failure in {test_name}:")
            # Print a clean traceback of the assertion line
            tb = sys.exc_info()[2]
            tb_frames = traceback.extract_tb(tb)
            last_frame = tb_frames[-1]
            print(f"          File: {last_frame.filename}, Line {last_frame.lineno}")
            print(f"          Code: {last_frame.line}")
            print(f"          Error: {ae}\n")
            failed_count += 1
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            print(f"[\033[91mERROR\033[0m] {test_name:<50} ({duration:.1f}ms)")
            print(f"\n      >>> Unexpected Exception in {test_name}:")
            traceback.print_exc(file=sys.stdout)
            print()
            failed_count += 1
            
    total_duration = time.time() - total_start
    print("-" * 70)
    print(" TEST EXECUTION SUMMARY")
    print("-" * 70)
    print(f"Total Test Cases Run: {len(test_functions)}")
    print(f"Passed:              \033[92m{passed_count}\033[0m")
    print(f"Failed / Errors:     " + (f"\033[91m{failed_count}\033[0m" if failed_count > 0 else "0"))
    print(f"Total Duration:      {total_duration:.3f} seconds")
    print("=" * 70)
    
    if failed_count > 0:
        sys.exit(1)
    else:
        print("\033[92mSUCCESS: All assertions passed successfully! Perfect code health.\033[0m\n")
        sys.exit(0)

if __name__ == '__main__':
    run_test_suite()
