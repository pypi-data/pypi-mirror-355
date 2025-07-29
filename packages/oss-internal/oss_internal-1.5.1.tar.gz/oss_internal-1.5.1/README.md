# ALI OSS Upload/Download Package

阿里云 OSS 文件上传下载工具包，支持同步和异步操作，提供文件上传、批量上传、目录上传以及文件下载功能。

## 功能特点

- 支持单个文件上传和下载
- 支持批量文件上传和下载
- 支持目录上传
- 支持同步和异步操作
- 提供上传/下载进度显示
- 完善的错误处理机制

## 安装

```bash
pip install oss-internal
```

## 使用方法

### 1. 文件上传

#### 单个文件上传
```python
from oss_internal import upload_file_to_oss

# 同步上传
file_path = upload_file_to_oss(
    file_path="path/to/local/file.txt",
    ali_access_key_id="your_key",
    ali_access_secret="your_secret",
    oss_origin="oss-cn-hangzhou",
    bucket_name="your-bucket",
    default_prefix="your/prefix"  # 可选
)

# 异步上传
from oss_internal import aupload_file_to_oss
import asyncio

async def upload():
    file_path = await aupload_file_to_oss(
        file_path="path/to/local/file.txt",
        ali_access_key_id="your_key",
        ali_access_secret="your_secret",
        oss_origin="oss-cn-hangzhou",
        bucket_name="your-bucket"
    )

asyncio.run(upload())
```

#### 批量文件上传
```python
from oss_internal import batch_upload_file_to_oss

# 同步批量上传
file_paths = [
    "path/to/file1.txt",
    "path/to/file2.txt",
    "path/to/file3.txt"
]

oss_keys, bucket_name = batch_upload_file_to_oss(
    file_paths=file_paths,
    ali_access_key_id="your_key",
    ali_access_secret="your_secret",
    oss_origin="oss-cn-hangzhou",
    bucket_name="your-bucket"
)

# 异步批量上传
from oss_internal import abatch_upload_file_to_oss

async def batch_upload():
    oss_keys, bucket_name = await abatch_upload_file_to_oss(
        file_paths=file_paths,
        ali_access_key_id="your_key",
        ali_access_secret="your_secret",
        oss_origin="oss-cn-hangzhou",
        bucket_name="your-bucket"
    )

asyncio.run(batch_upload())
```

#### 目录上传
```python
from oss_internal import upload_directory_to_oss

# 同步目录上传
oss_keys, bucket_name = upload_directory_to_oss(
    directory_path="path/to/directory",
    ali_access_key_id="your_key",
    ali_access_secret="your_secret",
    oss_origin="oss-cn-hangzhou",
    bucket_name="your-bucket"
)

# 异步目录上传
from oss_internal import aupload_directory_to_oss

async def upload_dir():
    oss_keys, bucket_name = await aupload_directory_to_oss(
        directory_path="path/to/directory",
        ali_access_key_id="your_key",
        ali_access_secret="your_secret",
        oss_origin="oss-cn-hangzhou",
        bucket_name="your-bucket"
    )

asyncio.run(upload_dir())
```

### 2. 文件下载

#### 单个文件下载
```python
from oss_internal import download_single_file_from_oss

try:
    file_path = download_single_file_from_oss(
        oss_key="path/to/oss/file.txt",
        ali_access_key_id="your_key",
        ali_access_secret="your_secret",
        oss_origin="oss-cn-hangzhou",
        bucket_name="your-bucket",
        temp_dir="/path/to/save"  # 可选，指定下载目录
    )
    print(f"文件下载成功: {file_path}")
except FileNotFoundError as e:
    print(f"文件不存在: {e}")
except Exception as e:
    print(f"下载失败: {e}")
```

#### 批量文件下载
```python
from oss_internal import download_batch_files_from_oss

try:
    file_paths = download_batch_files_from_oss(
        oss_keys=[
            "path/to/file1.txt",
            "path/to/file2.txt",
            "path/to/file3.txt"
        ],
        ali_access_key_id="your_key",
        ali_access_secret="your_secret",
        oss_origin="oss-cn-hangzhou",
        bucket_name="your-bucket",
        temp_dir="/path/to/save"  # 可选，指定下载目录
    )
    print(f"所有文件下载成功: {file_paths}")
except FileNotFoundError as e:
    print(f"没有文件下载成功: {e}")
except FileNotEnoughError as e:
    print(f"部分文件下载成功: {e}")
except Exception as e:
    print(f"下载失败: {e}")
```

### 3. 进度显示

```python
from oss_internal import show_upload_progress, show_download_progress

# 上传时显示进度
upload_file_to_oss(
    file_path="path/to/file.txt",
    ali_access_key_id="your_key",
    ali_access_secret="your_secret",
    oss_origin="oss-cn-hangzhou",
    bucket_name="your-bucket",
    progress_callback=show_upload_progress
)

# 下载时显示进度
download_single_file_from_oss(
    oss_key="path/to/oss/file.txt",
    ali_access_key_id="your_key",
    ali_access_secret="your_secret",
    oss_origin="oss-cn-hangzhou",
    bucket_name="your-bucket",
    progress_callback=show_download_progress
)
```

## 参数说明

### 通用参数
- `ali_access_key_id`: 阿里云 AccessKey ID
- `ali_access_secret`: 阿里云 AccessKey Secret
- `oss_origin`: OSS 服务的地域节点，例如 'oss-cn-hangzhou'
- `bucket_name`: OSS Bucket 的名称
- `internal`: 是否使用内网访问，默认为 True
- `progress_callback`: 进度回调函数，默认为 None

### 上传特有参数
- `file_path`: 本地文件路径
- `default_prefix`: 默认的 OSS 对象前缀路径
- `prefix`: 自定义的 OSS 对象前缀路径

### 下载特有参数
- `oss_key`: OSS 文件 key
- `temp_dir`: 临时目录路径，如果不指定则使用系统临时目录

## 错误处理

包中定义了以下自定义异常：
- `FileNotFoundError`: 文件不存在时抛出
- `FileNotEnoughError`: 批量下载时部分文件下载成功时抛出
- `EmptyDirectoryError`: 目录为空时抛出
- `NotADirectoryError`: 指定路径不是目录时抛出

## 依赖要求

- Python >= 3.11
- aiohappyeyeballs
- aiohttp
- aiosignal
- aliyun-python-sdk-core
- aliyun-python-sdk-kms
- asyncio-oss
- attrs
- certifi
- cffi
- charset-normalizer
- crcmod
- cryptography
- frozenlist
- idna
- jmespath
- multidict
- oss2
- propcache
- pycparser
- pycryptodome
- requests
- six
- tqdm
- urllib3
- yarl

## 许可证

MIT License