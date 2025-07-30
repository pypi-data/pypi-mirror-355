from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, HttpUrl, ConfigDict, model_validator, ValidationError
from datetime import datetime, timezone

# Common Models
class Location(BaseModel):
    """IP地理位置信息"""
    owner: Optional[str] = Field(None, description="IP归属单位")
    province_cn: Optional[str] = Field(None, description="省份（中文）")
    isp: Optional[str] = Field(None, description="运营商，如：联通、电信、移动等")
    province_en: Optional[str] = Field(None, description="省份（英文）")
    country_en: Optional[str] = Field(None, description="国家（英文）")
    district_cn: Optional[str] = Field(None, description="区县（中文）")
    gps: Optional[List[float]] = Field(None, description="GPS坐标 [经度, 纬度]")
    street_cn: Optional[str] = Field(None, description="街道（中文）")
    city_en: Optional[str] = Field(None, description="城市（英文）")
    district_en: Optional[str] = Field(None, description="区县（英文）")
    country_cn: Optional[str] = Field(None, description="国家（中文）")
    street_en: Optional[str] = Field(None, description="街道（英文）")
    city_cn: Optional[str] = Field(None, description="城市（中文）")
    country_code: Optional[str] = Field(None, description="国家代码，如：CN、US")
    asname: Optional[str] = Field(None, description="自治域名称")
    scene_cn: Optional[str] = Field(None, description="应用场景（中文），如：家庭宽带、IDC机房等")
    scene_en: Optional[str] = Field(None, description="应用场景（英文）")
    radius: Optional[float] = Field(None, description="GPS定位精度半径（单位：公里）")

class Component(BaseModel):
    """组件/产品信息"""
    product_level: Optional[str] = Field(None, description="应用层级：硬件设备层、操作系统层、服务协议层、中间支持层、应用业务层")
    product_catalog: Optional[List[str]] = Field(None, description="应用类别，如：IoT物联网、网络安全设备等")
    product_vendor: Optional[str] = Field(None, description="应用生产厂商")
    product_name_cn: Optional[str] = Field(None, description="产品名称（中文）")
    product_name_en: Optional[str] = Field(None, description="产品名称（英文）")
    id: Optional[str] = Field(None, description="组件唯一标识符")
    version: Optional[str] = Field(None, description="产品版本号")
    product_type: Optional[List[str]] = Field(None, description="应用类型，如：防火墙、VPN等")

class ImageItem(BaseModel):
    """图片信息"""
    data: Optional[str] = Field(None, description="Base64编码的图片数据")
    mime: Optional[str] = Field(None, description="图片MIME类型，如：image/png、image/jpeg")
    width: Optional[int] = Field(None, description="图片宽度（像素）")
    height: Optional[int] = Field(None, description="图片高度（像素）")
    md5: Optional[str] = Field(None, description="图片MD5哈希值")
    s3_url: Optional[str] = Field(None, description="图片在S3存储的URL地址")

class Favicon(BaseModel):
    """网站图标信息"""
    hash: Optional[str] = Field(None, description="favicon的MD5哈希值")
    data: Optional[str] = Field(None, description="Base64编码的favicon图片数据")
    location: Optional[str] = Field(None, description="favicon的URL地址")
    s3_url: Optional[str] = Field(None, description="favicon在S3存储的URL地址")

class CookieElement(BaseModel):
    """Cookie元素信息"""
    order_hash: Optional[str] = Field(None, description="Cookie所有key用英文逗号拼接后的MD5")
    simhash: Optional[str] = Field(None, description="Cookie key的simhash值")

class DomTreeInfo(BaseModel):
    """DOM树信息"""
    dom_hash: Optional[str] = Field(None, description="DOM树所有元素的哈希值")
    simhash: Optional[str] = Field(None, description="DOM树节点的simhash")

class LinkOtherItem(BaseModel):
    """其他链接信息"""
    is_inner: Optional[bool] = Field(None, description="是否为内部链接")
    url: Optional[str] = Field(None, description="链接URL地址，支持javascript:等特殊链接")

class LinkImgItem(BaseModel):
    """图片链接信息"""
    is_inner: Optional[bool] = Field(None, description="是否为内部链接")
    url: Optional[str] = Field(None, description="图片URL地址")
    md5: Optional[str] = Field(None, description="图片内容的MD5哈希值")

class LinkScriptItem(BaseModel):
    """脚本链接信息"""
    is_inner: Optional[bool] = Field(None, description="是否为内部链接")
    url: Optional[str] = Field(None, description="脚本URL地址")
    md5: Optional[str] = Field(None, description="脚本内容的MD5哈希值")

class LinkInfo(BaseModel):
    """页面链接汇总信息"""
    other: Optional[List[LinkOtherItem]] = Field(None, description="其他类型链接列表")
    img: Optional[List[LinkImgItem]] = Field(None, description="图片链接列表")
    script: Optional[List[LinkScriptItem]] = Field(None, description="脚本链接列表")

