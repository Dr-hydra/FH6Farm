import json
import os
import pickle
import time

import cv2
import numpy as np
import pyautogui
from PIL import ImageGrab


class VisionService:
    """Owns screenshots, template loading, scale handling, and basic image matches."""

    def __init__(
        self,
        app_dir,
        internal_dir,
        cache_dir,
        template_cache_file,
        template_meta_file,
        current_version,
        logger=None,
        regions_provider=None,
        running_checker=None,
        paused_checker=None,
        pause_handler=None,
        image_grabber=None,
        screenshot_provider=None,
        screen_size_provider=None,
    ):
        self.app_dir = app_dir
        self.internal_dir = internal_dir
        self.cache_dir = cache_dir
        self.template_cache_file = template_cache_file
        self.template_meta_file = template_meta_file
        self.current_version = current_version
        self.logger = logger or (lambda message: None)
        self.regions_provider = regions_provider or (lambda: {})
        self.running_checker = running_checker or (lambda: True)
        self.paused_checker = paused_checker or (lambda: False)
        self.pause_handler = pause_handler or (lambda: None)
        self.image_grabber = image_grabber or ImageGrab.grab
        self.screenshot_provider = screenshot_provider or pyautogui.screenshot
        self.screen_size_provider = screen_size_provider or pyautogui.size

        self.template_cache = {}
        self.template_gray_cache = {}
        self.template_transparent_cache = {}
        self.scaled_template_cache = {}
        self.file_template_cache = {}
        self.last_positions = {}

    def log(self, message):
        self.logger(message)

    def is_running(self):
        return self.running_checker()

    def _handle_pause_if_needed(self):
        if self.paused_checker():
            self.pause_handler()
            return True
        return False

    def _sleep_while_running(self, interval):
        sleep_end = time.time() + interval
        while self.is_running() and time.time() < sleep_end:
            time.sleep(0.05)

    def get_image_path(self, filename):
        basename = os.path.basename(filename)

        ext_path = os.path.join(self.app_dir, "images", basename)
        if os.path.exists(ext_path):
            return ext_path

        int_path = os.path.join(self.internal_dir, "images", basename)
        if os.path.exists(int_path):
            return int_path

        return filename

    def load_template(self, template_path):
        actual_path = self.get_image_path(template_path)
        cache_key = actual_path

        if cache_key in self.template_cache:
            return self.template_cache[cache_key], actual_path

        template = cv2.imread(actual_path, cv2.IMREAD_COLOR)
        if template is not None:
            self.template_cache[cache_key] = template
        return template, actual_path

    def load_template_gray(self, template_path):
        actual_path = self.get_image_path(template_path)
        cache_key = ("gray", actual_path)
        if cache_key in self.template_gray_cache:
            return self.template_gray_cache[cache_key]

        template = cv2.imread(actual_path, cv2.IMREAD_GRAYSCALE)
        if template is not None:
            self.template_gray_cache[cache_key] = template
        return template

    def load_template_transparent(self, template_path):
        actual_path = self.get_image_path(template_path)
        cache_key = ("transparent", actual_path)
        if cache_key in self.template_transparent_cache:
            return self.template_transparent_cache[cache_key]

        template = cv2.imread(actual_path, cv2.IMREAD_UNCHANGED)
        if template is not None:
            self.template_transparent_cache[cache_key] = template
        return template

    def get_images_root_dir(self):
        ext_dir = os.path.join(self.app_dir, "images")
        if os.path.isdir(ext_dir):
            return ext_dir

        int_dir = os.path.join(self.internal_dir, "images")
        if os.path.isdir(int_dir):
            return int_dir

        return None

    def get_template_meta(self):
        images_dir = self.get_images_root_dir()
        meta_data = {"__APP_VERSION__": self.current_version}
        if not images_dir:
            return meta_data

        for root, _, files in os.walk(images_dir):
            for file in files:
                if not file.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
                    continue

                path = os.path.join(root, file)
                rel_path = os.path.relpath(path, images_dir).replace("\\", "/")

                try:
                    stat = os.stat(path)
                    meta_data[rel_path] = {
                        "mtime": stat.st_mtime,
                        "size": stat.st_size,
                    }
                except Exception:
                    pass

        return meta_data

    def is_template_cache_valid(self):
        if not os.path.exists(self.template_cache_file) or not os.path.exists(self.template_meta_file):
            return False

        try:
            with open(self.template_meta_file, "r", encoding="utf-8") as f:
                old_meta = json.load(f)
        except Exception:
            return False

        new_meta = self.get_template_meta()
        return old_meta == new_meta

    def build_template_file_cache(self):
        self.log("开始构建模板缓存文件...")
        os.makedirs(self.cache_dir, exist_ok=True)

        images_dir = self.get_images_root_dir()
        if not images_dir:
            self.log("未找到 images 目录，无法构建模板缓存。")
            return False

        cache_data = {}
        meta_data = self.get_template_meta()
        scales = self.get_scales_to_try(fast_mode=False)

        for rel_path in meta_data.keys():
            if rel_path == "__APP_VERSION__":
                continue
            img_path = os.path.join(images_dir, rel_path)
            template = cv2.imread(img_path, cv2.IMREAD_COLOR)
            if template is None:
                continue

            cache_data[rel_path] = {}
            for scale in scales:
                try:
                    if scale == 1.0:
                        scaled = template.copy()
                    else:
                        scaled = cv2.resize(template, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

                    cache_data[rel_path][str(round(scale, 3))] = scaled
                except Exception:
                    continue

        try:
            with open(self.template_cache_file, "wb") as f:
                pickle.dump(cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)

            with open(self.template_meta_file, "w", encoding="utf-8") as f:
                json.dump(meta_data, f, ensure_ascii=False, indent=2)

            self.log("模板缓存文件构建完成。")
            return True
        except Exception as e:
            self.log(f"写入模板缓存失败: {e}")
            return False

    def load_template_file_cache(self):
        try:
            with open(self.template_cache_file, "rb") as f:
                self.file_template_cache = pickle.load(f)
            self.log("模板缓存文件加载成功。")
            return True
        except Exception as e:
            self.log(f"加载模板缓存失败: {e}")
            self.file_template_cache = {}
            return False

    def prepare_template_cache(self):
        os.makedirs(self.cache_dir, exist_ok=True)

        if self.is_template_cache_valid():
            if self.load_template_file_cache():
                return

        self.log("检测到软件版本更新或本地图片已修改，开始强制重建图像缓存(需几秒钟)...")
        try:
            if os.path.exists(self.template_cache_file):
                os.remove(self.template_cache_file)
            if os.path.exists(self.template_meta_file):
                os.remove(self.template_meta_file)
        except Exception as e:
            self.log(f"清理旧缓存文件失败: {e}")

        if self.build_template_file_cache():
            self.template_cache.clear()
            self.scaled_template_cache.clear()
            self.load_template_file_cache()

    def capture_region(self, region=None, mask_areas=None):
        try:
            if region:
                x, y, w, h = region
                bbox = (int(x), int(y), int(x + w), int(y + h))
                screen = self.image_grabber(bbox=bbox, all_screens=True)
            else:
                screen = self.image_grabber(all_screens=True)
        except Exception:
            screen = self.screenshot_provider(region=region)

        screen_bgr = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)

        if mask_areas:
            for rect in mask_areas:
                try:
                    mx1, my1, mx2, my2 = rect
                    mx1 = max(0, int(mx1))
                    my1 = max(0, int(my1))
                    mx2 = min(screen_bgr.shape[1], int(mx2))
                    my2 = min(screen_bgr.shape[0], int(my2))
                    if mx2 > mx1 and my2 > my1:
                        screen_bgr[my1:my2, mx1:mx2] = 0
                except Exception:
                    pass

        return screen_bgr

    def get_scales_to_try(self, fast_mode=True):
        regions = self.regions_provider() or {}
        full_region = regions.get("全界面")
        curr_w = full_region[2] if full_region else self.screen_size_provider()[0]
        primary_base = 2560
        primary_scale = curr_w / primary_base
        scales = []

        def add_scale(scale):
            scale = round(float(scale), 3)
            if 0.45 <= scale <= 1.8 and scale not in scales:
                scales.append(scale)

        add_scale(primary_scale)
        add_scale(primary_scale * 0.98)
        add_scale(primary_scale * 1.02)
        add_scale(primary_scale * 0.95)
        add_scale(primary_scale * 1.05)
        add_scale(primary_scale * 0.92)
        add_scale(primary_scale * 1.08)

        for base_width in [1920, 1600]:
            scale = curr_w / base_width
            add_scale(scale)
            add_scale(scale * 0.98)
            add_scale(scale * 1.02)

        for scale in [1.0, 0.95, 1.05, 0.9, 1.1, 0.85, 1.15, 0.8, 0.75, 0.7]:
            add_scale(scale)

        if fast_mode:
            return scales[:8]
        return scales

    def get_scaled_template(self, template_path, scale):
        actual_path = self.get_image_path(template_path)
        images_dir = self.get_images_root_dir()

        if images_dir and os.path.exists(actual_path):
            try:
                rel_key = os.path.relpath(actual_path, images_dir).replace("\\", "/")
            except Exception:
                rel_key = os.path.basename(actual_path)
        else:
            rel_key = os.path.basename(actual_path)

        mem_key = (actual_path, round(scale, 3))
        if mem_key in self.scaled_template_cache:
            return self.scaled_template_cache[mem_key], actual_path

        scale_key = str(round(scale, 3))
        if rel_key in self.file_template_cache:
            template = self.file_template_cache[rel_key].get(scale_key)
            if template is not None:
                self.scaled_template_cache[mem_key] = template
                return template, actual_path

        template_orig, actual_path = self.load_template(template_path)
        if template_orig is None:
            return None, actual_path

        try:
            if scale == 1.0:
                template = template_orig.copy()
            else:
                template = cv2.resize(template_orig, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

            self.scaled_template_cache[mem_key] = template
            return template, actual_path
        except Exception:
            return None, actual_path

    def find_image_in_screen(self, screen_bgr, template_path, region=None, threshold=0.75, fast_mode=True):
        try:
            scales_to_try = self.get_scales_to_try(fast_mode=fast_mode)

            for scale in scales_to_try:
                template, _ = self.get_scaled_template(template_path, scale)
                if template is None:
                    continue

                h, w = template.shape[:2]
                if h < 5 or w < 5:
                    continue
                if h > screen_bgr.shape[0] or w > screen_bgr.shape[1]:
                    continue

                result = cv2.matchTemplate(screen_bgr, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)

                if max_val >= threshold:
                    pos = (
                        max_loc[0] + w // 2 + (region[0] if region else 0),
                        max_loc[1] + h // 2 + (region[1] if region else 0),
                    )
                    self.last_positions[template_path] = pos
                    self.log(f"[ImageMatch] 命中: {template_path} | 得分: {max_val:.3f} (阈值 {threshold}) | 缩放比: {scale:.3f}")
                    return pos

            return None
        except Exception as e:
            self.log(f"find_image_in_screen 异常: {e}")
            return None

    def find_image(self, template_path, region=None, threshold=0.75, fast_mode=True):
        if not self.is_running():
            return None

        try:
            screen_bgr = self.capture_region(region)
            return self.find_image_in_screen(
                screen_bgr,
                template_path,
                region=region,
                threshold=threshold,
                fast_mode=fast_mode,
            )
        except Exception as e:
            self.log(f"查找图片时发生异常: {e}")
            return None

    def find_any_image(self, image_list, region=None, threshold=0.8, fast_mode=True):
        if not self.is_running():
            return None

        try:
            screen_bgr = self.capture_region(region)
            for image_path in image_list:
                pos = self.find_image_in_screen(
                    screen_bgr,
                    image_path,
                    region=region,
                    threshold=threshold,
                    fast_mode=fast_mode,
                )
                if pos:
                    return pos
            return None
        except Exception as e:
            self.log(f"find_any_image 异常: {e}")
            return None

    def find_image_transparent(self, template_path, region=None, threshold=0.70, fast_mode=True):
        if not self.is_running():
            return None

        try:
            screen_bgr = self.capture_region(region)
            template_bgra = self.load_template_transparent(template_path)

            if template_bgra is None:
                return None
            if template_bgra.shape[2] != 4:
                return self.find_image_in_screen(screen_bgr, template_path, region, threshold, fast_mode)

            scales_to_try = self.get_scales_to_try(fast_mode=fast_mode)
            for scale in scales_to_try:
                if scale == 1.0:
                    template_scaled = template_bgra.copy()
                else:
                    template_scaled = cv2.resize(template_bgra, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

                h, w = template_scaled.shape[:2]
                if h < 5 or w < 5 or h > screen_bgr.shape[0] or w > screen_bgr.shape[1]:
                    continue

                template_bgr = template_scaled[:, :, :3]
                alpha_mask = template_scaled[:, :, 3]
                result = cv2.matchTemplate(screen_bgr, template_bgr, cv2.TM_CCOEFF_NORMED, mask=alpha_mask)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                if max_val >= threshold:
                    self.log(f"[AlphaMatch] 命中(无视背景): {template_path} | 得分: {max_val:.3f} (阈值 {threshold}) | 缩放比: {scale:.3f}")
                    return (
                        max_loc[0] + w // 2 + (region[0] if region else 0),
                        max_loc[1] + h // 2 + (region[1] if region else 0),
                    )
            return None
        except Exception as e:
            self.log(f"find_image_transparent 异常: {e}")
            return None

    def find_any_image_transparent(self, image_list, region=None, threshold=0.70, fast_mode=True):
        if not self.is_running():
            return None

        try:
            screen_bgr = self.capture_region(region)
            scales_to_try = self.get_scales_to_try(fast_mode=fast_mode)

            for template_path in image_list:
                template_bgra = self.load_template_transparent(template_path)
                if template_bgra is None:
                    continue

                if template_bgra.shape[2] != 4:
                    pos = self.find_image_in_screen(screen_bgr, template_path, region, threshold, fast_mode)
                    if pos:
                        return pos
                    continue

                for scale in scales_to_try:
                    if scale == 1.0:
                        template_scaled = template_bgra.copy()
                    else:
                        template_scaled = cv2.resize(template_bgra, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

                    h, w = template_scaled.shape[:2]
                    if h < 5 or w < 5 or h > screen_bgr.shape[0] or w > screen_bgr.shape[1]:
                        continue

                    template_bgr = template_scaled[:, :, :3]
                    alpha_mask = template_scaled[:, :, 3]
                    result = cv2.matchTemplate(screen_bgr, template_bgr, cv2.TM_CCOEFF_NORMED, mask=alpha_mask)
                    _, max_val, _, max_loc = cv2.minMaxLoc(result)

                    if max_val >= threshold:
                        self.log(f"[AlphaMatchAny] 命中(无视背景): {template_path} | 得分: {max_val:.3f} (阈值 {threshold}) | 缩放比: {scale:.3f}")
                        return (
                            max_loc[0] + w // 2 + (region[0] if region else 0),
                            max_loc[1] + h // 2 + (region[1] if region else 0),
                        )
            return None
        except Exception as e:
            self.log(f"find_any_image_transparent 异常: {e}")
            return None

    def find_image_gray(self, template_path, region=None, threshold=0.75, fast_mode=True, invert_mode=False):
        if not self.is_running():
            return None

        try:
            screen_bgr = self.capture_region(region)
            screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)
            scales_to_try = self.get_scales_to_try(fast_mode=fast_mode)

            template_gray_raw = self.load_template_gray(template_path)
            if template_gray_raw is None:
                return None

            return self._find_gray_template_in_screen(
                screen_gray,
                template_gray_raw,
                template_path,
                region=region,
                threshold=threshold,
                scales_to_try=scales_to_try,
                invert_mode=invert_mode,
                log_prefix="[GrayMatch]",
            )
        except Exception as e:
            self.log(f"find_image_gray 异常: {e}")
            return None

    def find_any_image_gray(self, image_list, region=None, threshold=0.75, fast_mode=True, invert_mode=False):
        if not self.is_running():
            return None

        try:
            screen_bgr = self.capture_region(region)
            screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)
            scales_to_try = self.get_scales_to_try(fast_mode=fast_mode)

            for image_path in image_list:
                template_gray_raw = self.load_template_gray(image_path)
                if template_gray_raw is None:
                    continue

                pos = self._find_gray_template_in_screen(
                    screen_gray,
                    template_gray_raw,
                    image_path,
                    region=region,
                    threshold=threshold,
                    scales_to_try=scales_to_try,
                    invert_mode=invert_mode,
                    log_prefix="[GrayMatchAny]",
                )
                if pos:
                    return pos

            return None
        except Exception as e:
            self.log(f"find_any_image_gray 异常: {e}")
            return None

    def _find_gray_template_in_screen(
        self,
        screen_gray,
        template_gray_raw,
        template_path,
        region=None,
        threshold=0.75,
        scales_to_try=None,
        invert_mode=False,
        log_prefix="[GrayMatch]",
    ):
        scales_to_try = scales_to_try or self.get_scales_to_try(fast_mode=True)

        for scale in scales_to_try:
            template_gray = template_gray_raw
            if scale != 1.0:
                template_gray = cv2.resize(template_gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

            h, w = template_gray.shape[:2]
            if h < 5 or w < 5 or h > screen_gray.shape[0] or w > screen_gray.shape[1]:
                continue

            result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            if max_val >= threshold:
                self.log(f"{log_prefix} 命中: {template_path} | 模式: 原图 | 灰度得分: {max_val:.3f} (阈值 {threshold}) | 缩放比: {scale:.3f}")
                return (
                    max_loc[0] + w // 2 + (region[0] if region else 0),
                    max_loc[1] + h // 2 + (region[1] if region else 0),
                )

            if invert_mode:
                template_inv = 255 - template_gray
                result_inv = cv2.matchTemplate(screen_gray, template_inv, cv2.TM_CCOEFF_NORMED)
                _, max_val_inv, _, max_loc_inv = cv2.minMaxLoc(result_inv)
                if max_val_inv >= threshold:
                    self.log(f"{log_prefix} 命中: {template_path} | 模式: 反相 | 灰度得分: {max_val_inv:.3f} (阈值 {threshold}) | 缩放比: {scale:.3f}")
                    return (
                        max_loc_inv[0] + w // 2 + (region[0] if region else 0),
                        max_loc_inv[1] + h // 2 + (region[1] if region else 0),
                    )

        return None

    def wait_for_image_transparent(self, template_path, region=None, threshold=0.70, timeout=30, interval=0.4, fast_mode=True):
        start = time.time()
        while self.is_running() and time.time() - start < timeout:
            pos = self.find_image_transparent(template_path, region, threshold, fast_mode)
            if pos:
                return pos
            self._sleep_while_running(interval)
        return None

    def wait_for_any_image_transparent(self, image_list, region=None, threshold=0.70, timeout=30, interval=0.4, fast_mode=True):
        return self._wait_for_match(
            lambda: self.find_any_image_transparent(image_list, region, threshold, fast_mode),
            timeout=timeout,
            interval=interval,
        )

    def wait_for_any_image_gray(self, image_list, region=None, threshold=0.75, timeout=30, interval=0.3, fast_mode=True, invert_mode=False):
        return self._wait_for_match(
            lambda: self.find_any_image_gray(
                image_list,
                region=region,
                threshold=threshold,
                fast_mode=fast_mode,
                invert_mode=invert_mode,
            ),
            timeout=timeout,
            interval=interval,
        )

    def wait_for_image_gray(self, template_path, region=None, threshold=0.75, timeout=30, interval=0.3, fast_mode=True, invert_mode=False):
        return self._wait_for_match(
            lambda: self.find_image_gray(
                template_path,
                region=region,
                threshold=threshold,
                fast_mode=fast_mode,
                invert_mode=invert_mode,
            ),
            timeout=timeout,
            interval=interval,
        )

    def wait_for_any_image(self, image_list, region=None, threshold=0.75, timeout=30, interval=0.4, fast_mode=True, log_text=None):
        def match_once():
            try:
                screen_bgr = self.capture_region(region)
                for image_path in image_list:
                    pos = self.find_image_in_screen(
                        screen_bgr,
                        image_path,
                        region=region,
                        threshold=threshold,
                        fast_mode=fast_mode,
                    )
                    if pos:
                        return pos
            except Exception as e:
                self.log(f"wait_for_any_image 异常: {e}")
            return None

        return self._wait_for_match(match_once, timeout=timeout, interval=interval, log_text=log_text)

    def wait_for_image(self, template_path, region=None, threshold=0.75, timeout=30, interval=0.4, fast_mode=True, log_text=None):
        return self.wait_for_any_image(
            [template_path],
            region=region,
            threshold=threshold,
            timeout=timeout,
            interval=interval,
            fast_mode=fast_mode,
            log_text=log_text,
        )

    def find_image_with_element(self, main_path, sub_path, region=None, threshold=0.85, fast_mode=True):
        if not self.is_running():
            return None

        try:
            screen_bgr = self.capture_region(region)
            scales_to_try = self.get_scales_to_try(fast_mode=fast_mode)
            for scale in scales_to_try:
                main_template, _ = self.get_scaled_template(main_path, scale)
                sub_template, _ = self.get_scaled_template(sub_path, scale)
                if main_template is None or sub_template is None:
                    continue

                h_m, w_m = main_template.shape[:2]
                if h_m < 5 or w_m < 5 or h_m > screen_bgr.shape[0] or w_m > screen_bgr.shape[1]:
                    continue

                result_main = cv2.matchTemplate(screen_bgr, main_template, cv2.TM_CCOEFF_NORMED)
                loc = np.where(result_main >= threshold)
                checked = set()
                for x, y in zip(*loc[::-1]):
                    key = (x // 10, y // 10)
                    if key in checked:
                        continue
                    checked.add(key)

                    sub_roi = screen_bgr[
                        max(0, y - 5):min(screen_bgr.shape[0], y + h_m + 5),
                        max(0, x - 5):min(screen_bgr.shape[1], x + w_m + 5),
                    ]
                    if sub_template.shape[0] > sub_roi.shape[0] or sub_template.shape[1] > sub_roi.shape[1]:
                        continue

                    result_sub = cv2.matchTemplate(sub_roi, sub_template, cv2.TM_CCOEFF_NORMED)
                    sub_score = cv2.minMaxLoc(result_sub)[1]
                    if sub_score >= threshold:
                        main_score = result_main[y, x]
                        self.log(f"[ComboMatch] 命中: {main_path}+{sub_path} | 主图得分: {main_score:.3f} | 元素得分: {sub_score:.3f} (阈值 {threshold}) | 缩放比: {scale:.3f}")
                        return (
                            x + w_m // 2 + (region[0] if region else 0),
                            y + h_m // 2 + (region[1] if region else 0),
                        )
            return None
        except Exception as e:
            self.log(f"find_image_with_element 异常: {e}")
            return None

    def find_image_with_element_stable(
        self,
        main_path,
        sub_path,
        region=None,
        main_threshold=0.60,
        verify_threshold=0.72,
        sub_threshold=0.70,
        max_candidates=15,
    ):
        if not self.is_running():
            return None

        try:
            screen_gray = self.to_gray_image(self.capture_region(region))
            main_template = self.load_template_gray(main_path)
            sub_template = self.load_template_gray(sub_path)

            if main_template is None or sub_template is None:
                return None

            h_m, w_m = main_template.shape[:2]
            h_s, w_s = sub_template.shape[:2]

            if h_m > screen_gray.shape[0] or w_m > screen_gray.shape[1]:
                return None

            result_main = cv2.matchTemplate(screen_gray, main_template, cv2.TM_CCOEFF_NORMED)
            ys, xs = np.where(result_main >= main_threshold)

            if len(xs) == 0:
                return None

            candidates = [(float(result_main[y, x]), x, y) for x, y in zip(xs, ys)]
            candidates.sort(key=lambda t: t[0], reverse=True)

            checked = set()
            checked_count = 0

            for main_score, x, y in candidates:
                key = (x // 8, y // 8)
                if key in checked:
                    continue
                checked.add(key)

                checked_count += 1
                if checked_count > max_candidates:
                    break

                pad = 8
                x1 = max(0, x - pad)
                y1 = max(0, y - pad)
                x2 = min(screen_gray.shape[1], x + w_m + pad)
                y2 = min(screen_gray.shape[0], y + h_m + pad)

                sub_roi = screen_gray[y1:y2, x1:x2]
                if sub_roi.shape[0] < h_s or sub_roi.shape[1] < w_s:
                    continue

                result_sub = cv2.matchTemplate(sub_roi, sub_template, cv2.TM_CCOEFF_NORMED)
                sub_score = cv2.minMaxLoc(result_sub)[1]

                if main_score >= verify_threshold and sub_score >= sub_threshold:
                    cx = x + w_m // 2
                    cy = y + h_m // 2
                    if region:
                        cx += region[0]
                        cy += region[1]
                    self.log(f"[StableMatch] 命中: {main_path}+{sub_path} | 主图: {main_score:.3f} (需>{verify_threshold}) | 元素: {sub_score:.3f} (需>{sub_threshold})")
                    return (cx, cy)

            return None
        except Exception as e:
            self.log(f"find_image_with_element_stable 识别报错: {e}")
            return None

    def find_image_with_element_multi(
        self,
        main_path,
        sub_path,
        region=None,
        fast_mode=True,
        main_threshold=0.60,
        like_threshold=0.75,
        final_threshold=0.72,
        mask_areas=None,
        ignore_top_text=False,
    ):
        if not self.is_running():
            return None

        try:
            screen_bgr = self.capture_region(region, mask_areas=mask_areas)
            screen_gray = self.to_gray_image(screen_bgr)
            screen_hsv = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2HSV)
            scales_to_try = self.get_scales_to_try(fast_mode=fast_mode)

            for scale in scales_to_try:
                main_template, _ = self.get_scaled_template(main_path, scale)
                sub_template, _ = self.get_scaled_template(sub_path, scale)
                if main_template is None or sub_template is None:
                    continue

                h_m, w_m = main_template.shape[:2]
                if h_m < 5 or w_m < 5:
                    continue
                if h_m > screen_bgr.shape[0] or w_m > screen_bgr.shape[1]:
                    continue

                top_h = int(h_m * 0.20)
                mid_h = int(h_m * 0.60)
                bot_h = h_m - top_h - mid_h
                if top_h <= 0 or mid_h <= 0 or bot_h <= 0:
                    continue

                template_top_gray = self.to_gray_image(main_template[0:top_h, :])
                template_mid_bgr = main_template[top_h:top_h + mid_h, :]
                template_mid_gray = self.to_gray_image(template_mid_bgr)
                template_bot_bgr = main_template[top_h + mid_h:, :]
                template_bot_hsv = cv2.cvtColor(template_bot_bgr, cv2.COLOR_BGR2HSV)
                bot_roi_template = template_bot_hsv[:, :int(w_m * 0.6)]
                template_bot_avg_color = cv2.mean(bot_roi_template)[:3]

                result_main = cv2.matchTemplate(screen_bgr, main_template, cv2.TM_CCOEFF_NORMED)
                flat = result_main.ravel()
                if flat.size == 0:
                    continue
                top_k = min(30, flat.size)
                idxs = np.argpartition(flat, -top_k)[-top_k:]
                points = []
                for idx in idxs:
                    y, x = np.unravel_index(idx, result_main.shape)
                    score = result_main[y, x]
                    if score < max(0.55, main_threshold - 0.12):
                        continue
                    points.append((x, y, score))
                points.sort(key=lambda p: (p[0] // 50, p[1]))

                checked_points = set()

                for x, y, base_score in points:
                    key = (x // 10, y // 10)
                    if key in checked_points:
                        continue
                    checked_points.add(key)

                    bot_y1, bot_y2 = y + top_h + mid_h, y + h_m
                    bot_x1, bot_x2 = x, x + int(w_m * 0.6)
                    if bot_y2 <= screen_hsv.shape[0] and bot_x2 <= screen_hsv.shape[1]:
                        screen_bot_hsv = screen_hsv[bot_y1:bot_y2, bot_x1:bot_x2]
                        if screen_bot_hsv.size > 0:
                            screen_bot_avg_color = cv2.mean(screen_bot_hsv)[:3]
                            color_dist = abs(screen_bot_avg_color[0] - template_bot_avg_color[0])
                            if color_dist > 40:
                                continue
                        else:
                            continue
                    else:
                        continue

                    roi_bgr = screen_bgr[y:y + h_m, x:x + w_m]
                    if roi_bgr.shape[:2] != main_template.shape[:2]:
                        continue

                    pad = 5
                    sub_roi = screen_bgr[
                        max(0, y - pad):min(screen_bgr.shape[0], y + h_m + pad),
                        max(0, x - pad):min(screen_bgr.shape[1], x + w_m + pad),
                    ]
                    like_score = self.match_template_score(sub_roi, sub_template)
                    if like_score < like_threshold:
                        continue

                    mid_roi_bgr = roi_bgr[top_h:top_h + mid_h, :]
                    mid_color_score = self.match_template_score(mid_roi_bgr, template_mid_bgr)
                    mid_roi_gray = screen_gray[y + top_h:y + top_h + mid_h, x:x + w_m]
                    mid_gray_score = self.match_template_score(mid_roi_gray, template_mid_gray)
                    mid_score = mid_color_score * 0.6 + mid_gray_score * 0.4
                    if mid_score < 0.65:
                        continue

                    top_roi_gray = screen_gray[y:y + top_h, x:x + w_m]
                    top_score = self.match_template_score(top_roi_gray, template_top_gray)
                    if top_score < 0.50 and not ignore_top_text:
                        continue

                    bot_roi_bgr = roi_bgr[top_h + mid_h:, :]
                    bot_score = self.match_template_score(bot_roi_bgr, template_bot_bgr)
                    if bot_score < 0.55:
                        continue

                    final_score = (
                        mid_score * 0.40 +
                        bot_score * 0.25 +
                        base_score * 0.20 +
                        top_score * 0.15
                    )

                    current_pos = (
                        x + w_m // 2 + (region[0] if region else 0),
                        y + h_m // 2 + (region[1] if region else 0),
                    )

                    if final_score >= final_threshold:
                        self.log(
                            f"[MultiMatch-Pro] 锁定: {main_path} | "
                            f"综合: {final_score:.3f} | 车身: {mid_score:.3f} | "
                            f"底部: {bot_score:.3f} | 颜色距: {color_dist:.1f}"
                        )
                        return current_pos

            return None
        except Exception as e:
            self.log(f"find_image_with_element_multi 异常: {e}")
            return None

    def find_image_with_element_fast(self, main_path, sub_path, region=None, threshold=0.70, sub_threshold=0.70):
        if not self.is_running():
            return None

        try:
            screen_gray = self.to_gray_image(self.capture_region(region))
            main_template = self.load_template_gray(main_path)
            sub_template = self.load_template_gray(sub_path)

            if main_template is None or sub_template is None:
                return None

            h_m, w_m = main_template.shape[:2]
            h_s, w_s = sub_template.shape[:2]

            if h_m > screen_gray.shape[0] or w_m > screen_gray.shape[1]:
                return None

            result_main = cv2.matchTemplate(screen_gray, main_template, cv2.TM_CCOEFF_NORMED)
            loc = np.where(result_main >= threshold)
            checked = set()

            for x, y in zip(*loc[::-1]):
                key = (x // 10, y // 10)
                if key in checked:
                    continue
                checked.add(key)

                x1 = max(0, x - 5)
                y1 = max(0, y - 5)
                x2 = min(screen_gray.shape[1], x + w_m + 5)
                y2 = min(screen_gray.shape[0], y + h_m + 5)
                sub_roi = screen_gray[y1:y2, x1:x2]

                if sub_roi.shape[0] < h_s or sub_roi.shape[1] < w_s:
                    continue

                result_sub = cv2.matchTemplate(sub_roi, sub_template, cv2.TM_CCOEFF_NORMED)
                max_val_sub = cv2.minMaxLoc(result_sub)[1]
                if max_val_sub >= sub_threshold:
                    cx = x + w_m // 2
                    cy = y + h_m // 2
                    if region:
                        cx += region[0]
                        cy += region[1]
                    main_score = result_main[y, x]
                    self.log(f"[FastMatch] 命中: {main_path}+{sub_path} | 主图: {main_score:.3f} (需>{threshold}) | 元素: {max_val_sub:.3f} (需>{sub_threshold})")
                    return (cx, cy)

            return None
        except Exception as e:
            self.log(f"find_image_with_element_fast 异常: {e}")
            return None

    def wait_for_image_with_element_multi(
        self,
        main_path,
        sub_path,
        region=None,
        fast_mode=True,
        main_threshold=0.60,
        like_threshold=0.75,
        final_threshold=0.72,
        timeout=30,
        interval=0.4,
        ignore_top_text=False,
    ):
        return self._wait_for_match(
            lambda: self.find_image_with_element_multi(
                main_path=main_path,
                sub_path=sub_path,
                region=region,
                fast_mode=fast_mode,
                main_threshold=main_threshold,
                like_threshold=like_threshold,
                final_threshold=final_threshold,
                ignore_top_text=ignore_top_text,
            ),
            timeout=timeout,
            interval=interval,
        )

    def wait_for_image_with_element_stable(
        self,
        main_path,
        sub_path,
        region=None,
        main_threshold=0.60,
        verify_threshold=0.72,
        sub_threshold=0.70,
        max_candidates=15,
        timeout=3,
        interval=0.2,
    ):
        return self._wait_for_match(
            lambda: self.find_image_with_element_stable(
                main_path=main_path,
                sub_path=sub_path,
                region=region,
                main_threshold=main_threshold,
                verify_threshold=verify_threshold,
                sub_threshold=sub_threshold,
                max_candidates=max_candidates,
            ),
            timeout=timeout,
            interval=interval,
        )

    def wait_for_image_with_element_fast(
        self,
        main_path,
        sub_path,
        region=None,
        threshold=0.70,
        sub_threshold=0.70,
        timeout=4,
        interval=0.25,
    ):
        return self._wait_for_match(
            lambda: self.find_image_with_element_fast(
                main_path=main_path,
                sub_path=sub_path,
                region=region,
                threshold=threshold,
                sub_threshold=sub_threshold,
            ),
            timeout=timeout,
            interval=interval,
        )

    def wait_for_image_with_element(self, main_path, sub_path, region=None, threshold=0.85, timeout=30, interval=0.4, fast_mode=True):
        return self._wait_for_match(
            lambda: self.find_image_with_element(
                main_path,
                sub_path,
                region=region,
                threshold=threshold,
                fast_mode=fast_mode,
            ),
            timeout=timeout,
            interval=interval,
        )

    def find_image_ultimate_safe(self, main_path, anti_path, region=None, main_threshold=0.80, anti_threshold=0.65, mask_areas=None):
        if not self.is_running():
            return None

        try:
            screen_bgr = self.capture_region(region, mask_areas=mask_areas)
            screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)
            scales_to_try = self.get_scales_to_try(fast_mode=True)

            for scale in scales_to_try:
                main_template_bgr, _ = self.get_scaled_template(main_path, scale)
                anti_template_bgr = None
                if anti_path:
                    anti_template_bgr, _ = self.get_scaled_template(anti_path, scale)
                if main_template_bgr is None:
                    continue
                if anti_path and anti_template_bgr is None:
                    continue

                main_template_gray = cv2.cvtColor(main_template_bgr, cv2.COLOR_BGR2GRAY)
                h_m, w_m = main_template_bgr.shape[:2]

                if h_m < 10 or w_m < 10 or h_m > screen_bgr.shape[0] or w_m > screen_bgr.shape[1]:
                    continue

                result_main = cv2.matchTemplate(screen_bgr, main_template_bgr, cv2.TM_CCOEFF_NORMED)
                loc = np.where(result_main >= main_threshold)
                points = list(zip(*loc[::-1]))
                points.sort(key=lambda p: (p[1] // 50, p[0]))

                checked = set()
                for x, y in points:
                    key = (x // 10, y // 10)
                    if key in checked:
                        continue
                    checked.add(key)

                    base_score = result_main[y, x]
                    roi_bgr = screen_bgr[y:y + h_m, x:x + w_m]
                    roi_gray = screen_gray[y:y + h_m, x:x + w_m]
                    if roi_bgr.shape[:2] != main_template_bgr.shape[:2]:
                        continue

                    if anti_path and anti_template_bgr is not None:
                        h_a, w_a = anti_template_bgr.shape[:2]
                        pad_anti = 10
                        roi_y1 = max(0, y - pad_anti)
                        roi_y2 = min(screen_bgr.shape[0], y + h_m + pad_anti)
                        roi_x1 = max(0, x - pad_anti)
                        roi_x2 = min(screen_bgr.shape[1], x + w_m + pad_anti)
                        anti_roi = screen_bgr[roi_y1:roi_y2, roi_x1:roi_x2]
                        if anti_roi.shape[0] >= h_a and anti_roi.shape[1] >= w_a:
                            result_anti = cv2.matchTemplate(anti_roi, anti_template_bgr, cv2.TM_CCOEFF_NORMED)
                            anti_score = cv2.minMaxLoc(result_anti)[1]
                            if anti_score >= anti_threshold:
                                self.log(f"[排他拦截]: 发现排除图 ({anti_score:.2f})，放弃该目标。")
                                continue

                    top_h = int(h_m * 0.25)
                    template_top = main_template_gray[:top_h, :]
                    score_top = 0.0
                    pad_slide = 5
                    if top_h > pad_slide * 2 and w_m > pad_slide * 2:
                        template_top_core = template_top[pad_slide:-pad_slide, pad_slide:-pad_slide]
                        search_top = roi_gray[:int(h_m * 0.35), :]
                        if search_top.shape[0] >= template_top_core.shape[0] and search_top.shape[1] >= template_top_core.shape[1]:
                            result_top = cv2.matchTemplate(search_top, template_top_core, cv2.TM_CCOEFF_NORMED)
                            score_top = cv2.minMaxLoc(result_top)[1]

                    bottom_h = int(h_m * 0.25)
                    right_w = int(w_m * 0.35)
                    template_pi_box = main_template_bgr[h_m - bottom_h:, w_m - right_w:]
                    score_bot = 0.0
                    if bottom_h > pad_slide * 2 and right_w > pad_slide * 2:
                        template_pi_core = template_pi_box[pad_slide:-pad_slide, pad_slide:-pad_slide]
                        search_y1 = h_m - int(h_m * 0.35)
                        search_x1 = w_m - int(w_m * 0.45)
                        search_bot = roi_bgr[search_y1:, search_x1:]
                        if search_bot.shape[0] >= template_pi_core.shape[0] and search_bot.shape[1] >= template_pi_core.shape[1]:
                            result_bot = cv2.matchTemplate(search_bot, template_pi_core, cv2.TM_CCOEFF_NORMED)
                            score_bot = cv2.minMaxLoc(result_bot)[1]

                    if base_score >= 0.76 and score_top >= 0.75 and score_bot >= 0.85:
                        self.log(f"[终极安全-通过]: 锁定目标！总分:{base_score:.3f} | 顶部车名:{score_top:.2f} | 右下调校:{score_bot:.2f}")
                        return (
                            x + w_m // 2 + (region[0] if region else 0),
                            y + h_m // 2 + (region[1] if region else 0),
                        )

            return None
        except Exception as e:
            self.log(f"ultimate_safe 异常: {e}")
            return None

    def wait_for_image_ultimate_safe(self, main_path, anti_path, region=None, main_threshold=0.80, anti_threshold=0.65, timeout=3, interval=0.2, mask_areas=None):
        return self._wait_for_match(
            lambda: self.find_image_ultimate_safe(
                main_path,
                anti_path,
                region=region,
                main_threshold=main_threshold,
                anti_threshold=anti_threshold,
                mask_areas=mask_areas,
            ),
            timeout=timeout,
            interval=interval,
        )

    def find_image_smart(self, template_path, primary_region=None, fallback_region=None, threshold=0.75, fast_mode=True):
        if primary_region:
            pos = self.find_image(template_path, region=primary_region, threshold=threshold, fast_mode=fast_mode)
            if pos:
                return pos

        if fallback_region:
            return self.find_image(template_path, region=fallback_region, threshold=threshold, fast_mode=fast_mode)

        return None

    def match_template_score(self, src, template):
        try:
            if template is None or src is None:
                return 0.0
            th, tw = template.shape[:2]
            sh, sw = src.shape[:2]
            if th < 5 or tw < 5 or th > sh or tw > sw:
                return 0.0
            result = cv2.matchTemplate(src, template, cv2.TM_CCOEFF_NORMED)
            return cv2.minMaxLoc(result)[1]
        except Exception:
            return 0.0

    def _wait_for_match(self, match_once, timeout=30, interval=0.4, log_text=None):
        start = time.time()

        while self.is_running():
            if self._handle_pause_if_needed():
                start = time.time()
            if time.time() - start >= timeout:
                break

            pos = match_once()
            if pos:
                return pos

            if log_text:
                self.log(log_text)

            self._sleep_while_running(interval)

        return None

    def to_gray_image(self, img):
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    def to_edge_image(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        return cv2.Canny(blur, 50, 150)

    def crop_center_ratio(self, img, ratio=0.6):
        h, w = img.shape[:2]
        ch = int(h * ratio)
        cw = int(w * ratio)
        y1 = max(0, (h - ch) // 2)
        x1 = max(0, (w - cw) // 2)
        return img[y1:y1 + ch, x1:x1 + cw]
