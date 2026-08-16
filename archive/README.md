# archive/ — 历史脚本归档

> 2026-08-06 接手整理时，将根目录已完成使命的一次性脚本按任务分组归档至此。
> 归档前已把脚本内的相对路径引用统一改为绝对路径（`e:\wenan catch\...`），从任意目录运行不受影响。
> 这些脚本对应的源文档与产物（`*.pptx`/`*.pdf`/`*.html`）仍保留在项目根目录，未被移动。

## 分组

| 目录 | 内容 | 对应任务（时间） |
|------|------|------------------|
| `fengshui_ppt/` | 风水课程 HTML/PPT 生成与后处理脚本（build_course、build_final、apply_clean、relayout、ai_match 等 15 个） | 风水下罗经秘法 / 风水课程幻灯片（2026-07-20 ~ 07-31） |
| `qimen_ppt_v1/` | 奇门讲义第一代 PPT 脚本（build_full_ppt、build_qimen_ppt、qimen_chart_svg 等 4 个） | 成慈高级奇门讲义（2026-07-24），已被 docx2ppt 流水线取代 |
| `html_tools/` | HTML/PDF 转换与调试工具（base64 嵌入/还原、绝对/相对路径切换、Playwright 转 PDF 等 12 个） | 风水 HTML 页面嵌入图片（2026-07-20 ~ 07-25） |
| `scraper_tools/` | 主线采集系统的配套查询/导出工具（check_db、show_text、export_full、backfill、add_target 等 9 个） | 抖音文案采集调试（2026-07-09 ~ 07-20） |

## 注意

- 部分脚本仍引用微信下载目录 `C:\Users\Kimura\Documents\xwechat_files\...` 或桌面 `C:\Users\Kimura\Desktop\待处理\...` 中的源文档，换机后需更新（见 `docs/codebase/CONCERNS.md`）。
- 奇门 V1 的四份脚本已被 `docx2ppt/`（parse→chart→deck 流水线）取代，保留仅供回溯排盘图 SVG 的实现。
- 若需要恢复某个脚本到根目录：`git mv archive/<组>/<文件> <文件>`。
