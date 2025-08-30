Echo Merge Plugin

Overview
- Adds a one-time task “合成聲骸” that performs bulk Echo merging in the Data Bank/Data Dock screen.
- Feature-first approach for multi-language: prefers UI features (`button_echo_merge`, `data_merge_*`, `confirm_btn_*`), with OCR fallbacks for common translations.

Usage
- Run via `main_plugins.py`: this injects the plugin task without modifying upstream files.
- In the UI, select “合成聲骸” to start. Works from game world; it opens the ESC menu and navigates itself.

Language Support
- Features are language-agnostic. For OCR fallbacks, patterns include:
  - Data Bank: 中文(数据坞/數據塢/資料庫), English(Data Bank/Data Dock), 日本語(データバンク), 한국어(데이터뱅크)
  - Bulk Merge: 中文(批量融合/批量合成/合成), English(Bulk Merge/Echo Merge)
- If your language doesn’t match, open Data Bank manually; the plugin will continue from the merge screen.

Notes
- Requires 16:9 resolution (>= 1600x900) per project guidelines.
- Select-All is clicked once per round; then Merge; handles first-time confirm and closes rewards dialogs. Repeats until no more items can be merged.