class HttpServiceInfo(BaseModel):
    """HTTP服务详细信息"""
    status_code: Optional[int] = Field(None, description="HTTP返回状态码")
    path: Optional[str] = Field(None, description="HTTP请求路径")
    title: Optional[str] = Field(None, description="网页标题")
    meta_keywords: Optional[str] = Field(None, description="网页关键字（meta keywords）")
    server: Optional[str] = Field(None, description="Web服务器名称（HTTP headers中的Server字段）")
    x_powered_by: Optional[str] = Field(None, description="网站开发语言（HTTP headers中的X-Powered-By字段）")
    favicon: Optional[Favicon] = Field(None, description="网站图标信息")
    host: Optional[str] = Field(None, description="请求的host值")
    html_hash: Optional[str] = Field(None, description="网页HTML内容的MD5值")
    response_headers: Optional[str] = Field(None, description="HTTP响应头字符串")
    header_order_hash: Optional[str] = Field(None, description="HTTP头部所有key用英文逗号按序连接后的MD5")
    body: Optional[str] = Field(None, description="网页body内容")
    robots_hash: Optional[str] = Field(None, description="robots.txt文件的MD5值")
    robots: Optional[str] = Field(None, description="robots.txt文件内容")
    sitemap_hash: Optional[str] = Field(None, description="sitemap.xml文件的MD5值")
    sitemap: Optional[str] = Field(None, description="sitemap.xml文件内容")
    cookie_element: Optional[CookieElement] = Field(None, description="Cookie元素信息")
    dom_tree: Optional[DomTreeInfo] = Field(None, description="DOM树信息")
    script_function: Optional[List[str]] = Field(None, description="script标签中的函数名列表")
    script_variable: Optional[List[str]] = Field(None, description="script标签中的变量名列表")
    css_class: Optional[List[str]] = Field(None, description="CSS标签class字段值列表")
    css_id: Optional[List[str]] = Field(None, description="CSS标签id字段值列表")
    http_load_url: Optional[List[HttpUrl]] = Field(None, description="HTTP加载流URL列表，不包含静态资源")
    icp: Optional["ICPInfo"] = Field(None, description="ICP备案信息")
    copyright: Optional[str] = Field(None, description="版权信息")
    mail: Optional[List[str]] = Field(None, description="邮箱地址列表")
    page_type: Optional[List[str]] = Field(None, description="页面类型，如：登录页")
    iframe_url: Optional[List[HttpUrl]] = Field(None, description="iframe链接列表")
    iframe_hash: Optional[List[str]] = Field(None, description="iframe url内容的MD5值列表")
    iframe_title: Optional[List[str]] = Field(None, description="iframe链接标题列表")
    iframe_keywords: Optional[List[str]] = Field(None, description="iframe链接关键字列表")
    domain_is_wildcard: Optional[bool] = Field(None, description="是否存在泛解析域名")
    is_domain: Optional[bool] = Field(None, description="是否存在域名")
    icp_nature: Optional[str] = Field(None, description="ICP备案主体性质：企业、政府机关、事业单位等")
    icp_keywords: Optional[str] = Field(None, description="ICP备案网站中的关键词或域名")
    http_load_count: Optional[int] = Field(None, description="HTTP加载资源数量")
    data_sources: Optional[int] = Field(None, description="数据来源标识")
    page_type_keyword: Optional[List[str]] = Field(None, description="页面类型关键词列表")
    link: Optional[LinkInfo] = Field(None, description="页面链接汇总信息")


class TLSJarm(BaseModel):
    """TLS JARM指纹信息"""
    jarm_hash: Optional[str] = Field(None, description="JARM指纹哈希值")
    jarm_ans: Optional[List[str]] = Field(None, description="JARM指纹响应列表")


class FtpServiceInfo(BaseModel):
    """FTP服务信息"""
    is_anonymous: Optional[bool] = Field(None, description="是否允许匿名访问")

class RsyncServiceInfo(BaseModel):
    """Rsync服务信息"""
    authentication: Optional[bool] = Field(None, description="是否需要认证")

class SshKey(BaseModel):
    """SSH密钥信息"""
    type: Optional[str] = Field(None, description="密钥类型，如：RSA、DSA、ECDSA等")
    fingerprint: Optional[str] = Field(None, description="密钥指纹")
    key: Optional[str] = Field(None, description="公钥内容")

class SshServiceInfo(BaseModel):
    """SSH服务信息"""
    server_keys: Optional[List[SshKey]] = Field(None, description="服务器密钥列表")
    ciphers: Optional[List[str]] = Field(None, description="支持的加密算法列表")
    kex: Optional[List[str]] = Field(None, description="支持的密钥交换算法列表")
    digests: Optional[List[str]] = Field(None, description="支持的消息摘要算法列表")
    key_types: Optional[List[str]] = Field(None, description="支持的密钥类型列表")
    compression: Optional[List[str]] = Field(None, description="支持的压缩算法列表")

class UpnpServiceInfo(BaseModel):
    """UPnP服务信息"""
    deviceType: Optional[str] = Field(None, description="设备类型")
    friendlyName: Optional[str] = Field(None, description="友好名称")
    manufacturer: Optional[str] = Field(None, description="制造商")
    manufacturerURL: Optional[HttpUrl] = Field(None, description="制造商URL")
    modelDescription: Optional[str] = Field(None, description="设备型号描述")
    modelName: Optional[str] = Field(None, description="设备型号名称")
    modelNumber: Optional[str] = Field(None, description="设备型号编号")

class ICPInfo(BaseModel):
    """ICP备案信息"""
    licence: Optional[str] = Field(None, description="ICP备案号")
    update_time: Optional[str] = Field(None, description="备案更新时间")
    is_expired: Optional[bool] = Field(None, description="备案是否过期")
    leader_name: Optional[str] = Field(None, description="负责人姓名")
    domain: Optional[str] = Field(None, description="备案域名")
    main_licence: Optional[Dict[str, Any]] = Field(None, description="主体备案信息")
    content_type_name: Optional[str] = Field(None, description="内容类型名称")
    limit_access: Optional[bool] = Field(None, description="是否限制访问")

class SnmpServiceInfo(BaseModel):
    """SNMP服务信息"""
    sysname: Optional[str] = Field(None, description="系统名称")
    sysdesc: Optional[str] = Field(None, description="系统描述")
    sysuptime: Optional[str] = Field(None, description="系统运行时间")
    syslocation: Optional[str] = Field(None, description="系统位置")
    syscontact: Optional[str] = Field(None, description="系统联系人")
    sysobjectid: Optional[str] = Field(None, description="系统对象标识符")

class DockerContainer(BaseModel):
    """Docker容器信息"""
    Image: Optional[str] = Field(None, description="容器镜像")
    Command: Optional[str] = Field(None, description="容器运行命令")

class DockerVersionInfo(BaseModel):
    """Docker版本信息"""
    Version: Optional[str] = Field(None, description="Docker版本号")
    ApiVersion: Optional[str] = Field(None, description="API版本号")
    MinAPIVersion: Optional[str] = Field(None, description="最小API版本号")
    GitCommit: Optional[str] = Field(None, description="Git提交哈希")
    GoVersion: Optional[str] = Field(None, description="Go语言版本")
    Arch: Optional[str] = Field(None, description="系统架构")
    KernelVersion: Optional[str] = Field(None, description="内核版本")
    BuildTime: Optional[str] = Field(None, description="构建时间")

