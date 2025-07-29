import asyncio
import time
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.progress_display import (
    show_upload_progress,
    show_download_progress,
    ashow_upload_progress,
    ashow_download_progress
)

def test_sync_progress():
    """测试同步进度显示"""
    print("\n测试同步进度显示:")
    
    # 测试上传进度
    print("\n测试上传进度:")
    total_size = 1024 * 1024  # 1MB
    for i in range(0, total_size, 1024):
        show_upload_progress(i, total_size)
        time.sleep(0.01)  # 模拟上传延迟
    
    # 测试下载进度
    print("\n测试下载进度:")
    for i in range(0, total_size, 1024):
        show_download_progress(i, total_size)
        time.sleep(0.01)  # 模拟下载延迟

async def test_async_progress():
    """测试异步进度显示"""
    print("\n测试异步进度显示:")
    
    # 测试上传进度
    print("\n测试上传进度:")
    total_size = 1024 * 1024  # 1MB
    for i in range(0, total_size, 1024):
        await ashow_upload_progress(i, total_size)
        await asyncio.sleep(0.01)  # 模拟上传延迟
    
    # 测试下载进度
    print("\n测试下载进度:")
    for i in range(0, total_size, 1024):
        await ashow_download_progress(i, total_size)
        await asyncio.sleep(0.01)  # 模拟下载延迟

async def test_concurrent_progress():
    """测试并发进度显示"""
    print("\n测试并发进度显示:")
    
    async def upload_task():
        total_size = 1024 * 1024  # 1MB
        for i in range(0, total_size, 1024):
            await ashow_upload_progress(i, total_size)
            await asyncio.sleep(0.01)
    
    async def download_task():
        total_size = 512 * 1024  # 512KB
        for i in range(0, total_size, 512):
            await ashow_download_progress(i, total_size)
            await asyncio.sleep(0.01)
    
    # 并发执行上传和下载任务
    await asyncio.gather(upload_task(), download_task())

async def main():
    """主测试函数"""
    # 测试同步进度显示
    # test_sync_progress()
    
    # 测试异步进度显示
    await test_async_progress()
    
    # 测试并发进度显示
    await test_concurrent_progress()

if __name__ == "__main__":
    # 运行所有测试
    asyncio.run(main()) 