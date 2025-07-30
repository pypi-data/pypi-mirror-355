import queue
import threading


def worker(task_queue):
    """
    线程执行的工作函数，从任务队列中获取任务并执行。

    :param task_queue: 包含任务函数的队列。
    """
    while True:
        task = task_queue.get()
        if task is None:  # 终止信号
            break
        try:
            task()  # 执行任务
        finally:
            task_queue.task_done()


def run_multithreaded(tasks, thread_num):
    task_queue = queue.Queue()

    for task in tasks:
        task_queue.put(task)

    threads = []
    for _ in range(thread_num):
        thread = threading.Thread(target=worker, args=(task_queue,))
        thread.start()
        threads.append(thread)  # 这个是为了循环Thread().join()

    # 等待所有任务完成
    task_queue.join()

    # 发送终止信号
    for _ in range(thread_num):
        task_queue.put(None)

    # 等待所有线程退出
    for thread in threads:  # 就是上面用到的
        thread.join()
