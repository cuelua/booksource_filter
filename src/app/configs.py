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

    # 标签分类：通过关键词匹配分组
    # fmt:off
    categories: dict[str, list[str]] = msgspec.field(
        name="分类标签规则",
        default_factory=lambda: {
            "成人": [
                "18", "黄", "肉", "色", "涩", "瑟", "羞", "成人", "嘿嘿", "刘备",
                "绅士", "淑女", "涩涩", "禁书", "禁漫", "束冠", "不可描述",
                "h", "po", "nsfw", "🥵", "🔞", "🙈"
            ],
            "精品": ["精", "优", "满"],
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
    # fmt:off
    white_list: list[str] = msgspec.field(
        name="白名单关键词",
        default_factory=lambda: [
            # 小说类
            "小说", "章节", "目录", "正文", "阅读", "书架", "书单",
            "作者", "作品", "更新", "连载", "完本", "简介",
            "玄幻", "武侠", "都市", "言情", "历史", "科幻",
            # 漫画类
            "漫画", "连载漫画", "章节列表", "话", "话数", "条漫",
            "国漫", "日漫", "韩漫", "漫画阅读",
            # 听书 / 音频类
            "听书", "有声", "音频", "播放", "收听", "主播",
            "有声小说", "音频小说",
            # 文库 / 资料类
            "文库", "资料", "文档", "教程", "论文", "下载",
            "电子书", "PDF", "TXT",
            # 视频类
            "视频", "剧集", "番剧", "影视", "在线播放", "更新至",
        ]
    )
    # fmt:on

    # fmt:off
    black_list: list[str] = msgspec.field(
        name="黑名单关键词",
        default_factory=lambda: [
            "for sale", "make an offer", "buy this domain",
            "cheapest domains", "using the domain",
            "verify code", "captcha", "cloudflare challenge",
            "server is down", "nginx error", "bad gateway",
            "502 bad gateway", "403 forbidden", "404 not found",
            "域名出售", "正在出售", "出售中",
            "verify your browser", "checking your browser",
            "access denied", "security check", "ddos protection",
            "maintenance", "under maintenance",
            "suspended", "account suspended",
            "彩票", "棋牌", "色情", "博彩", "错误", "抱歉", "sorry", "welcome",
            "无法显示", "无法加载", "没有找到站点", "转让" 
        ]
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
    # 是否按照类型或标签保存
    save_by_type: bool = msgspec.field(name="按类型分别保存", default=True)
    save_by_category: bool = msgspec.field(name="按标签分别保存", default=True)
    # 是否从name和comment中提取标签
    name_for_classify: bool = msgspec.field(name="从名称中匹配标签", default=False)
    comment_for_classify: bool = msgspec.field(name="从注释中匹配标签", default=False)
    # 控制是否为默认类型添加标签
    use_novel_default_label: bool = msgspec.field(
        name="默认类型添加标签", default=False
    )

    # 子配置对象
    http: HttpConfig = msgspec.field(name="连接测试", default_factory=HttpConfig)
    url_filter: UrlFilterConfig = msgspec.field(
        name="网页过滤", default_factory=UrlFilterConfig
    )
    classify: ClassificationConfig = msgspec.field(
        name="标签分类", default_factory=ClassificationConfig
    )