class DockerServiceInfo(BaseModel):
    """Docker服务信息"""
    containers: Optional[List[DockerContainer]] = Field(None, description="容器列表")
    version: Optional[DockerVersionInfo] = Field(None, description="Docker版本信息")

class DnsServiceInfo(BaseModel):
    """DNS服务信息"""
    id_server: Optional[str] = Field(None, description="DNS服务器标识")
    version_bind: Optional[str] = Field(None, description="BIND版本信息")

class ElasticIndex(BaseModel):
    """Elasticsearch索引信息"""
    health: Optional[str] = Field(None, description="索引健康状态：green、yellow、red")
    status: Optional[str] = Field(None, description="索引状态：open、close")
    index: Optional[str] = Field(None, description="索引名称")
    uuid: Optional[str] = Field(None, description="索引唯一标识符")
    docs_count: Optional[Union[int,str]] = Field(None, description="文档数量")
    store_size: Optional[str] = Field(None, description="存储大小")
    pri: Optional[str] = Field(None, description="主分片数量")
    rep: Optional[str] = Field(None, description="副本分片数量")
    pri_store_size: Optional[str] = Field(None, description="主分片存储大小")
    docs_deleted: Optional[str] = Field(None, description="已删除文档数量")

class ElasticServiceInfo(BaseModel):
    """Elasticsearch服务信息"""
    indices: Optional[List[ElasticIndex]] = Field(None, description="索引列表")

class HiveDbTable(BaseModel):
    """Hive数据库表信息"""
    dbname: Optional[str] = Field(None, description="数据库名称")
    tables: Optional[List[str]] = Field(None, description="数据表名称列表")

class HiveServiceInfo(BaseModel):
    """Hive服务信息"""
    hive_dbs: Optional[List[HiveDbTable]] = Field(None, description="Hive数据库列表")

class MongoOpenSSLInfo(BaseModel):
    """MongoDB OpenSSL信息"""
    running: Optional[str] = Field(None, description="运行时OpenSSL版本")
    compiled: Optional[str] = Field(None, description="编译时OpenSSL版本")

class MongoBuildEnvironmentInfo(BaseModel):
    """MongoDB构建环境信息"""
    distmod: Optional[str] = Field(None, description="发行版模块")
    distarch: Optional[str] = Field(None, description="发行版架构")
    cc: Optional[str] = Field(None, description="C编译器")
    ccflags: Optional[str] = Field(None, description="C编译器标志")
    cxx: Optional[str] = Field(None, description="C++编译器")
    cxxflags: Optional[str] = Field(None, description="C++编译器标志")
    linkflags: Optional[str] = Field(None, description="链接器标志")
    target_arch: Optional[str] = Field(None, description="目标架构")
    target_os: Optional[str] = Field(None, description="目标操作系统")
    cppdefines: Optional[str] = Field(None, description="C预处理器定义")

class MongoBuildInfo(BaseModel):
    """MongoDB构建信息"""
    version: Optional[str] = Field(None, description="MongoDB版本号")
    gitVersion: Optional[str] = Field(None, description="Git版本号")
    openssl: Optional[MongoOpenSSLInfo] = Field(None, description="OpenSSL信息")
    sysInfo: Optional[str] = Field(None, description="系统信息")
    allocator: Optional[str] = Field(None, description="内存分配器")
    versionArray: Optional[List[int]] = Field(None, description="版本数组")
    javascriptEngine: Optional[str] = Field(None, description="JavaScript引擎")
    bits: Optional[int] = Field(None, description="系统位数：32或64")
    debug: Optional[bool] = Field(None, description="是否为调试版本")
    maxBsonObjectSize: Optional[int] = Field(None, description="最大BSON对象大小")
    buildEnvironment: Optional[MongoBuildEnvironmentInfo] = Field(None, description="构建环境信息")
    storageEngines: Optional[List[str]] = Field(None, description="存储引擎列表")
    modules: Optional[List[str]] = Field(None, description="模块列表")
    ok: Optional[float] = Field(None, description="操作状态码")

class MongoConnections(BaseModel):
    """MongoDB连接信息"""
    current: Optional[int] = Field(None, description="当前连接数")
    available: Optional[int] = Field(None, description="可用连接数")
    totalCreated: Optional[int] = Field(None, description="总创建连接数")
    rejected: Optional[int] = Field(None, description="拒绝连接数")
    active: Optional[int] = Field(None, description="活跃连接数")
    threaded: Optional[int] = Field(None, description="线程连接数")
    exhaustIsMaster: Optional[int] = Field(None, description="exhaustIsMaster连接数")
    exhaustHello: Optional[int] = Field(None, description="exhaustHello连接数")
    awaitingTopologyChanges: Optional[int] = Field(None, description="等待拓扑变化的连接数")

class MongoServerStatus(BaseModel):
    """MongoDB服务器状态"""
    host: Optional[str] = Field(None, description="主机名")
    process: Optional[str] = Field(None, description="进程类型")
    pid: Optional[int] = Field(None, description="进程ID")
    connections: Optional[MongoConnections] = Field(None, description="连接信息")

class MongoDatabase(BaseModel):
    """MongoDB数据库信息"""
    name: Optional[str] = Field(None, description="数据库名称")
    sizeOnDisk: Optional[Union[float,int,str]] = Field(None, description="磁盘占用大小")
    empty: Optional[bool] = Field(None, description="是否为空数据库")

class MongoListDatabases(BaseModel):
    """MongoDB数据库列表"""
    databases: Optional[List[MongoDatabase]] = Field(None, description="数据库列表")
    totalSize: Optional[Union[int,str]] = Field(None, description="总大小（字节）")
    totalSizeMb: Optional[int] = Field(None, description="总大小（MB）")

class MongoServiceInfo(BaseModel):
    """MongoDB服务信息"""
    authentication: Optional[bool] = Field(None, description="是否需要认证")
    buildInfo: Optional[MongoBuildInfo] = Field(None, description="构建信息")
    serverStatus: Optional[MongoServerStatus] = Field(None, description="服务器状态")
    listDatabases: Optional[MongoListDatabases] = Field(None, description="数据库列表")

