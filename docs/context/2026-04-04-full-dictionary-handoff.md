# 2026-04-04 全量词库接入交接文档

## 本轮目标

- 将用户下载到 `D:\todowloads` 的全量词库源文件接入项目
- 生成全量 SQLite 词库与 package
- 构建带全量词库的 Android APK
- 为下个对话准备可直接续接的压缩上下文

## 当前结论

- 全量源文件已接入并可被脚本直接解析
- 全量词库 SQLite 已生成成功
- Android package 已导出成功
- Debug APK 已构建成功，并复制到桌面
- Python 测试与 Android 单测均通过

## 关键路径与产物

- 仓库主工作路径：`C:\Users\10379\android_vocab_content`
- 原始仓库路径：`E:\aiproduct\安卓单词软件\content`
- 全量日语源：`C:\Users\10379\android_vocab_content\sources\jmdict\JMdict.gz`
- 全量法语源：`C:\Users\10379\android_vocab_content\sources\kaikki_fr\raw-wiktextract-data.jsonl.gz`
- Tatoeba 原始档案：`C:\Users\10379\android_vocab_content\sources\tatoeba\sentences.tar.bz2`
- Tatoeba 关系档案：`C:\Users\10379\android_vocab_content\sources\tatoeba\links.tar.bz2`
- 全量数据库：`C:\Users\10379\android_vocab_content\artifacts\prototype.db`
- 发布包数据库：`C:\Users\10379\android_vocab_content\artifacts\package\dictionary.db`
- 发布包清单：`C:\Users\10379\android_vocab_content\artifacts\package\manifest.json`
- 可安装 APK：`C:\Users\10379\Desktop\app-debug-full-dictionary.apk`

## 数据规模

- 总词条数：`2,359,088`
- 日语词条：`216,097`
- 法语词条：`2,142,991`
- `prototype.db` 大小：`1,376,002,048` bytes
- `app-debug.apk` 大小：`1,385,651,011` bytes

## 本轮关键实现

### 1. 全量源文件解析

- `src/dict_feasibility/source_paths.py`
  - 增加 full / fixture 自动解析逻辑
  - 普通 CLI 默认优先走 `sources/`
  - pytest 子进程默认优先走 fixture
- `src/dict_feasibility/jmdict_parser.py`
  - 支持直接读取 `JMdict.gz`
- `src/dict_feasibility/kaikki_parser.py`
  - 支持直接读取 `.jsonl.gz`
  - 能从 `translations` 中抽取已有中文释义填入 `meaning_zh`
- `scripts/parse_jmdict.py`
- `scripts/parse_kaikki_fr.py`

### 2. 全量构建改为流式，避免内存爆炸

- `src/dict_feasibility/sqlite_builder.py`
- `src/dict_feasibility/translation_pipeline.py`
- `src/dict_feasibility/reporting.py`
- `scripts/build_sqlite.py`
- `scripts/sample_report.py`

要点：

- 不再把全量 JSONL 一次性读入内存
- 统一改为迭代器 / 流式写 SQLite
- 样本报告也改为单遍统计

### 3. Android 打包修复

- `android-app/app/build.gradle.kts`
  - 增加 `androidResources { noCompress += "db" }`

原因：

- 全量 `dictionary.db` 太大
- 之前 `:app:compressDebugAssets` 在压缩资产时直接 `Java heap space`
- 改成 `.db` 不压缩后，`assembleDebug` 成功

### 4. 回归测试

- `tests/test_full_source_parsers.py`
- `tests/test_source_paths.py`
- `tests/test_build_sqlite_streaming.py`
- `tests/test_android_project_layout.py`

新增点：

- 校验全量源路径解析
- 校验 gzip 源解析
- 校验 SQLite 构建走流式写入
- 校验 Android 侧保留 `.db` 非压缩打包

## 已执行并确认通过的命令

在 `C:\Users\10379\android_vocab_content`：

```powershell
python scripts/render_feasibility_report.py
python scripts/build_sqlite.py
python scripts/export_dictionary_package.py
python -m pytest
```

验证结果：

- `python -m pytest`：`60 passed`

在 `C:\Users\10379\android_vocab_content\android-app`：

```powershell
.\gradlew.bat clean testDebugUnitTest assembleDebug
```

验证结果：

- Android 构建成功
- `BUILD SUCCESSFUL`

## 当前仍存在的产品限制

### 1. 中文匹配质量仍不够高

- 日语 `JMdict` 原始源中几乎没有中文释义
- 法语 `Kaikki` 全量数据里只有少量条目自带中文翻译
- 当前 `manifest.json` 中可见：
  - 日语 `already_translated = 0`
  - 法语 `already_translated = 11533`

这意味着：

- 现在“全量词库接入”已经完成
- 但“高质量中文查词体验”还没有完成

### 2. Tatoeba 全量例句尚未真正接入日语链路

- 原始 `sentences.tar.bz2` / `links.tar.bz2` 已放入 `sources/tatoeba`
- 但当前日语例句提取仍未完成正式的 lemma-to-sentence 关联
- 现阶段日语例句覆盖仍然有限

### 3. APK 体积非常大

- 现在的 Debug APK 约 `1.386 GB`
- 可以安装测试，但分发、更新、首次安装体验都很差

## 下个对话最优先的工作

按优先级建议：

1. 做“中文释义覆盖率提升”方案
   - 优先引入离线中译资源或映射表
   - 避免直接对 200 多万词条走付费翻译 API
2. 做 Tatoeba 全量例句关联
   - 至少先把高频词的日语例句补齐
3. 做词库瘦身与发布方案
   - 按语言拆包
   - 按频率分层
   - 首包仅内置核心词库，其余走下载包
4. 做 Release 包验证
   - 当前只验证了 Debug APK

## 明确不要重复做的事

- 不要再回退到 sample 词库路径
- 不要删除 `noCompress += "db"`，否则大库 APK 再次无法构建
- 不要默认启用 OpenAI 大规模翻译
  - 当前环境中虽然检测到 API 相关环境变量
  - 但 200 多万词条的批量翻译可能产生明显费用
  - 若要做，必须先单独确认成本策略

## 可直接引用的关键文件

- `src/dict_feasibility/source_paths.py:1`
- `src/dict_feasibility/jmdict_parser.py:1`
- `src/dict_feasibility/kaikki_parser.py:1`
- `src/dict_feasibility/sqlite_builder.py:1`
- `scripts/build_sqlite.py:1`
- `scripts/export_dictionary_package.py:1`
- `android-app/app/build.gradle.kts:1`
- `tests/test_android_project_layout.py:1`
- `docs/feasibility-report.md:1`
- `artifacts/package/manifest.json:1`

