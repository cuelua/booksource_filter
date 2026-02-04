<p align="center">
  <img src="./src/resources/images/logo.ico" alt="Logo" width="120"/>
</p>

<p align="center">
  <img src="https://img.shields.io/github/license/cuelua/booksource_filter?color=%23ffe3e8" alt="License"/>
  <img src="https://img.shields.io/badge/platform-Windows-%23bd7d82" alt="Platform"/>
  <a href="https://github.com/cuelua/booksource_filter/releases">
    <img src="https://img.shields.io/github/downloads/cuelua/booksource_filter/total?color=%236a3239" alt="Downloads"/>
  </a>
</p>

# 📚 书源筛选工具

用于筛选、分类和清理阅读书源，支持去重、分组和测试网页。

# 🧩 使用方法

- 运行程序
- 将书源文件放入 `导入`文件夹
- 筛选结果会生成到 `导出`文件夹

# 📁 目录结构

```
程序目录
├── 书源筛选.exe
├── 配置.json                 # 首次运行生成的配置文件
├── 导入/                       # 放入待筛选的书源文件
└── 导出/                       # 程序输出的筛选结果
    ├── 其他.json             # 获取的字段不属于常规网址的书源
    ├── 无效.json             # 不可访问或网页不符合要求的书源
    ├── 重复.json             # 按域名去重后被判定为重复的书源
    └── 合格.json             # 按域名去重后被判定为合格的书源
```

# ⚙️ 功能说明

- 首次运行会创建默认配置文件
- 测试网页
  - 根据 `bookSourceUrl`进行访问测试
  - 可成功访问的会根据黑白名单进行筛选
  - 测试完会根据响应时间排序
- 重新分组
  - 根据 `bookSourceGroup`中的关键字重新分组
  - 可选择是否根据 `bookSourceName`和 `bookSourceComment`中的关键字进行分组
- 去重处理
  - 按域名去重
- 保存时会根据 `bookSourceType`的类别分组保存
- 可选择是否按照 `分类标签规则`的顺序根据 `bookSourceGroup`进行分组保存
