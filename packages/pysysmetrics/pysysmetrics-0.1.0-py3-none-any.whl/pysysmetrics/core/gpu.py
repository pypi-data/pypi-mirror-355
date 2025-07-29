import os
import sys
import time
import psutil
import argparse
import platform
from datetime import datetime

try:
    import pynvml
except ImportError:
    print("ModuleNotFoundError: No module named 'pynvml'")
    sys.exit(1)

def get_script_name(pid: int) -> str:
    try:
        process = psutil.Process(pid)
        cmdline = process.cmdline()
        if len(cmdline) > 1:
            return os.path.basename(cmdline[1])
        return "Unknown"
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return "Unknown"


def get_gpu_processes() -> list[dict]:
    gpu_processes = []
    pynvml.nvmlInit()
    device_count = pynvml.nvmlDeviceGetCount()
    for i in range(device_count):
        handle = pynvml.nvmlDeviceGetHandleByIndex(i)
        device_name = pynvml.nvmlDeviceGetName(handle)
        if isinstance(device_name, bytes):
            device_name = device_name.decode()

        try:
            process_infos = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
        except pynvml.NVMLError:
            continue

        for p in process_infos:
            gpu_processes.append({
                "pid": p.pid,
                "name": get_script_name(p.pid),
                "memory_used": p.usedGpuMemory / (1024 ** 2),
                "device_name": device_name
            })

    pynvml.nvmlShutdown()
    return gpu_processes


def print_gpu_processes_info(gpu_processes: list[dict]) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n========================= Refresh @ {timestamp} =========================")
    if not gpu_processes:
        print("No GPU processes currently running.")
        return

    print(f"{'PID':<10}{'Script Name':<30}{'GPU Mem (MB)':<15}{'GPU Mem (GB)':<15}{'GPU Device':<20}")
    print("-" * 90)
    for proc in gpu_processes:
        mb = proc["memory_used"]
        gb = mb / 1024
        print(f"{proc['pid']:<10}{proc['name']:<30}{mb:<15.2f}{gb:<15.2f}{proc['device_name']:<20}")

def print_system_info() -> None:
    try:
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()
        if device_count == 0:
            print("No NVIDIA GPU detected.")
            return
        os_info = f"{platform.system()} {platform.release()}"
        print("-" * 70)
        print("System Information:")
        print(f"Operating System : {os_info}")
        print("-" * 70)
        print("GPU Information:")
        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            name = pynvml.nvmlDeviceGetName(handle)
            if isinstance(name, bytes):
                name = name.decode()
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            total_mem_gb = mem_info.total / (1024 ** 3)
            total_mem_mb = mem_info.total / (1024 ** 2)

            print(f"GPU {i} Model        : {name}")
            print(f"GPU {i} Total Memory : {total_mem_gb:.2f} GB ({total_mem_mb:.0f} MB)")
        print("-" * 70)

        pynvml.nvmlShutdown()
    except pynvml.NVMLError as e:
        print(f"NVML Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Monitor GPU processes.")
    parser.add_argument("interval", type=int, help="Refresh interval in seconds (positive integer)")
    args = parser.parse_args()

    if args.interval <= 0:
        print("Error: Interval must be a positive integer.")
        sys.exit(1)

    system_platform = sys.platform.lower()
    if "darwin" in system_platform:
        print("Error: GPU monitoring is not supported on macOS with pynvml.")
        sys.exit(1)

    try:
        pynvml.nvmlInit()
        pynvml.nvmlShutdown()
    except pynvml.NVMLError:
        print("Error: NVIDIA driver or GPU not detected. Cannot initialize NVML.")
        sys.exit(1)

    print_system_info()

    while True:
        gpu_processes = get_gpu_processes()
        print_gpu_processes_info(gpu_processes)
        print("=" * 70)
        time.sleep(args.interval)

def monitor_gpu_memory(interval: int) -> None:
    if interval <= 0:
        print("Error: Interval must be a positive integer.")
        sys.exit(1)

    system_platform = sys.platform.lower()
    if "darwin" in system_platform:
        print("Error: GPU monitoring is not supported on macOS with pynvml.")
        sys.exit(1)

    try:
        pynvml.nvmlInit()
        pynvml.nvmlShutdown()
    except pynvml.NVMLError:
        print("Error: NVIDIA driver or GPU not detected. Cannot initialize NVML.")
        sys.exit(1)

    print_system_info()

    while True:
        gpu_processes = get_gpu_processes()
        print_gpu_processes_info(gpu_processes)
        print("=" * 70)
        time.sleep(interval)

if __name__ == "__main__":
    main()
