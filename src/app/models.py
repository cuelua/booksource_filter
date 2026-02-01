import msgspec


# 基础模型：支持 camelCase 命名，省略默认值
class BaseModel(msgspec.Struct, omit_defaults=True, rename="camel"):
    pass


# ---- 规则模型（用于解析书源规则） ----


# 通用规则基类：书籍列表、名称、作者等
class RuleBase(BaseModel, kw_only=True):
    book_list: str = ""
    name: str = ""
    author: str = ""
    kind: str = ""
    word_count: str = ""
    last_chapter: str = ""
    intro: str = ""
    cover_url: str = ""
    book_url: str = ""


# 搜索规则（继承通用规则）
class RuleSearch(RuleBase):
    pass


# 探索规则（继承通用规则）
class RuleExplore(RuleBase):
    pass


# 书籍信息规则
class RuleBookInfo(BaseModel, kw_only=True):
    init: str = ""
    name: str = ""
    author: str = ""
    kind: str = ""
    word_count: str = ""
    last_chapter: str = ""
    intro: str = ""
    cover_url: str = ""
    toc_url: str = ""  # 目录 URL


# 目录规则
class RuleToc(BaseModel, kw_only=True):
    chapter_list: str = ""
    chapter_name: str = ""
    chapter_url: str = ""
    is_volume: str = ""  # 是否分卷
    is_vip: str = ""  # 是否 VIP
    update_time: str = ""
    next_toc_url: str = ""  # 下一页目录 URL


# 内容规则
class RuleContent(BaseModel, kw_only=True):
    web_js: str = ""  # 网页 JS
    content: str = ""  # 正文内容
    next_content_url: str = ""  # 下一页内容 URL
    source_regex: str = ""  # 内容提取正则
    replace_regex: str = ""  # 内容替换正则
    image_style: str = ""  # 图片样式


# ---- 核心模型：书源 ----
class BookSource(BaseModel, kw_only=True, dict=True):
    book_source_url: str  # 书源 URL
    book_source_name: str  # 书源名称
    book_source_group: str = ""  # 分组标签
    book_source_type: int  # 类型（小说/漫画/音频等）
    enabled: bool  # 是否启用
    enabled_explore: bool  # 是否启用探索
    weight: int  # 权重
    custom_order: int  # 自定义排序
    last_update_time: int | str | None = None
    book_source_comment: str = ""  # 注释
    login_url: str = ""  # 登录 URL
    login_ui: str = ""  # 登录界面
    login_check_js: str = ""  # 登录检测 JS
    concurrent_rate: str = ""  # 并发速率
    header: str = ""  # 请求头
    book_url_pattern: str = ""  # 书籍 URL 模式
    search_url: str = ""  # 搜索 URL
    explore_url: str = ""  # 探索 URL

    # 规则对象（可选）
    rule_search: RuleSearch | None = None
    rule_explore: RuleExplore | None = None
    rule_book_info: RuleBookInfo | None = None
    rule_toc: RuleToc | None = None
    rule_content: RuleContent | None = None

    respond_time: int | str | None = None  # 响应时间（测速结果）

    def __post_init__(self):
        # 初始化时附加 domain 字段（域名）
        self.domain: str = ""
