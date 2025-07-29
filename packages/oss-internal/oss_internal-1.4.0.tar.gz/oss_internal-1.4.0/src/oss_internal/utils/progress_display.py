from tqdm.asyncio import tqdm

def show_upload_progress(consumed_bytes: int, total_bytes: int):
    """
    实时显示上传进度的回调函数。

    Args:
        consumed_bytes (int): 当前已上传的字节数。
        total_bytes (int): 上传总字节数。
    """
    if not hasattr(show_upload_progress, 'pbar'):
        show_upload_progress.pbar = tqdm(total=total_bytes, unit='B', unit_scale=True, desc='Uploading')
    
    if total_bytes:
        show_upload_progress.pbar.update(consumed_bytes - show_upload_progress.pbar.n)
    else:
        show_upload_progress.pbar.update(consumed_bytes - show_upload_progress.pbar.n)
        show_upload_progress.pbar.close()
        delattr(show_upload_progress, 'pbar')

def show_download_progress(consumed_bytes: int, total_bytes: int):
    """
    实时显示下载进度的回调函数。

    Args:
        consumed_bytes (int): 当前已下载的字节数。
        total_bytes (int): 下载总字节数。
    """
    if not hasattr(show_download_progress, 'pbar'):
        show_download_progress.pbar = tqdm(total=total_bytes, unit='B', unit_scale=True, desc='Downloading')
    
    if total_bytes:
        show_download_progress.pbar.update(consumed_bytes - show_download_progress.pbar.n)
    else:
        show_download_progress.pbar.update(consumed_bytes - show_download_progress.pbar.n)
        show_download_progress.pbar.close()
        delattr(show_download_progress, 'pbar')

async def ashow_upload_progress(consumed_bytes: int, total_bytes: int):
    """
    异步实时显示上传进度的回调函数。

    Args:
        consumed_bytes (int): 当前已上传的字节数。
        total_bytes (int): 上传总字节数。
    """
    if not hasattr(show_upload_progress_async, 'pbar'):
        show_upload_progress_async.pbar = tqdm(total=total_bytes, unit='B', unit_scale=True, desc='Uploading')
        show_upload_progress_async._consumed = 0
    
    if show_upload_progress_async.pbar:
        increment = consumed_bytes - show_upload_progress_async._consumed
        if increment > 0:
            show_upload_progress_async.pbar.update(increment)
            show_upload_progress_async._consumed = consumed_bytes
    
    if not total_bytes or consumed_bytes >= total_bytes:
        show_upload_progress_async.pbar.close()
        delattr(show_upload_progress_async, 'pbar')
        delattr(show_upload_progress_async, '_consumed')

async def ashow_download_progress(consumed_bytes: int, total_bytes: int):
    """
    异步实时显示下载进度的回调函数。

    Args:
        consumed_bytes (int): 当前已下载的字节数。
        total_bytes (int): 下载总字节数。
    """
    if not hasattr(show_download_progress_async, 'pbar'):
        show_download_progress_async.pbar = tqdm(total=total_bytes, unit='B', unit_scale=True, desc='Downloading')
        show_download_progress_async._consumed = 0
    
    if show_download_progress_async.pbar:
        increment = consumed_bytes - show_download_progress_async._consumed
        if increment > 0:
            show_download_progress_async.pbar.update(increment)
            show_download_progress_async._consumed = consumed_bytes
    
    if not total_bytes or consumed_bytes >= total_bytes:
        show_download_progress_async.pbar.close()
        delattr(show_download_progress_async, 'pbar')
        delattr(show_download_progress_async, '_consumed')
