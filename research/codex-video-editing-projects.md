# Codex 自動剪輯影片專案：精準版清單產生方式

你要的是「可連網環境下」的精準版清單。由於此執行環境對外連線被 403 阻擋，我已改為提供**可直接執行的自動化腳本**，讓你在可連網主機上一鍵產生最新清單。

## 一鍵產生精準清單

```bash
python research/collect_codex_video_projects.py --token "$GITHUB_TOKEN"
```

輸出檔案：

- `research/codex-video-editing-projects-precise.md`

## 腳本做了什麼

1. 用多組查詢詞向 GitHub Search API 搜尋（Codex/LLM + video editing + ffmpeg/moviepy/whisper）。
2. 對重複 repo 去重。
3. 用關鍵字與 star 數計分，排序出最相關前 20 個專案。
4. 產出 Markdown 表格，包含：repo、score、stars、語言、更新時間、命中理由。

## 建議你如何判斷是否值得用

優先看以下欄位：

- 最近更新（建議 6–12 個月內）
- README 是否有 end-to-end pipeline（輸入素材 → 分段/字幕 → 剪輯 → 輸出）
- 是否直接支援 `ffmpeg` / `moviepy` / `whisper`
- 是否有 CLI 或可重現範例命令

## 若你沒有 GitHub Token

可以直接跑（會較容易撞 rate limit）：

```bash
python research/collect_codex_video_projects.py
```

## 在此受限環境的驗證方式

我已在本地以 dry-run 驗證輸出流程：

```bash
python research/collect_codex_video_projects.py --dry-run
```

