import msgspec


# 工具函数：定义字段别名和默认值
def alias(name, default):
    return msgspec.field(default=default, name=name)


# ---- HTTP 请求配置 ----
class HttpConfig(msgspec.Struct):
    timeout: float = alias("总超时时间(秒)", 5)  # 总超时时间（秒）
    timeout_read: float = alias("读取超时时间(秒)", 1)  # 单次读取超时
    max_workers: int = alias("并发线程数", 128)  # 并发线程数
    max_redirects: int = alias("最大重定向次数", 3)  # 最大重定向次数
    verify: bool = alias("验证SSL证书", False)  # 是否验证 SSL
    trust_env: bool = alias("使用系统代理", True)  # 是否使用系统代理
    user_agent: str = alias(  # 请求头 UA
        "请求头",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    )


# ---- 分类配置 ----
class ClassificationConfig(msgspec.Struct):
    # 类型映射：小说=0，音频=1，漫画=2，文件=3，视频=4
    # fmt:off
    type_map: dict[str, int] = msgspec.field(
        name="类型",
        default_factory=lambda: {"小说": 0, "音频": 1, "漫画": 2, "文件": 3, "视频": 4},
    )
    # fmt:on

    # 反向映射：数字 → 类型名
    @property
    def reverse_type_map(self) -> dict[int, str]:
        return {v: k for k, v in self.type_map.items()}

    # 分类开关：控制是否从name和comment中提取标签
    use_name_for_classify: bool = msgspec.field(name="从名称中匹配标签", default=False)
    use_comment_for_classify: bool = msgspec.field(
        name="从注释中匹配标签", default=False
    )
    # 控制是否为小说添加默认标签
    use_novel_default_label: bool = msgspec.field(
        name="小说添加类型标签", default=False
    )

    # 标签分类：通过关键词匹配分组
    # fmt:off
    categories: dict[str, list[str]] = msgspec.field(
        name="分类标签规则",
        default_factory=lambda: {
            "精品": ["精", "优", "满"],
            "成人": [
                "18", "黄", "肉", "色", "涩", "瑟", "羞", "成人", "嘿嘿", "刘备",
                "绅士", "淑女", "涩涩", "禁书", "禁漫", "束冠", "不可描述",
                "h", "po", "nsfw", "🥵", "🔞", "🙈"
            ],
            "男频": ["男频"],
            "女频": ["甜", "女频", "言情", "女生", "轻言"],
            "轻文": ["轻"],
            "耽美": ["耽", "长佩", "bl"],
            "正版": ["正版", "付费"],
            "社区": ["论坛", "频道", "社区", "收集", "发布", "置顶"],
            "失效": ["失效", "缺失", "待修", "超时", "未测", "错误"],
        },
    )
    # fmt:on


# ---- URL 过滤配置 ----
class UrlFilterConfig(msgspec.Struct):
    min_html_length: int = alias("最小HTML长度", 200)  # HTML 长度阈值
    min_visible_text_length: int = alias("最小可见文本长度", 50)  # 可见文本长度阈值
    # fmt:off
    keywords: list[str] = msgspec.field(               # 屏蔽词列表
        name="屏蔽关键词",
        default_factory=lambda: [
            "error", "nginx", "banggood", "for sale", "verify code", "make an offer",
            "server is down", "buy this domain", "cheapest domains", "using the domain",
            "sorry", "can not be accessed", "彩票", "棋牌", "错误", "抱歉", "转让", "公司",
            "没有找到站点", "welcome", "无法显示", "无法加载", "域名出售", "正在出售",
        ],
    )
    # fmt:on


# ---- 总配置 ----
class AppConfig(msgspec.Struct):
    use_format: bool = alias("格式化导出JSON", True)  # 导出 JSON 是否格式化
    url_check: bool = alias("启用URL检测", True)  # 是否启用 URL 检测
    use_slice: bool = alias("启用切片保存", True)  # 是否启用切片保存
    auto_close: bool = alias("程序自动关闭", False)  # 程序结束是否自动关闭
    clear_output: bool = alias("导出前清空目录", True)  # 导出前是否清空目录
    deduplicate_by_domain: bool = alias("按域名去重", True)  # 是否按域名去重

    # 子配置对象
    http: HttpConfig = msgspec.field(name="连接测试", default_factory=HttpConfig)
    url_filter: UrlFilterConfig = msgspec.field(
        name="网页过滤", default_factory=UrlFilterConfig
    )
    classify: ClassificationConfig = msgspec.field(
        name="标签分类", default_factory=ClassificationConfig
    )
