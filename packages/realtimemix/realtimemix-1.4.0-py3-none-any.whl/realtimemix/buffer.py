from .utils import *


class BufferPool:
    """
    缓冲池类，用于减少内存分配开销

    通过重用音频缓冲区来避免频繁的内存分配和释放，
    提高音频处理的性能。

    Attributes:
        buffer_size (int): 缓冲区大小（帧数）
        channels (int): 声道数
        pool (deque): 缓冲区池
        _lock (threading.Lock): 线程安全锁
    """

    def __init__(self, buffer_size: int, channels: int, pool_size: int = 8):
        """
        初始化缓冲池

        Args:
            buffer_size (int): 单个缓冲区大小（帧数）
            channels (int): 声道数
            pool_size (int, optional): 池中缓冲区数量. Defaults to 8.

        Example:
            >>> pool = BufferPool(buffer_size=1024, channels=2, pool_size=8)
        """
        self.buffer_size = buffer_size
        self.channels = channels
        self.pool = deque(maxlen=pool_size)
        self._lock = threading.Lock()

        # Pre-allocate buffers
        for _ in range(pool_size):
            self.pool.append(np.zeros((buffer_size, channels), dtype=np.float32))

    def get_buffer(self) -> npt.NDArray[np.float32]:
        """
        从池中获取一个缓冲区

        如果池中有可用的缓冲区，则从池中取出一个并清零。
        如果池为空，则创建新的缓冲区。

        Returns:
            np.ndarray: 清零的音频缓冲区，形状为 (buffer_size, channels)

        Note:
            返回的缓冲区已经被清零，可以直接使用
        """
        try:
            with self._lock:
                if self.pool:
                    buffer = self.pool.popleft()
                    # 验证缓冲区完整性
                    if (
                        buffer.shape != (self.buffer_size, self.channels)
                        or buffer.dtype != np.float32
                    ):
                        logger.warning("Invalid buffer in pool, creating new one")
                        buffer = np.zeros((self.buffer_size, self.channels), dtype=np.float32)
                    else:
                        # 确保缓冲区被正确清零
                        buffer.fill(0.0)
                        # 验证没有NaN或Inf值
                        if np.any(np.isnan(buffer)) or np.any(np.isinf(buffer)):
                            logger.warning("Corrupted buffer detected, replacing")
                            buffer = np.zeros((self.buffer_size, self.channels), dtype=np.float32)
                    return buffer
        except Exception as e:
            logger.error(f"Error accessing buffer pool: {e}")

        # Pool is empty or error occurred, create new buffer
        try:
            return np.zeros((self.buffer_size, self.channels), dtype=np.float32)
        except Exception as e:
            logger.error(f"Failed to create new buffer: {e}")
            # 最后的紧急措施
            return np.zeros((1024, 2), dtype=np.float32)  # 使用默认大小

    def return_buffer(self, buffer: npt.NDArray[np.float32]) -> None:
        """
        将缓冲区返回到池中

        Args:
            buffer (np.ndarray): 要返回的缓冲区

        Note:
            如果池已满，缓冲区将被丢弃（让垃圾收集器处理）
        """
        try:
            # 验证缓冲区有效性
            if (
                buffer is None
                or buffer.shape != (self.buffer_size, self.channels)
                or buffer.dtype != np.float32
            ):
                logger.debug("Invalid buffer returned, discarding")
                return

            # 检查数据完整性
            if np.any(np.isnan(buffer)) or np.any(np.isinf(buffer)):
                logger.debug("Corrupted buffer returned, discarding")
                return

            with self._lock:
                if len(self.pool) < self.pool.maxlen:
                    self.pool.append(buffer)
                # 如果池已满，让垃圾收集器处理这个缓冲区
        except Exception as e:
            logger.error(f"Error returning buffer to pool: {e}")
            # 忽略错误，让垃圾收集器处理缓冲区
