import os
import tempfile
import unittest

import cv2
import numpy as np
from PIL import Image

from fh6auto_core.vision_service import VisionService


def make_service(app_dir, internal_dir=None, **kwargs):
    internal_dir = internal_dir or app_dir
    return VisionService(
        app_dir=app_dir,
        internal_dir=internal_dir,
        cache_dir=os.path.join(app_dir, "cache"),
        template_cache_file=os.path.join(app_dir, "cache", "template_cache.pkl"),
        template_meta_file=os.path.join(app_dir, "cache", "template_meta.json"),
        current_version="test",
        logger=lambda message: None,
        regions_provider=lambda: {"全界面": (0, 0, 2560, 1440)},
        screen_size_provider=lambda: (2560, 1440),
        **kwargs,
    )


class VisionServiceTests(unittest.TestCase):
    def test_image_path_prefers_external_images(self):
        with tempfile.TemporaryDirectory() as app_dir, tempfile.TemporaryDirectory() as internal_dir:
            os.makedirs(os.path.join(app_dir, "images"))
            os.makedirs(os.path.join(internal_dir, "images"))
            external_path = os.path.join(app_dir, "images", "needle.png")
            internal_path = os.path.join(internal_dir, "images", "needle.png")
            open(external_path, "wb").close()
            open(internal_path, "wb").close()

            service = make_service(app_dir, internal_dir)

            self.assertEqual(external_path, service.get_image_path("needle.png"))

    def test_scales_start_near_current_window_width(self):
        with tempfile.TemporaryDirectory() as app_dir:
            service = make_service(app_dir)

            self.assertEqual([1.0, 0.98, 1.02], service.get_scales_to_try()[:3])

    def test_capture_region_converts_to_bgr_and_masks_rectangles(self):
        image = Image.fromarray(np.full((4, 4, 3), [10, 20, 30], dtype=np.uint8), "RGB")
        calls = []

        def grabber(**kwargs):
            calls.append(kwargs)
            return image

        with tempfile.TemporaryDirectory() as app_dir:
            service = make_service(app_dir, image_grabber=grabber)

            captured = service.capture_region(region=(5, 6, 4, 4), mask_areas=[(1, 1, 3, 3)])

        self.assertEqual({"bbox": (5, 6, 9, 10), "all_screens": True}, calls[0])
        self.assertEqual((4, 4, 3), captured.shape)
        self.assertEqual([30, 20, 10], captured[0, 0].tolist())
        self.assertEqual([0, 0, 0], captured[1, 1].tolist())

    def test_find_image_in_screen_uses_template_cache_and_region_offset(self):
        with tempfile.TemporaryDirectory() as app_dir:
            images_dir = os.path.join(app_dir, "images")
            os.makedirs(images_dir)

            template = (np.arange(6 * 6 * 3, dtype=np.uint8).reshape((6, 6, 3)) * 2) % 255
            cv2.imwrite(os.path.join(images_dir, "needle.png"), template)

            screen = np.zeros((12, 12, 3), dtype=np.uint8)
            screen[4:10, 3:9] = template
            service = make_service(app_dir)

            pos = service.find_image_in_screen(
                screen,
                "needle.png",
                region=(10, 20, 12, 12),
                threshold=0.99,
                fast_mode=True,
            )

            self.assertEqual((16, 27), pos)
            self.assertEqual((16, 27), service.last_positions["needle.png"])

    def test_find_image_gray_supports_invert_mode(self):
        with tempfile.TemporaryDirectory() as app_dir:
            images_dir = os.path.join(app_dir, "images")
            os.makedirs(images_dir)

            template = (np.arange(6 * 6, dtype=np.uint8).reshape((6, 6)) * 5) % 255
            cv2.imwrite(os.path.join(images_dir, "gray.png"), template)

            screen = np.zeros((12, 12), dtype=np.uint8)
            screen[2:8, 3:9] = 255 - template
            image = Image.fromarray(screen, "L").convert("RGB")

            service = make_service(app_dir, image_grabber=lambda **kwargs: image)

            self.assertIsNone(service.find_image_gray("gray.png", region=(10, 20, 12, 12), threshold=0.99))
            self.assertEqual(
                (16, 25),
                service.find_image_gray("gray.png", region=(10, 20, 12, 12), threshold=0.99, invert_mode=True),
            )

    def test_find_any_image_transparent_matches_alpha_template(self):
        with tempfile.TemporaryDirectory() as app_dir:
            images_dir = os.path.join(app_dir, "images")
            os.makedirs(images_dir)

            template_bgr = (np.arange(6 * 6 * 3, dtype=np.uint8).reshape((6, 6, 3)) * 3) % 255
            alpha = np.full((6, 6, 1), 255, dtype=np.uint8)
            template_bgra = np.concatenate([template_bgr, alpha], axis=2)
            cv2.imwrite(os.path.join(images_dir, "alpha.png"), template_bgra)
            other_bgra = np.concatenate([255 - template_bgr, alpha], axis=2)
            cv2.imwrite(os.path.join(images_dir, "other.png"), other_bgra)

            screen_bgr = np.zeros((12, 12, 3), dtype=np.uint8)
            screen_bgr[4:10, 2:8] = template_bgr
            screen_rgb = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(screen_rgb, "RGB")

            service = make_service(app_dir, image_grabber=lambda **kwargs: image)

            self.assertEqual(
                (15, 27),
                service.find_any_image_transparent(["other.png", "alpha.png"], region=(10, 20, 12, 12), threshold=0.99),
            )

    def test_wait_for_any_image_gray_uses_pause_handler(self):
        with tempfile.TemporaryDirectory() as app_dir:
            paused = [True]
            pause_calls = []
            service = make_service(
                app_dir,
                paused_checker=lambda: paused[0],
                pause_handler=lambda: (pause_calls.append("paused"), paused.__setitem__(0, False)),
            )
            service.find_any_image_gray = lambda *args, **kwargs: (1, 2)

            self.assertEqual((1, 2), service.wait_for_any_image_gray(["any.png"], timeout=1, interval=0))
            self.assertEqual(["paused"], pause_calls)

    def test_find_image_with_element_matches_sub_template_inside_main(self):
        with tempfile.TemporaryDirectory() as app_dir:
            images_dir = os.path.join(app_dir, "images")
            os.makedirs(images_dir)

            main_template = (np.arange(10 * 10 * 3, dtype=np.uint8).reshape((10, 10, 3)) * 7) % 255
            sub_template = main_template[2:8, 3:9]
            cv2.imwrite(os.path.join(images_dir, "main.png"), main_template)
            cv2.imwrite(os.path.join(images_dir, "sub.png"), sub_template)

            screen_bgr = np.zeros((24, 24, 3), dtype=np.uint8)
            screen_bgr[5:15, 4:14] = main_template
            screen_rgb = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2RGB)
            service = make_service(app_dir, image_grabber=lambda **kwargs: Image.fromarray(screen_rgb, "RGB"))

            self.assertEqual(
                (19, 30),
                service.find_image_with_element("main.png", "sub.png", region=(10, 20, 24, 24), threshold=0.99),
            )

    def test_find_image_with_element_fast_matches_grayscale_pair(self):
        with tempfile.TemporaryDirectory() as app_dir:
            images_dir = os.path.join(app_dir, "images")
            os.makedirs(images_dir)

            main_template = (np.arange(10 * 10, dtype=np.uint8).reshape((10, 10)) * 3) % 255
            sub_template = main_template[2:8, 3:9]
            cv2.imwrite(os.path.join(images_dir, "main_gray.png"), main_template)
            cv2.imwrite(os.path.join(images_dir, "sub_gray.png"), sub_template)

            screen_gray = np.zeros((24, 24), dtype=np.uint8)
            screen_gray[6:16, 5:15] = main_template
            service = make_service(
                app_dir,
                image_grabber=lambda **kwargs: Image.fromarray(screen_gray, "L").convert("RGB"),
            )

            self.assertEqual(
                (20, 31),
                service.find_image_with_element_fast("main_gray.png", "sub_gray.png", region=(10, 20, 24, 24), threshold=0.99, sub_threshold=0.99),
            )

    def test_find_image_ultimate_safe_matches_main_without_anti_template(self):
        with tempfile.TemporaryDirectory() as app_dir:
            images_dir = os.path.join(app_dir, "images")
            os.makedirs(images_dir)

            main_template = (np.arange(48 * 48 * 3, dtype=np.uint8).reshape((48, 48, 3)) * 5) % 255
            cv2.imwrite(os.path.join(images_dir, "ultimate.png"), main_template)

            screen_bgr = np.zeros((90, 90, 3), dtype=np.uint8)
            screen_bgr[12:60, 10:58] = main_template
            screen_rgb = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2RGB)
            service = make_service(app_dir, image_grabber=lambda **kwargs: Image.fromarray(screen_rgb, "RGB"))

            self.assertEqual(
                (134, 236),
                service.find_image_ultimate_safe("ultimate.png", None, region=(100, 200, 90, 90), main_threshold=0.99),
            )


if __name__ == "__main__":
    unittest.main()
