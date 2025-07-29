import oss2
import asyncio_oss

def generate_signed_url(oss_key: str, 
                        ali_access_key_id: str = None,
                        ali_access_secret: str = None,
                        oss_origin: str = None,
                        bucket_name: str = None,
                        internal: bool = True,
                        expire_seconds: int = 300) -> str:
    """
    生成阿里云 OSS 对象的签名访问 URL（临时有效）。

    Args:
        oss_key (str): OSS 对象的 Key（路径）
        ali_access_key_id (str, optional): 阿里云 AccessKey ID，用于认证
        ali_access_secret (str, optional): 阿里云 AccessKey Secret，用于认证
        oss_origin (str, optional): OSS 服务的地域节点，例如 'oss-cn-hangzhou'
        bucket_name (str, optional): OSS Bucket 的名称
        internal (bool, optional): 是否使用内网访问，默认为 True。True 使用内网域名，False 使用公网域名
        expire_seconds (int, optional): 签名链接的有效时长，单位为秒，默认 5 分钟

    Returns:
        str: 签名后的访问 URL

    Raises:
        ValueError: 当必要的参数（ali_access_key_id, ali_access_secret, oss_origin, bucket_name）为空时抛出
        RuntimeError: 当签名 URL 生成失败时抛出

    Example:
        >>> ALI_ACCESS_KEY_ID = 'your_access_key_id'
        >>> ALI_ACCESS_SECRET = 'your_access_secret'
        >>> OSS_ORIGIN = 'oss-cn-beijing'
        >>> BUCKET_NAME = 'your-bucket'
        >>> signed_url = generate_signed_url(
        ...     oss_key="test.txt",
        ...     ali_access_key_id=ALI_ACCESS_KEY_ID,
        ...     ali_access_secret=ALI_ACCESS_SECRET,
        ...     oss_origin=OSS_ORIGIN,
        ...     bucket_name=BUCKET_NAME
        ... )
    """
    if not all([ali_access_key_id, ali_access_secret, oss_origin, bucket_name]):
        raise ValueError("ali_access_key_id, ali_access_secret, oss_origin, bucket_name 不能为空")
    
    endpoint = f"https://{oss_origin}-internal.aliyuncs.com" if internal else f"https://{oss_origin}.aliyuncs.com"
    auth = oss2.Auth(ali_access_key_id, ali_access_secret)
    bucket = oss2.Bucket(auth, endpoint, bucket_name=bucket_name)

    try:
        signed_url = bucket.sign_url("GET", oss_key, expire_seconds)
        return signed_url
    except Exception as e:
        raise RuntimeError(f"签名 URL 生成失败：{e}")

async def agenerate_signed_url(oss_key: str,
                               ali_access_key_id: str,
                               ali_access_secret: str,
                               oss_origin: str,
                               bucket_name: str,
                               internal: bool = True,
                               expire_seconds: int = 300) -> str:
    """
    异步生成阿里云 OSS 对象的签名访问 URL（临时有效）。

    Args:
        oss_key (str): OSS 对象的 Key（路径）
        ali_access_key_id (str): 阿里云 AccessKey ID，用于认证
        ali_access_secret (str): 阿里云 AccessKey Secret，用于认证
        oss_origin (str): OSS 服务的地域节点，例如 'oss-cn-hangzhou'
        bucket_name (str): OSS Bucket 的名称
        internal (bool, optional): 是否使用内网访问，默认为 True。True 使用内网域名，False 使用公网域名
        expire_seconds (int, optional): 签名链接的有效时长，单位为秒，默认 5 分钟

    Returns:
        str: 签名后的访问 URL

    Raises:
        ValueError: 当必要的参数为空时抛出
        RuntimeError: 当签名 URL 生成失败时抛出
    """
    if not all([ali_access_key_id, ali_access_secret, oss_origin, bucket_name]):
        raise ValueError("ali_access_key_id, ali_access_secret, oss_origin, bucket_name 不能为空")
    oss_endpoint = f"https://{oss_origin}-internal.aliyuncs.com" if internal else f"https://{oss_origin}.aliyuncs.com"
    oss_auth = oss2.Auth(ali_access_key_id, ali_access_secret)
    bucket = oss2.Bucket(
        oss_auth,
        oss_endpoint,
        bucket_name=bucket_name,
    )
    try:
        async with asyncio_oss.Bucket(oss_auth, oss_endpoint, bucket_name) as bucket:
            result_url = await bucket.sign_url("GET", oss_key, expire_seconds)
            assert result_url
    except Exception as e:
        raise RuntimeError(f"签名 URL 生成失败：{e}")
    
    return result_url


# if __name__ == "__main__":
#     import asyncio
    # ALI_ACCESS_KEY_ID = 'LTAI5tQe2TUCGB5q7AAaD3rX'
    # ALI_ACCESS_SECRET = '9HX2hrBiiyM4BfBa5YeomjYIvb7H23'
    # OSS_ORIGIN = 'oss-cn-beijing'
    # BUCKET_NAME = 'micro-drama'
#     signed_url = asyncio.run(agenerate_signed_url(oss_key="test.txt", expire_seconds=300, ali_access_key_id=ALI_ACCESS_KEY_ID, ali_access_secret=ALI_ACCESS_SECRET, oss_origin=OSS_ORIGIN, bucket_name=BUCKET_NAME))
#     print(signed_url)