class EthernetIpServiceInfo(BaseModel):
    """EtherNet/IP服务信息"""
    product_name: Optional[str] = Field(None, description="产品名称")
    product_code: Optional[int] = Field(None, description="产品代码")
    device_ip: Optional[str] = Field(None, description="设备IP地址")
    vendor: Optional[str] = Field(None, description="供应商")
    revision: Optional[str] = Field(None, description="版本修订号")
    serial_num: Optional[str] = Field(None, description="设备序列号")
    device_type: Optional[str] = Field(None, description="设备类型")

class ModbusProjectInfo(BaseModel):
    """Modbus项目信息"""
    Project_Revision: Optional[str] = Field(None, description="项目修订版本")
    ProjectLastModified: Optional[str] = Field(None, description="项目最后修改时间")
    ProjectInformation: Optional[str] = Field(None, description="项目信息描述")

class ModbusServiceInfo(BaseModel):
    """Modbus服务信息"""
    UnitId: Optional[int] = Field(None, description="单元标识符")
    DeviceIdentification: Optional[str] = Field(None, description="设备标识")
    SlaveIDdata: Optional[str] = Field(None, description="从站ID数据")
    CpuModule: Optional[str] = Field(None, description="CPU模块")
    MemoryCard: Optional[str] = Field(None, description="存储卡信息")
    ProjectInfo: Optional[ModbusProjectInfo] = Field(None, description="项目信息")

class S7ServiceInfo(BaseModel):
    """西门子S7协议服务信息"""
    Module: Optional[str] = Field(None, description="模块名称")
    Basic_Hardware: Optional[str] = Field(None, description="基础硬件")
    Basic_Firmware: Optional[str] = Field(None, description="基础固件")
    Name_of_the_PLC: Optional[str] = Field(None, description="PLC名称")
    Name_of_the_module: Optional[str] = Field(None, description="模块名称")
    Plant_identification: Optional[str] = Field(None, description="工厂标识")
    Reserved_for_operating_system: Optional[str] = Field(None, description="操作系统保留字段")
    Module_type_name: Optional[str] = Field(None, description="模块类型名称")
    Serial_number_of_memory_card: Optional[str] = Field(None, description="存储卡序列号")
    OEM_ID_of_a_module: Optional[str] = Field(None, description="模块OEM标识")
    Location_designation_of_a_module: Optional[str] = Field(None, description="模块位置标识")
    unknown_129: Optional[str] = Field(default=None, alias="Unknown(129)", description="未知字段129")

class SmbServiceInfo(BaseModel):
    """SMB服务信息"""
    ServerDefaultDialect: Optional[str] = Field(None, description="服务器默认方言")
    ListDialects: Optional[List[str]] = Field(None, description="支持的方言列表")
    Capabilities: Optional[List[str]] = Field(None, description="服务器能力列表")
    Authentication: Optional[str] = Field(None, description="认证方式")
    ServerOS: Optional[str] = Field(None, description="服务器操作系统")
    ServerDomain: Optional[str] = Field(None, description="服务器域名")
    ServerDNSDomainName: Optional[str] = Field(None, description="服务器DNS域名")
    RemoteName: Optional[str] = Field(None, description="远程名称")
    SupportNTLMv2: Optional[bool] = Field(None, description="是否支持NTLMv2")
    SMBv1OS: Optional[str] = Field(None, description="SMBv1操作系统信息")
    listShares: Optional[List[Any]] = Field(None, description="共享列表")

class TlsValidationInfo(BaseModel):
    """TLS证书验证信息"""
    matches_domain: Optional[bool] = Field(None, description="证书是否匹配域名")
    browser_trusted: Optional[bool] = Field(None, description="证书是否被浏览器信任")
    browser_error: Optional[str] = Field(None, description="浏览器验证错误信息")

class TlsServiceInfo(BaseModel):
    """TLS服务信息"""
    tls_AKID: Optional[str] = Field(None, description="颁发机构密钥标识符（Authority Key Identifier）")
    tls_authority_key_id: Optional[str] = Field(None, description="颁发机构密钥标识符")
    tls_SAN: Optional[List[str]] = Field(None, description="主体可选名称（Subject Alternative Name）")
    tls_subject_alt_name: Optional[List[str]] = Field(None, description="主体可选名称")
    tls_SKID: Optional[str] = Field(None, description="主体密钥标识符（Subject Key Identifier）")
    tls_subject_key_id: Optional[str] = Field(None, description="主体密钥标识符")
    tls_md5: Optional[str] = Field(None, description="证书MD5哈希值")
    tls_sha1: Optional[str] = Field(None, description="证书SHA1哈希值")
    tls_sha256: Optional[str] = Field(None, description="证书SHA256哈希值")
    tls_SPKI: Optional[str] = Field(None, description="公钥SHA256哈希值（Subject Public Key Info）")
    tls_subject_key_info_sha256: Optional[str] = Field(None, description="公钥SHA256哈希值")
    tls_SN: Optional[str] = Field(None, description="证书序列号（Serial Number）")
    tls_serial_number: Optional[str] = Field(None, description="证书序列号")
    tls_issuer: Optional[str] = Field(None, description="证书签发者完整信息")
    tls_issuer_common_name: Optional[str] = Field(None, description="签发者通用名称（CN）")
    tls_issuer_country: Optional[str] = Field(None, description="签发者所属国家（C）")
    tls_issuer_organization: Optional[str] = Field(None, description="签发者所属组织（O）")
    tls_subject: Optional[str] = Field(None, description="证书主体完整信息")
    tls_subject_common_name: Optional[str] = Field(None, description="主体通用名称（CN）")
    tls_subject_country: Optional[str] = Field(None, description="主体所属国家（C）")
    tls_subject_organization: Optional[str] = Field(None, description="主体所属组织（O）")
    common_name_wildcard: Optional[bool] = Field(None, description="通用名称是否为泛域名证书")
    ja3s: Optional[str] = Field(None, description="JA3S指纹（TLS服务器指纹）")
    ja4s: Optional[str] = Field(None, description="JA4S指纹（TLS服务器指纹）")
    two_way_authentication: Optional[bool] = Field(None, description="是否启用双向认证")
    handshake_log: Optional[Dict[str, Any]] = Field(None, description="TLS握手日志")
    version: Optional[List[str]] = Field(None, description="支持的TLS版本列表")
    validation: Optional[TlsValidationInfo] = Field(None, description="证书验证信息")


