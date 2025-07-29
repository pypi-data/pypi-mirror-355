

import time
import matplotlib.pyplot as plt
import random
import sys

sys.setrecursionlimit(5000)

def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[0]
    left = [x for x in arr[1:] if x < pivot]
    right = [x for x in arr[1:] if x > pivot]
    return quick_sort(left) + [pivot] + quick_sort(right)

def benchmark():
    sizes = [10, 100, 700, 3000]
    times = []

    for size in sizes:
        arr = list(range(size, 0, -1))
        random.shuffle(arr)
        start = time.time()
        quick_sort(arr)
        end = time.time()
        times.append(end - start)

    plt.plot(sizes, times, marker='o')
    plt.xlabel("Input Size")
    plt.ylabel("Time Taken (seconds)")
    plt.title("Quick Sort Performance")
    plt.show()
