# KeenPie 项目规范

## 推送准则

### data/ 目录禁止推送
- `data/` 目录包含用户个人事项数据（SQLite 数据库），**严禁**提交到版本控制
- `.gitignore` 已配置排除 `data/`，但每次提交前仍需确认 `git status` 中无 data 相关文件
- 如需导出/备份数据，使用应用内设置页的"导出数据"功能

## 技术栈
- Python 3.x + PySide6 + SQLite
- 入口：`main.py`
- 运行：`python main.py`

## 项目结构
```
keen-pie/
├── main.py              # 入口
├── app/
│   ├── db.py            # 数据库层
│   ├── config.py        # 配置管理 (QSettings)
│   ├── color_adapt.py   # 屏幕采样颜色自适应
│   ├── sticky_overlay.py # 置顶便签窗口
│   ├── main_window.py   # 主窗口框架
│   └── pages/
│       ├── home_page.py     # 主页（事项编辑）
│       ├── tasks_page.py    # 事项记录
│       └── settings_page.py # 设置
├── data/                # 用户数据（不推送）
└── requirements.txt
```