class IPTcpData(BaseModel):
    """TCP连接信息"""
    window: Optional[int] = Field(None, description="TCP窗口大小")

class IPAddressData(BaseModel):
    """IP地址相关信息"""
    distance: Optional[int] = Field(None, description="网络跳数距离")
    initial_ttl: Optional[int] = Field(None, description="初始TTL值")
    tos: Optional[int] = Field(None, description="服务类型（Type of Service）")
    ttl: Optional[int] = Field(None, description="生存时间（Time To Live）")

class NetData(BaseModel):
    """网络连接信息"""
    service_probe_name: Optional[str] = Field(None, description="服务探测器名称")
    tcp: Optional[IPTcpData] = Field(None, description="TCP连接信息")
    router_ip: Optional[str] = Field(None, description="路由器IP地址")
    ip: Optional[IPAddressData] = Field(None, description="IP地址相关信息")
    port_response_time: Optional[int] = Field(None, description="端口响应时间（毫秒）")


class ServiceSpecificData(BaseModel):
    """服务特定数据（已废弃，仅为兼容保留）"""
    http: Optional[HttpServiceInfo] = Field(None, description="HTTP服务详细信息")
    ftp: Optional[FtpServiceInfo] = Field(None, description="FTP服务信息")
    rsync: Optional[RsyncServiceInfo] = Field(None, description="Rsync服务信息")
    ssh: Optional[SshServiceInfo] = Field(None, description="SSH服务信息")
    upnp: Optional[UpnpServiceInfo] = Field(None, description="UPnP服务信息")
    snmp: Optional[SnmpServiceInfo] = Field(None, description="SNMP服务信息")
    docker: Optional[DockerServiceInfo] = Field(None, description="Docker服务信息")
    domain: Optional[DnsServiceInfo] = Field(None, description="DNS服务信息")
    elastic: Optional[ElasticServiceInfo] = Field(None, description="Elasticsearch服务信息")
    hive: Optional[HiveServiceInfo] = Field(None, description="Hive服务信息")
    mongodb: Optional[MongoServiceInfo] = Field(None, description="MongoDB服务信息")
    ethernetip: Optional[EthernetIpServiceInfo] = Field(None, description="EtherNet/IP服务信息")
    modbus: Optional[ModbusServiceInfo] = Field(None, description="Modbus服务信息")
    s7: Optional[S7ServiceInfo] = Field(None, description="西门子S7协议服务信息")
    smb: Optional[SmbServiceInfo] = Field(None, description="SMB服务信息")
    tls: Optional[TlsServiceInfo] = Field(None, description="TLS服务信息")
    tls_jarm: Optional[TLSJarm] = Field(default=None, alias="tls-jarm", description="TLS JARM指纹信息")


