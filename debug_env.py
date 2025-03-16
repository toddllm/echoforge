import sys
import os
import site

print("Python executable:", sys.executable)
print("Python version:", sys.version)
print("\nPython path:")
for p in sys.path:
    print(f"  - {p}")

print("\nSite packages:")
for p in site.getsitepackages():
    print(f"  - {p}")

print("\nTrying to import silentcipher...")
try:
    import silentcipher
    print(f"SUCCESS! silentcipher found at: {silentcipher.__file__}")
    print(f"silentcipher version: {silentcipher.__version__ if hasattr(silentcipher, '__version__') else 'unknown'}")
except ImportError as e:
    print(f"FAILED! Error: {e}")
    
    # Check if the module exists in site-packages
    site_packages = site.getsitepackages()
    for sp in site_packages:
        silentcipher_path = os.path.join(sp, "silentcipher")
        if os.path.exists(silentcipher_path):
            print(f"Found silentcipher directory at {silentcipher_path}, but it couldn't be imported")
            
        # Check for egg/dist info
        for item in os.listdir(sp):
            if "silentcipher" in item.lower():
                print(f"Found silentcipher-related file in site-packages: {item}") 