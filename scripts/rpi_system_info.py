import platform
import psutil
import subprocess

print("Raspberry Pi Edge Device System Information")
print("=" * 60)
print("OS:", platform.platform())
print("Python:", platform.python_version())
print("Machine:", platform.machine())
print("Processor:", platform.processor())
print("CPU cores:", psutil.cpu_count(logical=True))
print("RAM total GB:", round(psutil.virtual_memory().total / (1024**3), 2))

try:
    print("\nCPU information:")
    print(subprocess.check_output("lscpu", shell=True, text=True))
except Exception as e:
    print("Could not read lscpu:", e)