class ServiceData(BaseModel):
    """服务数据信息"""
    product: Optional[str] = Field(None, description="经过Quake指纹识别后的产品名称")
    components: Optional[List[Component]] = Field(None, description="组件列表")
    port: Optional[int] = Field(None, description="端口号")
    service_id: Optional[str] = Field(None, description="服务唯一标识符")
    name: str = Field(..., description="服务名称/应用协议名称，如：http、ssh等")
    cert: Optional[str] = Field(None, description="SSL/TLS证书信息（格式化后的证书字符串）")
    transport: Optional[str] = Field(None, description="传输层协议：tcp或udp")
    time: Optional[str] = Field(None, description="服务发现时间")
    version: Optional[str] = Field(None, description="产品版本号")
    tags: Optional[List[str]] = Field(None, description="服务标签列表")
    response: Optional[str] = Field(None, description="服务原始响应数据")
    response_hash: Optional[str] = Field(None, description="响应数据的哈希值")
    net: Optional[NetData] = Field(None, description="网络连接信息")

    @model_validator(mode='before')
    @classmethod
    def populate_tls_data(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        service_name = values.get('name')
        if service_name in ('tls', 'tls/ssl'):
            # 如果服务名称表明是TLS相关服务，
            # 并且原始数据中 'service' 对象下没有 'tls' 键，或者该键的值不是一个字典，
            # 我们就主动为 'tls' 键设置一个空字典。
            # 这样 Pydantic 在后续处理时，会用这个空字典去尝试创建 TlsServiceInfo 实例，
            # 结果将是一个所有字段都为 None 的 TlsServiceInfo 对象，
            # 但 ServiceData.tls 本身将不再是 None。
            if not isinstance(values.get('tls'), dict): # 包含了 'tls' 不存在或其值不是字典的情况
                values['tls'] = {} 
            
            # 'tls-jarm' 字段由其别名处理。
            # 如果原始数据中 'service' 对象下存在 'tls-jarm' 键，
            # Pydantic 会用它来填充 ServiceData 模型的 'tls_jarm' 属性。
            # 如果不存在，'tls_jarm' 将保持为 None。
            # 此处校验器无需为 'tls_jarm' 做特殊处理。
        return values

    @model_validator(mode='before')
    @classmethod
    def populate_full_mongodb_buildinfo(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        # Normalize service name first
        service_name = values.get('name')
        if service_name == 'mongodb/ssl':
            values['name'] = 'mongodb'
            service_name = 'mongodb'  # Update for current scope

        # If it's a mongodb service, try to get full buildInfo from response
        if service_name == 'mongodb':
            raw_response_str = values.get('response')
            # Ensure 'mongodb' key exists and is a dict before trying to access/modify it
            if 'mongodb' not in values or not isinstance(values.get('mongodb'), dict):
                values['mongodb'] = {} # Initialize if not present or not a dict

            mongodb_data = values.get('mongodb') # Now it's guaranteed to be a dict or newly initialized {}

            if raw_response_str and isinstance(mongodb_data, dict):
                import json # Import locally to avoid top-level import if not always needed
                try:
                    parsed_response = json.loads(raw_response_str)
                    if isinstance(parsed_response, dict):
                        full_build_info_from_response = parsed_response.get('buildInfo')

                        if isinstance(full_build_info_from_response, dict):
                            # Ensure 'buildInfo' in mongodb_data is a dict before updating
                            if not isinstance(mongodb_data.get('buildInfo'), dict):
                                mongodb_data['buildInfo'] = {}
                            
                            # Update the existing buildInfo with fields from the full_build_info_from_response
                            # This prioritizes fields from response, but keeps others if they exist in the direct mongodb.buildInfo
                            # A more robust merge might be needed if there are complex overlaps
                            # For now, let's assume full_build_info_from_response is more complete or authoritative
                            mongodb_data['buildInfo'] = full_build_info_from_response
                            
                except json.JSONDecodeError:
                    # Log or handle error if response is not valid JSON
                    pass 
        return values

    http: Optional[HttpServiceInfo] = Field(None, description="HTTP服务详细信息")
    ftp: Optional[FtpServiceInfo] = Field(None, description="FTP服务信息")
    rsync: Optional[RsyncServiceInfo] = Field(None, description="Rsync服务信息")
    ssh: Optional[SshServiceInfo] = Field(None, description="SSH服务信息")
    upnp: Optional[UpnpServiceInfo] = Field(None, description="UPnP服务信息")
    snmp: Optional[SnmpServiceInfo] = Field(None, description="SNMP服务信息")
    docker: Optional[DockerServiceInfo] = Field(None, description="Docker服务信息")
    domain: Optional[DnsServiceInfo] = Field(None, description="DNS服务信息")
    elastic: Optional[ElasticServiceInfo] = Field(None, description="Elasticsearch服务信息")
    hive: Optional[HiveServiceInfo] = Field(None, description="Hive服务信息")
    mongodb: Optional[MongoServiceInfo] = Field(None, description="MongoDB服务信息")
    ethernetip: Optional[EthernetIpServiceInfo] = Field(None, description="EtherNet/IP服务信息")
    modbus: Optional[ModbusServiceInfo] = Field(None, description="Modbus服务信息")
    s7: Optional[S7ServiceInfo] = Field(None, description="西门子S7协议服务信息")
    smb: Optional[SmbServiceInfo] = Field(None, description="SMB服务信息")
    tls: Optional[TlsServiceInfo] = Field(None, description="TLS服务信息")
    tls_jarm: Optional[TLSJarm] = Field(default=None, alias="tls-jarm", description="TLS JARM指纹信息")


class QuakeService(BaseModel):
    """Quake服务数据模型"""
    ip: str = Field(..., description="IP地址")
    port: int = Field(..., description="端口号")
    hostname: Optional[str] = Field(None, description="主机名（rDNS数据）")
    transport: Optional[str] = Field(None, description="传输层协议：tcp或udp")
    asn: Optional[int] = Field(None, description="自治域号码（Autonomous System Number）")
    org: Optional[str] = Field(None, description="自治域归属组织名称")
    service: ServiceData = Field(..., description="服务详细信息")
    location: Optional[Location] = Field(None, description="地理位置信息")
    time: Optional[str] = Field(None, description="数据更新时间")
    domain: Optional[str] = Field(None, description="网站域名")
    components: Optional[List[Component]] = Field(None, description="组件列表")
    images: Optional[List[ImageItem]] = Field(None, description="图片列表")
    is_ipv6: Optional[bool] = Field(None, description="是否为IPv6地址")
    is_latest: Optional[bool] = Field(None, description="是否为最新数据")
    app: Optional[Component] = Field(None, description="主要应用组件信息")
    id: Optional[str] = Field(None, description="记录唯一标识符")
    os_name: Optional[str] = Field(None, description="操作系统名称")
    
    @model_validator(mode='after')
    def validate_time_field(self) -> 'QuakeService':
        """验证时间字段是否在合理范围内"""
        if self.time:
            try:
                # 尝试解析时间字符串
                dt = datetime.fromisoformat(self.time.replace('Z', '+00:00'))
                current_time = datetime.now(timezone.utc)
                
                # 检查时间是否在未来超过1天（允许时区差异）
                if dt > current_time.replace(hour=23, minute=59, second=59, microsecond=999999):
                    # 仅记录警告，不抛出异常，以保持向后兼容
                    import warnings
                    warnings.warn(
                        f"时间字段值可能异常，显示为未来时间: {self.time}",
                        UserWarning
                    )
            except (ValueError, AttributeError):
                # 如果时间格式不正确，忽略验证
                pass
        return self


class QuakeHost(BaseModel):
    """Quake主机数据模型"""
    hostname: Optional[str] = Field(None, description="主机名（rDNS数据）")
    org: Optional[str] = Field(None, description="自治域归属组织名称")
    ip: str = Field(..., description="IP地址")
    os_version: Optional[str] = Field(None, description="操作系统版本")
    os_name: Optional[str] = Field(None, description="操作系统名称")
    location: Optional[Location] = Field(None, description="地理位置信息")
    is_ipv6: Optional[bool] = Field(False, description="是否为IPv6地址")
    services: Optional[List[ServiceData]] = Field(None, description="主机上的服务列表")
    time: Optional[str] = Field(None, description="数据更新时间")
    asn: Optional[int] = Field(None, description="自治域号码（Autonomous System Number）")
    id: Optional[str] = Field(None, description="记录唯一标识符")
    
    @model_validator(mode='after')
    def validate_time_field(self) -> 'QuakeHost':
        """验证时间字段是否在合理范围内"""
        if self.time:
            try:
                # 尝试解析时间字符串
                dt = datetime.fromisoformat(self.time.replace('Z', '+00:00'))
                current_time = datetime.now(timezone.utc)
                
                # 检查时间是否在未来超过1天（允许时区差异）
                if dt > current_time.replace(hour=23, minute=59, second=59, microsecond=999999):
                    # 仅记录警告，不抛出异常，以保持向后兼容
                    import warnings
                    warnings.warn(
                        f"时间字段值可能异常，显示为未来时间: {self.time}",
                        UserWarning
                    )
            except (ValueError, AttributeError):
                # 如果时间格式不正确，忽略验证
                pass
        return self


# User Info Models
class UserRole(BaseModel):
    """用户角色信息"""
    fullname: str = Field(..., description="角色全名，如'注册用户'、'终身会员'等")
    priority: int = Field(..., description="角色优先级")
    credit: int = Field(..., description="该角色对应的积分额度")

class EnterpriseInformation(BaseModel):
    """企业认证信息"""
    name: Optional[str] = Field(None, description="企业名称")
    email: Optional[str] = Field(None, description="企业邮箱")
    status: str = Field(..., description="认证状态，如'未认证'、'已认证'等")

class PrivacyLog(BaseModel):
    """隐私日志配置"""
    status: bool = Field(..., description="隐私日志开启状态")
    time: Optional[str] = Field(None, description="隐私日志配置时间")
    # 扩展字段（实际API返回但文档未说明）
    quake_log_status: Optional[bool] = Field(None, description="Quake日志状态")
    quake_log_time: Optional[str] = Field(None, description="Quake日志时间")
    anonymous_model: Optional[bool] = Field(None, description="匿名模式状态")

class DisableInfo(BaseModel):
    """账号禁用信息"""
    disable_time: Optional[str] = Field(None, description="禁用时间")
    start_time: Optional[str] = Field(None, description="开始时间")

class InvitationCodeInfo(BaseModel):
    """邀请码信息"""
    code: str = Field(..., description="邀请码")
    invite_acquire_credit: int = Field(..., description="邀请获得的积分")
    invite_number: int = Field(..., description="邀请人数")

class RoleValidityPeriod(BaseModel):
    """角色有效期信息"""
    start_time: str = Field(..., description="开始时间")
    end_time: str = Field(..., description="结束时间") 
    remain_days: int = Field(..., description="剩余天数")

class User(BaseModel):
    """用户基本信息"""
    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    fullname: str = Field(..., description="全名/昵称")
    email: Optional[str] = Field(None, description="用户邮箱（可能为空）")
    group: Optional[List[str]] = Field(None, description="用户组列表")

class UserInfoData(BaseModel):
    """用户详细信息数据"""
    # 基础信息
    id: str = Field(..., description="用户信息记录ID")
    user: User = Field(..., description="用户基本信息")
    token: str = Field(..., description="用户API Token")
    source: str = Field(..., description="用户来源，如'quake'、'360_account'等")
    
    # 账号状态
    banned: bool = Field(..., alias="baned", description="是否被封禁")  # 修正API的拼写错误
    ban_status: str = Field(..., description="封禁状态描述，如'使用中'")
    personal_information_status: bool = Field(..., description="个人信息完善状态")
    
    # 积分相关
    credit: int = Field(..., description="当前可用积分")
    persistent_credit: int = Field(..., description="永久积分")
    month_remaining_credit: Optional[int] = Field(None, description="本月剩余免费查询次数")
    constant_credit: Optional[int] = Field(None, description="常量积分")
    free_query_api_count: Optional[int] = Field(None, description="免费API查询次数")
    
    # 联系信息
    mobile_phone: Optional[str] = Field(None, description="手机号码")
    
    # 其他信息
    privacy_log: Optional[PrivacyLog] = Field(None, description="隐私日志配置")
    enterprise_information: Optional[EnterpriseInformation] = Field(None, description="企业认证信息")
    role: List[UserRole] = Field(..., description="用户角色列表")
    
    # 扩展字段
    avatar_id: Optional[str] = Field(None, description="头像ID")
    time: Optional[str] = Field(None, description="注册时间")
    disable: Optional[DisableInfo] = Field(None, description="禁用信息")
    invitation_code_info: Optional[InvitationCodeInfo] = Field(None, description="邀请码信息")
    is_cashed_invitation_code: Optional[bool] = Field(None, description="是否已兑换邀请码")
    role_validity: Optional[Dict[str, Optional[RoleValidityPeriod]]] = Field(None, description="角色有效期信息")

    @model_validator(mode='after')
    def validate_role_validity(self) -> 'UserInfoData':
        """验证并转换role_validity字段"""
        if self.role_validity and isinstance(self.role_validity, dict):
            validated_validity: Dict[str, Optional[RoleValidityPeriod]] = {}
            for role_name, validity_data in self.role_validity.items():
                if validity_data is None:
                    validated_validity[role_name] = None
                elif isinstance(validity_data, dict):
                    try:
                        validated_validity[role_name] = RoleValidityPeriod.model_validate(validity_data)
                    except ValidationError:
                        # 如果验证失败，保持原始数据
                        validated_validity[role_name] = validity_data
                else:
                    validated_validity[role_name] = validity_data
            self.role_validity = validated_validity
        return self


# Aggregation Models
class AggregationBucket(BaseModel):
    """聚合数据桶"""
    key: Union[str, int, float] = Field(..., description="聚合键值")
    doc_count: int = Field(..., description="文档数量")

class AggregationData(BaseModel):
    """聚合数据基类"""
    pass


# Favicon Similarity Models
class SimilarIconData(BaseModel):
    """相似图标数据"""
    key: str = Field(..., description="favicon哈希值")
    doc_count: int = Field(..., description="相同favicon的数量")
    data: Optional[str] = Field(None, description="Base64编码的favicon图片数据")


# Pagination and Metadata
class Pagination(BaseModel):
    """分页信息"""
    count: Optional[int] = Field(None, description="当前页返回的数据条数")
    page_index: Optional[int] = Field(None, description="当前页码")
    page_size: Optional[int] = Field(None, description="每页数据条数")
    total: Optional[Union[int, Dict[str, Any]]] = Field(None, description="总数据条数或总数信息")
    pagination_id: Optional[str] = Field(None, description="深度分页标识符")

class Meta(BaseModel):
    """响应元数据"""
    pagination: Optional[Pagination] = Field(None, description="分页信息")
    total: Optional[Union[int, Dict[str, Any]]] = Field(None, description="总数据条数或总数信息")
    pagination_id: Optional[str] = Field(None, description="深度分页标识符")


# Generic API Response Wrapper
class QuakeResponse(BaseModel):
    """Quake API 基础响应模型"""
    code: Union[int, str] = Field(..., description="响应状态码，0表示成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")
    meta: Optional[Meta] = Field(None, description="响应元数据")


# Specific Response Models
class UserInfoResponse(QuakeResponse):
    """用户信息响应"""
    data: Optional[UserInfoData] = Field(None, description="用户详细信息")

class FilterableFieldsResponse(QuakeResponse):
    """可筛选字段响应"""
    data: Optional[List[str]] = Field(None, description="可筛选字段列表")

class ServiceSearchResponse(QuakeResponse):
    """服务搜索响应"""
    data: Optional[List[QuakeService]] = Field(None, description="服务数据列表")
    meta: Meta = Field(..., description="响应元数据，包含分页信息")

    @property
    def services(self) -> List[QuakeService]:
        """安全地获取服务列表，如果 data 不是列表则返回空列表"""
        if isinstance(self.data, list):
            return self.data
        return []

class ServiceScrollResponse(QuakeResponse):
    """服务深度查询响应"""
    data: Optional[List[QuakeService]] = Field(None, description="服务数据列表")
    meta: Meta = Field(..., description="响应元数据，包含分页标识符")

class ServiceAggregationResponse(QuakeResponse):
    """服务聚合响应"""
    data: Optional[Dict[str, List[AggregationBucket]]] = Field(None, description="聚合结果，键为聚合字段名")
    meta: Optional[Meta] = Field(None, description="响应元数据")

class HostSearchResponse(QuakeResponse):
    """主机搜索响应"""
    data: Optional[List[QuakeHost]] = Field(None, description="主机数据列表")
    meta: Meta = Field(..., description="响应元数据，包含分页信息")

    @property
    def hosts(self) -> List[QuakeHost]:
        """安全地获取主机列表，如果 data 不是列表则返回空列表"""
        if isinstance(self.data, list):
            return self.data
        return []

class HostScrollResponse(QuakeResponse):
    """主机深度查询响应"""
    data: Optional[List[QuakeHost]] = Field(None, description="主机数据列表")
    meta: Meta = Field(..., description="响应元数据，包含分页标识符")

class HostAggregationResponse(QuakeResponse):
    """主机聚合响应"""
    data: Optional[Dict[str, List[AggregationBucket]]] = Field(None, description="聚合结果，键为聚合字段名")
    meta: Optional[Meta] = Field(None, description="响应元数据")

class SimilarIconResponse(QuakeResponse):
    """相似图标查询响应"""
    data: Optional[List[SimilarIconData]] = Field(None, description="相似图标数据列表")
    meta: Optional[Meta] = Field(None, description="响应元数据")


# Request Body Models
class BaseSearchQuery(BaseModel):
    """基础搜索查询参数"""
    query: Optional[str] = Field(None, description="查询语句，使用Quake查询语法")
    ignore_cache: Optional[bool] = Field(False, description="是否忽略缓存")
    start_time: Optional[str] = Field(None, description="查询起始时间，格式：YYYY-MM-DD HH:MM:SS，时区为UTC")
    end_time: Optional[str] = Field(None, description="查询截止时间，格式：YYYY-MM-DD HH:MM:SS，时区为UTC")
    ip_list: Optional[List[str]] = Field(None, description="IP列表，支持单个IP或CIDR格式")
    rule: Optional[str] = Field(None, description="类型为IP列表的数据收藏名称")

    @model_validator(mode='before')
    @classmethod
    def check_query_or_ip_list(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        # ScrollSearchQuery 有自己的验证逻辑，所以跳过
        if cls.__name__ == "ScrollSearchQuery":
            return values
            
        if not values.get('query') and not values.get('ip_list'):
            if cls.__name__ != "AggregationQuery": # AggregationQuery always needs a query
                 raise ValueError('必须提供 "query" 或 "ip_list" 参数之一')
            elif not values.get('query'): # This implies cls.__name__ == "AggregationQuery"
                 raise ValueError('聚合查询必须提供 "query" 参数')
        return values

class RealtimeSearchQuery(BaseSearchQuery):
    """实时查询参数"""
    start: Optional[int] = Field(0, description="返回结果的起始位置", ge=0)
    size: Optional[int] = Field(10, description="返回结果的数量", ge=1, le=10000)
    include: Optional[List[str]] = Field(None, description="包含字段列表")
    exclude: Optional[List[str]] = Field(None, description="排除字段列表")
    latest: Optional[bool] = Field(False, description="是否只查询最新数据（仅服务查询支持）")
    shortcuts: Optional[List[str]] = Field(None, description="快捷过滤器列表（仅服务查询支持）")

class ScrollSearchQuery(BaseSearchQuery):
    """深度查询参数"""
    size: Optional[int] = Field(10, description="每次返回的数据条数", ge=1, le=1000)
    pagination_id: Optional[str] = Field(None, description="分页标识符，用于获取下一页数据")
    include: Optional[List[str]] = Field(None, description="包含字段列表")
    exclude: Optional[List[str]] = Field(None, description="排除字段列表")
    latest: Optional[bool] = Field(False, description="是否只查询最新数据（仅服务查询支持）")

    @model_validator(mode='before')
    @classmethod
    def validate_query_required(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """确保 query 字段必填，因为深度查询接口要求 query 是必填项"""
        if not values.get('query'):
            raise ValueError('深度查询必须提供 "query" 参数')
        return values

class AggregationQuery(BaseSearchQuery):
    """聚合查询参数"""
    aggregation_list: List[str] = Field(..., description="聚合字段列表")
    size: Optional[int] = Field(5, description="每个聚合项返回的数量", ge=1, le=1000)
    latest: Optional[bool] = Field(False, description="是否只查询最新数据（仅服务聚合支持）")

class FaviconSimilarityQuery(BaseModel):
    """Favicon相似度查询参数"""
    favicon_hash: str = Field(..., description="favicon的MD5哈希值")
    similar: Optional[float] = Field(0.9, description="相似度阈值", ge=0, le=1)
    size: Optional[int] = Field(10, description="返回数量", ge=1, le=50)
    ignore_cache: Optional[bool] = Field(False, description="是否忽略缓存")
    start_time: Optional[str] = Field(None, description="查询起始时间，格式：YYYY-MM-DD HH:MM:SS，时区为UTC")
    end_time: Optional[str] = Field(None, description="查询截止时间，格式：YYYY-MM-DD HH:MM:SS，时区为UTC")
