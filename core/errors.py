class RunAborted(RuntimeError):
    """当前任务可能仍在运行，停止后续队列。"""
