import re
import time

from qfluentwidgets import FluentIcon

from ok import Logger
from src.task.BaseWWTask import BaseWWTask
from src.task.WWOneTimeTask import WWOneTimeTask

logger = Logger.get_logger(__name__)


class BulkFusionDiscardTask(WWOneTimeTask, BaseWWTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "合成聲骸"
        self.description = "ESC→数据坞/數據屋→左側第四→批量融合→篩選=已棄置→全選→批量融合，直至融合次數=0"
        self.icon = FluentIcon.FILTER
        self.default_config.update({
            '_enabled': True,
            # 使用底線前綴，避免 GUI 嘗試將 dict 類型渲染為配置項而報錯
            '_fallback_coords': {
                'left_menu_4th': (0.04, 0.56),      # 左側第4個圖標
                'select_all': (0.26, 0.91),         # 全選（底部偏左）
                'bulk_fusion_tab': (0.18, 0.20),    # 「批量融合」頁籤（上半部）
                'bulk_fusion_exec': (0.68, 0.91),   # 「批量融合」執行按鈕（底部偏右）
                'filter_icon': (0.04, 0.92),        # 篩選小圖標（左下半部，依你環境校正）
                'close_reward_blank': (0.53, 0.05), # 空白區域
                'first_time_checkbox': (0.49, 0.55) # 「本次登陸不再顯示」複選框大致位置
            }
        })

        # 文本匹配（簡繁/英文 兼容）
        self.text_datahouse = re.compile(r'(数据坞|數據坞|数据屋|數據屋)')
        self.text_bulk_fusion = re.compile(r'(批量融合|Bulk\s*Fusion)', re.IGNORECASE)
        self.text_filter = re.compile(r'(筛选|篩選|Filter)', re.IGNORECASE)
        # 僅匹配「已棄置」，排除「已棄置優先」之類的排序項
        self.text_discarded = re.compile(r'(已弃置(?!优先)|已棄置(?!優先)|Discarded(?!\s*First))', re.IGNORECASE)
        self.text_confirm = re.compile(r'(确认|確認|確定|确定|应用|應用|Apply|保存|Save|Confirm|OK)', re.IGNORECASE)
        self.text_select_all = re.compile(r'(全选|全選|Select\s*All)', re.IGNORECASE)
        self.text_select_all_checked = re.compile(r'(全[选選]\s*[√vV])', re.IGNORECASE)
        # 「本次登陸不再顯示」等變體（放寬匹配，以免地區版字串略有不同）
        self.text_dont_show = re.compile(r'((本次登录|本次登陸).{0,4})?(不再显示|不再顯示|不显示|不顯示)', re.IGNORECASE)
        self.text_got_echo = re.compile(r'(获得声骸|獲得聲骸|Obtained\s*Echo|Echo\s*Obtained)', re.IGNORECASE)
        self.text_fusion_count = re.compile(
            r'((数据|數據)\s*融合\s*(次数|次數)\s*[=:：]?\s*(\d+))|((Fusion|Merge)\s*(Count|Attempts)\s*[=:：]?\s*(\d+))',
            re.IGNORECASE)

    def run(self):
        WWOneTimeTask.run(self)
        self.ensure_main()
        self.open_esc_menu()

        # 進入數據坞/屋
        self.wait_click_ocr(match=self.text_datahouse, box="right", raise_if_not_found=True, settle_time=0.2)
        # 確認標題出現（左上）
        self.wait_ocr(match=self.text_datahouse, box="top_left", raise_if_not_found=True, settle_time=0.2)

        # 左側第4個圖標
        self._click_fallback_or_ocr('left_menu_4th', ocr=None)
        self.sleep(0.8)

        # 等待頁面內容載入（嘗試看到「批量融合/Filter/全選」任一關鍵字）
        if not (self.wait_ocr(match=self.text_bulk_fusion, raise_if_not_found=False, settle_time=0.2, time_out=2)
                or self.wait_ocr(match=self.text_filter, raise_if_not_found=False, settle_time=0.2, time_out=2)
                or self.wait_ocr(match=self.text_select_all, raise_if_not_found=False, settle_time=0.2, time_out=2)):
            # 再點一次左側第4個圖標，避免第一次點擊未生效
            self._click_fallback_or_ocr('left_menu_4th', ocr=None)
            self.sleep(0.8)

        # 進入批量融合頁（上半部）
        self._click_fallback_or_ocr('bulk_fusion_tab', ocr=self.text_bulk_fusion, box_hint='top', must=True)
        # 簡單確認頁面是否已切換（嘗試檢測關鍵元素）
        if not (self.wait_ocr(match=self.text_select_all, box='bottom', raise_if_not_found=False, time_out=2) or
                self.wait_ocr(match=self.text_bulk_fusion, box='top', raise_if_not_found=False, time_out=2)):
            # 再嘗試一次點擊
            self._click_fallback_or_ocr('bulk_fusion_tab', ocr=self.text_bulk_fusion, box_hint='top', must=False)
        self.sleep(0.8)

        # 篩選→已棄置→確認
        self._apply_discarded_filter()

        # 迴圈融合直至融合次數=0
        self._loop_until_zero()

    # --- helpers ---
    def _apply_discarded_filter(self):
        # 直接用座標點擊篩選圖標，不依賴 OCR
        if not self._click_fallback_or_ocr('filter_icon', ocr=None, box_hint=None, must=False):
            # 退而求其次：在預估位置附近掃描多個點位；仍失敗則在左下狹窄 ROI 內掃描
            if not self._scan_click_around_filter_icon():
                if not self._scan_click_in_roi(0.02, 0.86, 0.18, 0.96):
                    # 最後保險：點靠近左下角的常見位置
                    self.click_relative(0.12, 0.92, after_sleep=0.5)

        # 確保篩選菜單已展開（等待看到「已棄置」類項）
        if not self.wait_ocr(match=self.text_discarded, raise_if_not_found=False, settle_time=0.2, time_out=2):
            # 再點一次篩選（仍只用座標與掃描）
            if not self._click_fallback_or_ocr('filter_icon', ocr=None, box_hint=None, must=False):
                self._scan_click_around_filter_icon()
            self.wait_ocr(match=self.text_discarded, raise_if_not_found=False, settle_time=0.2, time_out=2)

        # 勾選「已棄置」（或「已棄置優先」等變體）
        self.wait_click_ocr(match=self.text_discarded, raise_if_not_found=True, settle_time=0.2)
        # 有些 UI 不需要確認；若找不到確認按鈕，直接點擊空白區域關閉彈窗並繼續
        if not self.wait_click_ocr(match=self.text_confirm, raise_if_not_found=False, settle_time=0.2):
            self.log_debug('confirm button not found; close panel by clicking blank area')
            self.click_relative(0.5, 0.5, after_sleep=0.3)
        self.sleep(0.5)

    def _loop_until_zero(self):
        first_time = True
        while True:
            # 先確保「全選」為勾選狀態
            if not self._ensure_select_all_checked():
                # 再保險點，再嘗試一次
                self._click_fallback_or_ocr('select_all', ocr=self.text_select_all, box_hint='bottom')
                self._ensure_select_all_checked()

            # 再讀取剩餘次數（在全選之後檢測）
            count = self._read_fusion_count()
            self.log_info(f'当前數據融合次數: {count}')
            if count is not None and count <= 0:
                self.log_info('數據融合次數=0，停止。')
                break

            # 批量融合（執行按鈕在底部區域）
            self._click_fallback_or_ocr('bulk_fusion_exec', ocr=self.text_bulk_fusion, box_hint='bottom_right', must=True)

            if first_time:
                self._handle_first_time_dialog()
                first_time = False

            # 等待結果，關閉獲取面板
            self._wait_and_close_reward()

            # 小等待使 UI 穩定
            self.sleep(0.4)

    def _read_fusion_count(self):
        # 讀取「數據融合次數」文本（批量融合按鈕上方區域）
        box = self.box_of_screen(0.58, 0.80, 0.93, 0.90, name='fusion_count_area')
        texts = self.ocr(box=box, match=self.text_fusion_count)
        if not texts:
            # 若未匹配到，嘗試整個右下區域
            texts = self.ocr(box=self.box_of_screen(0.50, 0.75, 0.98, 0.95), match=self.text_fusion_count)
        if texts:
            # 取第一個匹配，提取數字
            for t in texts:
                m = self.text_fusion_count.search(t.name)
                if m:
                    # 模式包含中英兩種分支，數字分別落在不同捕獲組。
                    # 為了兼容，從所有捕獲組中反向尋找第一個純數字的組。
                    try:
                        for grp in reversed(m.groups() or ()):  # type: ignore[arg-type]
                            if grp and str(grp).isdigit():
                                return int(grp)
                    except Exception:
                        pass

        # Fallback：直接拼接 ROI 內的 OCR 文本後再整體匹配
        try:
            all_tokens = self.ocr(box=box)
            joined = ''.join([t.name for t in (all_tokens or [])])
            if not joined:
                # 再嘗試更大的右下區域
                all_tokens = self.ocr(box=self.box_of_screen(0.50, 0.75, 0.98, 0.95))
                joined = ''.join([t.name for t in (all_tokens or [])])
            if joined:
                m = self.text_fusion_count.search(joined)
                if m:
                    for grp in reversed(m.groups() or ()):  # type: ignore[arg-type]
                        if grp and str(grp).isdigit():
                            return int(grp)
                # 寬鬆匹配：尋找「(次|次數|次数|Count|Attempts) ... 數字」
                loose_patterns = [
                    re.compile(r'(次|次數|次数)[^\d]{0,6}(\d+)', re.IGNORECASE),
                    re.compile(r'(Count|Attempts)[^\d]{0,6}(\d+)', re.IGNORECASE),
                ]
                for p in loose_patterns:
                    m2 = p.search(joined)
                    if m2:
                        num = m2.group(2)
                        if num and num.isdigit():
                            return int(num)
        except Exception:
            pass
        return None

    def _handle_first_time_dialog(self):
        # 有些環境第一次融合會彈窗：盡量勾選「本次登陸不再顯示」，否則點空白返回融合頁面
        # 1) 嘗試全螢幕點擊「不再顯示」
        clicked = self.wait_click_ocr(match=self.text_dont_show, box=None, raise_if_not_found=False, settle_time=0.2)
        # 2) 嘗試全螢幕點擊「確認」
        clicked_confirm = self.wait_click_ocr(match=self.text_confirm, box=None, raise_if_not_found=False, settle_time=0.2)
        if not clicked and not clicked_confirm:
            # 3) 都沒看到，直接點空白區域關閉任何可能的遮罩
            self.click_relative(0.5, 0.5, after_sleep=0.3)
            # 4) 確保回到融合頁面（底部應可見全選/批量融合）
            if not (self.wait_ocr(match=self.text_select_all, box='bottom', raise_if_not_found=False, time_out=1.0)
                    or self.wait_ocr(match=self.text_bulk_fusion, box='bottom_right', raise_if_not_found=False, time_out=1.0)):
                self._click_fallback_or_ocr('bulk_fusion_exec', ocr=self.text_bulk_fusion, box_hint='bottom_right', must=False)
                self.sleep(0.3)
                self.wait_ocr(match=self.text_select_all, box='bottom', raise_if_not_found=False, time_out=1.0)

    def _wait_and_close_reward(self):
        # 等「获得声骸/獲得聲骸」或數秒超時
        got = self.wait_ocr(match=self.text_got_echo, box="top", raise_if_not_found=False, settle_time=0.8,
                            time_out=6)
        # 點空白區域關閉
        x, y = self.default_config['_fallback_coords']['close_reward_blank']
        self.click_relative(x, y, after_sleep=0.4)

        # 關閉後，確保回到融合畫面：
        # 1) 等待底部『全選/批量融合』重新可見
        if not (self.wait_ocr(match=self.text_select_all, box='bottom', raise_if_not_found=False, time_out=1.2)
                or self.wait_ocr(match=self.text_bulk_fusion, box='bottom_right', raise_if_not_found=False, time_out=1.2)):
            # 2) 若仍不可見，主動再點一次『批量融合』執行鍵以回到融合畫面
            self._click_fallback_or_ocr('bulk_fusion_exec', ocr=self.text_bulk_fusion, box_hint='bottom_right', must=False)
            self.sleep(0.4)
            # 3) 再等待一次確認已回到融合畫面
            self.wait_ocr(match=self.text_select_all, box='bottom', raise_if_not_found=False, time_out=1.5)

    def _click_fallback_or_ocr(self, key, ocr=None, box_hint=None, must=False):
        """
        先用 OCR 點擊，失敗則用預設相對座標；must=True 表示兩者都失敗則拋例外。
        """
        if ocr is not None:
            found = self.wait_click_ocr(match=ocr, box=box_hint if box_hint else None, raise_if_not_found=False,
                                        settle_time=0.3)
            if found:
                return True
            # 再嘗試整個畫面（無區域限制），以防 UI 位置與分辨率不同
            found = self.wait_click_ocr(match=ocr, box=None, raise_if_not_found=False, settle_time=0.3)
            if found:
                return True
        # fallback
        coords = self.default_config.get('_fallback_coords', {}).get(key)
        if coords and isinstance(coords, (tuple, list)) and len(coords) == 2:
            self.click_relative(coords[0], coords[1], after_sleep=0.5)
            return True
        if must:
            raise Exception(f'Failed to click {key} via OCR and fallback')
        return False

    def _ensure_select_all_checked(self):
        """確保『全選』處於勾選狀態；若未勾選則嘗試點擊一次並再次檢查。"""
        # 先嘗試檢測已勾選狀態
        if self.wait_ocr(match=self.text_select_all_checked, box='bottom', raise_if_not_found=False, time_out=0.8):
            return True
        # 若未勾選，嘗試點擊『全選』
        self._click_fallback_or_ocr('select_all', ocr=self.text_select_all, box_hint='bottom', must=False)
        # 再次檢查是否已勾選
        if self.wait_ocr(match=self.text_select_all_checked, box='bottom', raise_if_not_found=False, time_out=1.2):
            return True
        # 有些字型不顯示√，放寬：只要能看到『全選』即可接受
        return self.wait_ocr(match=self.text_select_all, box='bottom', raise_if_not_found=False, time_out=0.8)

    def _scan_click_around_filter_icon(self):
        """
        在預估的篩選圖標座標附近做小範圍的格點掃描點擊。
        點擊後檢測是否出現「已棄置」字樣，若出現代表面板已展開。
        返回 True 表示成功展開，False 表示未展開。
        """
        base = self.default_config.get('_fallback_coords', {}).get('filter_icon', (0.12, 0.92))
        # 相對偏移（畫面百分比），以 2% 為步距，優先點附近的方位
        deltas = [
            (0.00, 0.00), (-0.02, 0.00), (0.02, 0.00), (0.00, -0.02), (0.00, 0.02),
            (-0.02, -0.02), (0.02, -0.02), (-0.02, 0.02), (0.02, 0.02),
            (-0.03, 0.00), (0.03, 0.00), (0.00, -0.03), (0.00, 0.03)
        ]
        for dx, dy in deltas:
            x = min(max(base[0] + dx, 0.0), 1.0)
            y = min(max(base[1] + dy, 0.0), 1.0)
            self.click_relative(x, y, after_sleep=0.3)
            if self.wait_ocr(match=self.text_discarded, raise_if_not_found=False, settle_time=0.2, time_out=1):
                self.log_debug(f'filter panel opened via scan at ({x:.2f}, {y:.2f})')
                return True
        self.log_debug('scan_click_around_filter_icon failed to open panel')
        return False

    def _scan_click_in_roi(self, x1, y1, x2, y2, steps_x: int = 6, steps_y: int = 4):
        """
        在給定 ROI 內做粗網格掃描點擊，嘗試打開篩選面板。
        參數 steps_x/steps_y 控制採樣點數量，默認 6x4 共 24 點。
        成功打開（檢測到「已棄置」）返回 True，否則 False。
        """
        try:
            sx = max(2, steps_x)
            sy = max(2, steps_y)
            for iy in range(sy):
                for ix in range(sx):
                    rx = x1 + (x2 - x1) * (ix + 0.5) / sx
                    ry = y1 + (y2 - y1) * (iy + 0.5) / sy
                    self.click_relative(rx, ry, after_sleep=0.25)
                    if self.wait_ocr(match=self.text_discarded, raise_if_not_found=False, settle_time=0.2, time_out=0.8):
                        self.log_debug(f'filter panel opened via ROI scan at ({rx:.2f}, {ry:.2f})')
                        return True
            return False
        except Exception as e:
            self.log_debug(f'_scan_click_in_roi error: {e}')
            return False
