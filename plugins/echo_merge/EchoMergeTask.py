import re
from qfluentwidgets import FluentIcon

from ok import Logger
from src.task.WWOneTimeTask import WWOneTimeTask
from src.task.BaseWWTask import BaseWWTask


logger = Logger.get_logger(__name__)


class EchoMergeTask(WWOneTimeTask, BaseWWTask):
    """
    Bulk Echo Fusion (Discarded only):
    ESC → Data Bank → Left menu 4th → Bulk Fusion → Filter=Discarded → Select All → Bulk Fusion, until Fusion Count = 0

    Multilingual and robust: OCR-first, coordinate fallback, with small-area scan around filter icon.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "合成聲骸"
        self.description = "ESC→数据坞/數據屋→左側第四→批量融合→篩選=已棄置→全選→批量融合，直至融合次數=0"
        self.icon = FluentIcon.FILTER
        self.default_config.update({
            "_enabled": False,
            "_fallback_coords": {
                "left_menu_4th": (0.04, 0.56),
                "select_all": (0.26, 0.91),
                "bulk_fusion_tab": (0.18, 0.20),
                "bulk_fusion_exec": (0.68, 0.91),
                "filter_icon": (0.04, 0.92),
                "close_reward_blank": (0.53, 0.05),
                "first_time_checkbox": (0.49, 0.55),
            },
        })

        # Text patterns (CN/TW/EN)
        self.text_datahouse = re.compile(r"(数据坞|數據坞|數據塢|数据屋|數據屋|資料庫|Data\s*Bank|Data\s*Dock)", re.IGNORECASE)
        self.text_bulk_fusion = re.compile(r"(批量融合|Bulk\s*Fusion|Echo\s*Merge|Merge)", re.IGNORECASE)
        self.text_filter = re.compile(r"(筛选|篩選|Filter)", re.IGNORECASE)
        self.text_discarded = re.compile(r"(已弃置(?!优先)|已棄置(?!優先)|Discarded(?!\s*First))", re.IGNORECASE)
        self.text_confirm = re.compile(r"(确认|確認|確定|确定|应用|應用|Apply|保存|Save|Confirm|OK|Yes)", re.IGNORECASE)
        self.text_select_all = re.compile(r"(全选|全選|Select\s*All)", re.IGNORECASE)
        self.text_select_all_checked = re.compile(r"(全[选選]\s*[√vV])", re.IGNORECASE)
        self.text_dont_show = re.compile(r"((本次登[录錄入]|本次登入).{0,4})?(不再显示|不再顯示|不显示|不顯示)", re.IGNORECASE)
        self.text_got_echo = re.compile(r"(获得声骸|獲得聲骸|Obtained\s*Echo|Echo\s*Obtained)", re.IGNORECASE)
        self.text_fusion_count = re.compile(
            r"((数据|數據)\s*融合\s*(次数|次數)\s*[=:：]?\s*(\d+))|((Fusion|Merge)\s*(Count|Attempts)\s*[=:：]?\s*(\d+))",
            re.IGNORECASE,
        )

    # ---------- High-level flow ----------
    def run(self):
        WWOneTimeTask.run(self)
        self.ensure_main()
        self.open_esc_menu()

        # Enter Data Bank (right menu)
        self.wait_click_ocr(match=self.text_datahouse, box="right", raise_if_not_found=True, settle_time=0.2)
        self.wait_ocr(match=self.text_datahouse, box="top_left", raise_if_not_found=True, settle_time=0.2)

        # Left menu 4th
        self._click_fallback_or_ocr("left_menu_4th", ocr=None)
        self.sleep(0.8)

        # Wait for basic elements
        if not (
            self.wait_ocr(match=self.text_bulk_fusion, raise_if_not_found=False, settle_time=0.2, time_out=2)
            or self.wait_ocr(match=self.text_filter, raise_if_not_found=False, settle_time=0.2, time_out=2)
            or self.wait_ocr(match=self.text_select_all, raise_if_not_found=False, settle_time=0.2, time_out=2)
        ):
            self._click_fallback_or_ocr("left_menu_4th", ocr=None)
            self.sleep(0.8)

        # Enter Bulk Fusion tab (top area)
        self._click_fallback_or_ocr("bulk_fusion_tab", ocr=self.text_bulk_fusion, box_hint="top", must=True)
        if not (
            self.wait_ocr(match=self.text_select_all, box="bottom", raise_if_not_found=False, time_out=2)
            or self.wait_ocr(match=self.text_bulk_fusion, box="top", raise_if_not_found=False, time_out=2)
        ):
            self._click_fallback_or_ocr("bulk_fusion_tab", ocr=self.text_bulk_fusion, box_hint="top", must=False)
        self.sleep(0.8)

        # Apply filter: Discarded
        self._apply_discarded_filter()

        # Loop until fusion count = 0
        self._loop_until_zero()

    # ---------- Helpers ----------
    def _apply_discarded_filter(self):
        # Click filter icon by coordinates first
        if not self._click_fallback_or_ocr("filter_icon", ocr=None, box_hint=None, must=False):
            # Try scanning nearby and ROI fallback
            if not self._scan_click_around_filter_icon():
                if not self._scan_click_in_roi(0.02, 0.86, 0.18, 0.96):
                    self.click_relative(0.12, 0.92, after_sleep=0.5)

        # Ensure panel opened (look for Discarded)
        if not self.wait_ocr(match=self.text_discarded, raise_if_not_found=False, settle_time=0.2, time_out=2):
            if not self._click_fallback_or_ocr("filter_icon", ocr=None, box_hint=None, must=False):
                self._scan_click_around_filter_icon()
            self.wait_ocr(match=self.text_discarded, raise_if_not_found=False, settle_time=0.2, time_out=2)

        # Check Discarded and Confirm/close
        self.wait_click_ocr(match=self.text_discarded, raise_if_not_found=True, settle_time=0.2)
        if not self.wait_click_ocr(match=self.text_confirm, raise_if_not_found=False, settle_time=0.2):
            self.click_relative(0.5, 0.5, after_sleep=0.3)
        self.sleep(0.5)

    def _loop_until_zero(self):
        first_time = True
        while True:
            # Always click Select All once
            self._click_fallback_or_ocr("select_all", ocr=self.text_select_all, box_hint="bottom", must=False)
            self.sleep(0.2)

            # Read remaining fusion count
            count = self._read_fusion_count()
            self.log_info(f"当前數據融合次數: {count}")
            if count is not None and count <= 0:
                self.log_info("數據融合次數=0，停止。")
                break

            # Execute Bulk Fusion
            self._click_fallback_or_ocr("bulk_fusion_exec", ocr=self.text_bulk_fusion, box_hint="bottom_right", must=True)

            if first_time:
                self._handle_first_time_dialog()
                first_time = False

            # Wait result and close
            self._wait_and_close_reward()
            self.sleep(0.4)

    def _read_fusion_count(self):
        box = self.box_of_screen(0.58, 0.80, 0.93, 0.90, name="fusion_count_area")
        texts = self.ocr(box=box, match=self.text_fusion_count)
        if not texts:
            texts = self.ocr(box=self.box_of_screen(0.50, 0.75, 0.98, 0.95), match=self.text_fusion_count)
        if texts:
            for t in texts:
                m = self.text_fusion_count.search(t.name)
                if m:
                    try:
                        for grp in reversed(m.groups() or ()):  # type: ignore[arg-type]
                            if grp and str(grp).isdigit():
                                return int(grp)
                    except Exception:
                        pass
        # Fallback: join all tokens and search
        try:
            all_tokens = self.ocr(box=box)
            joined = "".join([t.name for t in (all_tokens or [])])
            if not joined:
                all_tokens = self.ocr(box=self.box_of_screen(0.50, 0.75, 0.98, 0.95))
                joined = "".join([t.name for t in (all_tokens or [])])
            if joined:
                m = self.text_fusion_count.search(joined)
                if m:
                    for grp in reversed(m.groups() or ()):  # type: ignore[arg-type]
                        if grp and str(grp).isdigit():
                            return int(grp)
                loose_patterns = [
                    re.compile(r"(次|次數|次数)[^\d]{0,6}(\d+)", re.IGNORECASE),
                    re.compile(r"(Count|Attempts)[^\d]{0,6}(\d+)", re.IGNORECASE),
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
        # Try to check "Don't show again" and click confirm
        clicked = self.wait_click_ocr(match=self.text_dont_show, box=None, raise_if_not_found=False, settle_time=0.2, time_out=1.5)
        if not clicked:
            if self._click_fallback_or_ocr("first_time_checkbox", ocr=None, box_hint=None, must=False):
                self.log_debug("fallback clicked first_time_checkbox")
                clicked = True
        clicked_confirm = (
            self.wait_click_ocr(match=self.text_confirm, box="bottom_right", raise_if_not_found=False, settle_time=0.2, time_out=1.5)
            or self.wait_click_ocr(match=self.text_confirm, box="bottom", raise_if_not_found=False, settle_time=0.2, time_out=1.5)
            or self.wait_click_ocr(match=self.text_confirm, box=None, raise_if_not_found=False, settle_time=0.2, time_out=1.2)
        )
        if not clicked and not clicked_confirm:
            self.click_relative(0.5, 0.5, after_sleep=0.3)
            if not (
                self.wait_ocr(match=self.text_select_all, box="bottom", raise_if_not_found=False, time_out=1.0)
                or self.wait_ocr(match=self.text_bulk_fusion, box="bottom_right", raise_if_not_found=False, time_out=1.0)
            ):
                self._click_fallback_or_ocr("bulk_fusion_exec", ocr=self.text_bulk_fusion, box_hint="bottom_right", must=False)
                self.sleep(0.3)
                self.wait_ocr(match=self.text_select_all, box="bottom", raise_if_not_found=False, time_out=1.0)

    def _wait_and_close_reward(self):
        got = self.wait_ocr(match=self.text_got_echo, box="top", raise_if_not_found=False, settle_time=0.8, time_out=6)
        x, y = self.default_config["_fallback_coords"]["close_reward_blank"]
        self.click_relative(x, y, after_sleep=0.4)
        if not (
            self.wait_ocr(match=self.text_select_all, box="bottom", raise_if_not_found=False, time_out=1.2)
            or self.wait_ocr(match=self.text_bulk_fusion, box="bottom_right", raise_if_not_found=False, time_out=1.2)
        ):
            self._click_fallback_or_ocr("bulk_fusion_exec", ocr=self.text_bulk_fusion, box_hint="bottom_right", must=False)
            self.sleep(0.4)
            self.wait_ocr(match=self.text_select_all, box="bottom", raise_if_not_found=False, time_out=1.5)

    def _click_fallback_or_ocr(self, key, ocr=None, box_hint=None, must=False, ocr_time_out: float = 1.5):
        if ocr is not None:
            found = self.wait_click_ocr(match=ocr, box=box_hint if box_hint else None, raise_if_not_found=False, settle_time=0.3, time_out=ocr_time_out)
            if found:
                return True
            found = self.wait_click_ocr(match=ocr, box=None, raise_if_not_found=False, settle_time=0.3, time_out=ocr_time_out)
            if found:
                return True
        coords = self.default_config.get("_fallback_coords", {}).get(key)
        if coords and isinstance(coords, (tuple, list)) and len(coords) == 2:
            self.click_relative(coords[0], coords[1], after_sleep=0.5)
            return True
        if must:
            raise Exception(f"Failed to click {key} via OCR and fallback")
        return False

    def _ensure_select_all_checked(self):
        if self.wait_ocr(match=self.text_select_all_checked, box="bottom", raise_if_not_found=False, time_out=0.8):
            return True
        self._click_fallback_or_ocr("select_all", ocr=self.text_select_all, box_hint="bottom", must=False)
        if self.wait_ocr(match=self.text_select_all_checked, box="bottom", raise_if_not_found=False, time_out=1.2):
            return True
        return self.wait_ocr(match=self.text_select_all, box="bottom", raise_if_not_found=False, time_out=0.8)

    def _scan_click_around_filter_icon(self):
        base = self.default_config.get("_fallback_coords", {}).get("filter_icon", (0.12, 0.92))
        deltas = [
            (0.00, 0.00), (-0.02, 0.00), (0.02, 0.00), (0.00, -0.02), (0.00, 0.02),
            (-0.02, -0.02), (0.02, -0.02), (-0.02, 0.02), (0.02, 0.02),
            (-0.03, 0.00), (0.03, 0.00), (0.00, -0.03), (0.00, 0.03),
        ]
        for dx, dy in deltas:
            x = min(max(base[0] + dx, 0.0), 1.0)
            y = min(max(base[1] + dy, 0.0), 1.0)
            self.click_relative(x, y, after_sleep=0.3)
            if self.wait_ocr(match=self.text_discarded, raise_if_not_found=False, settle_time=0.2, time_out=1):
                self.log_debug(f"filter panel opened via scan at ({x:.2f}, {y:.2f})")
                return True
        self.log_debug("scan_click_around_filter_icon failed to open panel")
        return False

    def _scan_click_in_roi(self, x1, y1, x2, y2, steps_x: int = 6, steps_y: int = 4):
        try:
            sx = max(2, steps_x)
            sy = max(2, steps_y)
            for iy in range(sy):
                for ix in range(sx):
                    rx = x1 + (x2 - x1) * (ix + 0.5) / sx
                    ry = y1 + (y2 - y1) * (iy + 0.5) / sy
                    self.click_relative(rx, ry, after_sleep=0.25)
                    if self.wait_ocr(match=self.text_discarded, raise_if_not_found=False, settle_time=0.2, time_out=0.8):
                        self.log_debug(f"filter panel opened via ROI scan at ({rx:.2f}, {ry:.2f})")
                        return True
            return False
        except Exception as e:
            self.log_debug(f"_scan_click_in_roi error: {e}")
            return False

