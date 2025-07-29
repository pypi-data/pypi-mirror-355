import os
import tempfile
import oss2

from typing import List

from .schemas.error import FileNotEnoughError

def download_single_file_from_oss(oss_key: str,
                                ali_access_key_id: str,
                                ali_access_secret: str,
                                oss_origin: str,
                                bucket_name: str,
                                internal: bool = True,
                                temp_dir: str = '') -> str:
    """
    从 OSS 下载单个文件到临时目录
    
    Args:
        oss_key (str): OSS文件key
        ali_access_key_id (str): 阿里云 AccessKey ID，用于认证
        ali_access_secret (str): 阿里云 AccessKey Secret，用于认证
        oss_origin (str): OSS 服务的地域节点，例如 'oss-cn-hangzhou'
        bucket_name (str): OSS Bucket 的名称
        internal (bool, optional): 是否使用内网访问，默认为 True
        temp_dir (str, optional): 临时目录路径，如果不指定则使用系统临时目录
        
    Returns:
        str: 下载文件的路径
        
    Raises:
        ValueError: 当必要的参数为空时抛出
        FileNotFoundError: 当OSS文件不存在时抛出
        Exception: 当下载过程中发生其他错误时抛出
    """
    if not all([ali_access_key_id, ali_access_secret, oss_origin, bucket_name]):
        raise ValueError("ali_access_key_id, ali_access_secret, oss_origin, bucket_name 不能为空")
    
    # 设置OSS端点
    oss_endpoint = f"https://{oss_origin}-internal.aliyuncs.com" if internal else f"https://{oss_origin}.aliyuncs.com"
    oss_auth = oss2.Auth(ali_access_key_id, ali_access_secret)
    bucket = oss2.Bucket(oss_auth, oss_endpoint, bucket_name)
    
    # 如果没有指定临时目录，使用系统临时目录
    if not temp_dir:
        temp_dir = tempfile.mkdtemp()
    elif not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    try:
        file_path = os.path.join(temp_dir, os.path.basename(oss_key))
        try:
            bucket.get_object_to_file(oss_key, file_path)
            return file_path
        except oss2.exceptions.NoSuchKey:
            raise FileNotFoundError(f"OSS文件不存在: {oss_key}")
            
    except oss2.exceptions.OssError as e:
        raise Exception(f"OSS操作失败: {str(e)}")
    except Exception as e:
        raise Exception(f"下载过程发生错误: {str(e)}")

def download_batch_files_from_oss(oss_keys: List[str],
                                ali_access_key_id: str,
                                ali_access_secret: str,
                                oss_origin: str,
                                bucket_name: str,
                                internal: bool = True,
                                temp_dir: str = '') -> List[str]:
    """
    从 OSS 批量下载文件到临时目录
    
    Args:
        oss_keys (List[str]): OSS文件key列表
        ali_access_key_id (str): 阿里云 AccessKey ID，用于认证
        ali_access_secret (str): 阿里云 AccessKey Secret，用于认证
        oss_origin (str): OSS 服务的地域节点，例如 'oss-cn-hangzhou'
        bucket_name (str): OSS Bucket 的名称
        internal (bool, optional): 是否使用内网访问，默认为 True
        temp_dir (str, optional): 临时目录路径，如果不指定则使用系统临时目录
        
    Returns:
        List[str]: 成功下载的文件路径列表
        
    Raises:
        ValueError: 当必要的参数为空时抛出
        FileNotFoundError: 当没有文件成功下载时抛出
        Exception: 当下载过程中发生其他错误时抛出
    """
    if not all([ali_access_key_id, ali_access_secret, oss_origin, bucket_name]):
        raise ValueError("ali_access_key_id, ali_access_secret, oss_origin, bucket_name 不能为空")
    
    if not isinstance(oss_keys, list):
        raise ValueError(f"oss_keys 必须是列表类型，当前类型: {type(oss_keys)}")
    
    # 设置OSS端点
    oss_endpoint = f"https://{oss_origin}-internal.aliyuncs.com" if internal else f"https://{oss_origin}.aliyuncs.com"
    oss_auth = oss2.Auth(ali_access_key_id, ali_access_secret)
    bucket = oss2.Bucket(oss_auth, oss_endpoint, bucket_name)
    
    # 如果没有指定临时目录，使用系统临时目录
    if not temp_dir:
        temp_dir = tempfile.mkdtemp()
    elif not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    try:
        downloaded_files = []
        for key in oss_keys:
            if not isinstance(key, str):
                raise ValueError(f"无效的OSS key类型: {type(key)}")
            
            file_path = os.path.join(temp_dir, os.path.basename(key))
            try:
                bucket.get_object_to_file(key, file_path)
                downloaded_files.append(file_path)
            except oss2.exceptions.NoSuchKey:
                continue
            
        if not downloaded_files:
            raise FileNotFoundError("没有成功下载任何文件")
        
        elif len(downloaded_files)!=len(oss_keys):
            raise FileNotEnoughError(f"部分文件下载成功，查看路径:{temp_dir}")

        return downloaded_files
            
    except oss2.exceptions.OssError as e:
        raise Exception(f"OSS操作失败: {str(e)}")
    except Exception as e:
        raise Exception(f"下载过程发生错误: {str(e)}")