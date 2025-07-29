import collections
import os.path
import pathlib
import unittest

import cv2
import numpy as np

import dito

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None
    print("Could not import matplotlib -- skipping its related tests")


####
#%%% base classes
####


class TestCase(unittest.TestCase):
    """
    Base class for test cases.
    """
    
    def assertNumpyShape(self, image, shape):
        self.assertIsInstance(image, np.ndarray)
        self.assertEqual(image.shape, shape)
    
    def assertIsImage(self, x):
        self.assertTrue(dito.is_image(image=x))
    
    def assertEqualImageContainers(self, x, y, enforce_is_image=True):
        if enforce_is_image:
            self.assertIsImage(x)
            self.assertIsImage(y)
        self.assertEqual(x.dtype, y.dtype)
        self.assertEqual(x.shape, y.shape)
    
    def assertEqualImages(self, x, y, enforce_is_image=True):
        self.assertEqualImageContainers(x, y, enforce_is_image=enforce_is_image)
        if np.issubdtype(x.dtype, np.floating):
            self.assertTrue(np.allclose(x, y))
        else:
            self.assertTrue(np.all(x == y))

    def assertDifferingImages(self, x, y):
        self.assertEqualImageContainers(x=x, y=y)
        self.assertTrue(np.any(x != y))


class TempDirTestCase(TestCase):
    def setUp(self):
        self.temp_dir = dito.get_temp_dir(prefix="dito.tests.")

    def tearDown(self):
        self.temp_dir.cleanup()


class DiffTestCase(TestCase):
    def setUp(self):
        self.image1_bool = np.array([[False, True]], dtype=bool)
        self.image2_bool = np.array([[True, False]], dtype=bool)

        self.image1_int8 = np.array([[-128, 127]], dtype=np.int8)
        self.image2_int8 = np.array([[127, -128]], dtype=np.int8)

        self.image1_uint8 = np.array([[0, 255]], dtype=np.uint8)
        self.image2_uint8 = np.array([[255, 0]], dtype=np.uint8)

        self.image1_float32 = np.array([[0.0, 1.0]], dtype=np.float32)
        self.image2_float32 = np.array([[1.0, 0.0]], dtype=np.float32)

        self.image1_float64 = np.array([[0.0, 1.0]], dtype=np.float64)
        self.image2_float64 = np.array([[1.0, 0.0]], dtype=np.float64)


####
#%%% test cases
####


class CachedImageLoader_Test(TempDirTestCase):
    def test_CachedImageLoader_init(self):
        max_count = 8
        loader = dito.CachedImageLoader(max_count=max_count)
        self.assertEqual(loader.get_cache_info().maxsize, max_count)
        self.assertEqual(loader.get_cache_info().hits, 0)
        self.assertEqual(loader.get_cache_info().misses, 0)

    def test_CachedImageLoader_hit_nohit(self):
        # save two images
        image = dito.xslope()
        filename_0 = os.path.join(self.temp_dir.name, "image_0.png")
        filename_1 = os.path.join(self.temp_dir.name, "image_1.png")
        dito.save(filename=filename_0, image=image)
        dito.save(filename=filename_1, image=image)

        loader = dito.CachedImageLoader(max_count=4)

        # miss
        loader.load(filename=filename_0)
        self.assertEqual(loader.get_cache_info().hits, 0)
        self.assertEqual(loader.get_cache_info().misses, 1)

        # hit
        loader.load(filename=filename_0)
        self.assertEqual(loader.get_cache_info().hits, 1)
        self.assertEqual(loader.get_cache_info().misses, 1)

        # hit
        loader.load(filename=filename_0)
        self.assertEqual(loader.get_cache_info().hits, 2)
        self.assertEqual(loader.get_cache_info().misses, 1)

        # miss
        loader.load(filename=filename_1)
        self.assertEqual(loader.get_cache_info().hits, 2)
        self.assertEqual(loader.get_cache_info().misses, 2)

        # hit
        loader.load(filename=filename_1)
        self.assertEqual(loader.get_cache_info().hits, 3)
        self.assertEqual(loader.get_cache_info().misses, 2)

    def test_CachedImageLoader_raise(self):
        loader = dito.CachedImageLoader(max_count=4)
        filename = os.path.join(self.temp_dir.name, "__nonexistent__.png")
        self.assertRaises(FileNotFoundError, lambda: loader.load(filename=filename))


class abs_diff_Tests(DiffTestCase):
    def test_abs_diff_bool(self):
        result = dito.abs_diff(image1=self.image1_bool, image2=self.image2_bool)
        expected_result = np.array([[1, 1]], dtype=bool)
        self.assertEqualImages(result, expected_result)

    def test_abs_diff_int8(self):
        result = dito.abs_diff(image1=self.image1_int8, image2=self.image2_int8)
        expected_result = np.array([[127, 127]], dtype=np.int8)
        self.assertEqualImages(result, expected_result)

    def test_abs_diff_uint8(self):
        result = dito.abs_diff(image1=self.image1_uint8, image2=self.image2_uint8)
        expected_result = np.array([[255, 255]], dtype=np.uint8)
        self.assertEqualImages(result, expected_result)

    def test_abs_diff_float32(self):
        result = dito.abs_diff(image1=self.image1_float32, image2=self.image2_float32)
        expected_result = np.array([[1.0, 1.0]], dtype=np.float32)
        self.assertEqualImages(result, expected_result)

    def test_abs_diff_float64(self):
        result = dito.abs_diff(image1=self.image1_float64, image2=self.image2_float64)
        expected_result = np.array([[1.0, 1.0]], dtype=np.float64)
        self.assertEqualImages(result, expected_result)


class adaptive_round_Tests(TestCase):
    def test_adaptive_round_python_float_zero(self):
        number = 0.0
        self.assertIsInstance(dito.adaptive_round(number=number, digit_count=4), float)
        self.assertEqual(dito.adaptive_round(number=number, digit_count=1), 0.0)
        self.assertEqual(dito.adaptive_round(number=number, digit_count=6), 0.0)

    def test_adaptive_round_python_float(self):
        number = 123.456789
        self.assertIsInstance(dito.adaptive_round(number=number, digit_count=4), float)
        self.assertEqual(dito.adaptive_round(number=number, digit_count=1), 100.0)
        self.assertEqual(dito.adaptive_round(number=number, digit_count=2), 120.0)
        self.assertEqual(dito.adaptive_round(number=number, digit_count=3), 123.0)
        self.assertEqual(dito.adaptive_round(number=number, digit_count=4), 123.5)
        self.assertEqual(dito.adaptive_round(number=number, digit_count=5), 123.46)
        self.assertEqual(dito.adaptive_round(number=number, digit_count=6), 123.457)

    def test_adaptive_round_python_int(self):
        number = 123
        self.assertIsInstance(dito.adaptive_round(number=number, digit_count=4), int)
        self.assertEqual(dito.adaptive_round(number=number, digit_count=1), 100)
        self.assertEqual(dito.adaptive_round(number=number, digit_count=2), 120)
        self.assertEqual(dito.adaptive_round(number=number, digit_count=3), 123)
        self.assertEqual(dito.adaptive_round(number=number, digit_count=4), 123)
        self.assertEqual(dito.adaptive_round(number=number, digit_count=5), 123)
        self.assertEqual(dito.adaptive_round(number=number, digit_count=6), 123)

    def test_adaptive_round_numpy_float32_scalar(self):
        number = np.float32(123.456789)
        self.assertIsInstance(dito.adaptive_round(number=number, digit_count=4), np.float32)
        self.assertAlmostEqual(float(dito.adaptive_round(number=number, digit_count=1)), 100.0)
        self.assertAlmostEqual(float(dito.adaptive_round(number=number, digit_count=2)), 120.0)
        self.assertAlmostEqual(float(dito.adaptive_round(number=number, digit_count=3)), 123.0)
        self.assertAlmostEqual(float(dito.adaptive_round(number=number, digit_count=4)), 123.5)

    def test_adaptive_round_numpy_float64_scalar(self):
        number = np.float64(123.456789)
        self.assertIsInstance(dito.adaptive_round(number=number, digit_count=4), np.float64)
        self.assertAlmostEqual(float(dito.adaptive_round(number=number, digit_count=1)), 100.0)
        self.assertAlmostEqual(float(dito.adaptive_round(number=number, digit_count=2)), 120.0)
        self.assertAlmostEqual(float(dito.adaptive_round(number=number, digit_count=3)), 123.0)
        self.assertAlmostEqual(float(dito.adaptive_round(number=number, digit_count=4)), 123.5)
        self.assertAlmostEqual(float(dito.adaptive_round(number=number, digit_count=5)), 123.46)
        self.assertAlmostEqual(float(dito.adaptive_round(number=number, digit_count=6)), 123.457)

    def test_adaptive_round_numpy_uint8_scalar(self):
        number = np.uint8(123)
        self.assertIsInstance(dito.adaptive_round(number=number, digit_count=4), np.uint8)
        self.assertEqual(int(dito.adaptive_round(number=number, digit_count=1)), 100)
        self.assertEqual(int(dito.adaptive_round(number=number, digit_count=2)), 120)
        self.assertEqual(int(dito.adaptive_round(number=number, digit_count=3)), 123)
        self.assertEqual(int(dito.adaptive_round(number=number, digit_count=4)), 123)


class as_channel_Tests(TestCase):
    def test_as_channels_raise_on_none(self):
        self.assertRaises(ValueError, lambda: dito.as_channels(b=None, g=None, r=None))

    def test_as_channels_raise_on_color(self):
        image = dito.pm5544()
        self.assertRaises(ValueError, lambda: dito.as_channels(b=image, g=None, r=None))

    def test_as_channels_single(self):
        image = dito.pm5544()
        image_b = dito.as_gray(image=image)
        image_rgb = dito.as_channels(b=image_b, g=None, r=None)
        self.assertEqualImageContainers(dito.as_color(image=image_b), image_rgb)
        self.assertEqualImages(image_b, image_rgb[:, :, 0])
        self.assertEqual(np.sum(image_rgb[:, :, 1]), 0)
        self.assertEqual(np.sum(image_rgb[:, :, 2]), 0)

    def test_as_channels_all(self):
        image = dito.pm5544()
        image_b = image[:, :, 0]
        image_g = image[:, :, 1]
        image_r = image[:, :, 2]
        image_rgb = dito.as_channels(b=image_b, g=image_g, r=image_r)
        self.assertEqualImages(image, image_rgb)


class as_color_Tests(TestCase):
    def test_as_color(self):
        image = dito.pm5544()
        image_b = image[:, :, 0]
        image_c = dito.as_color(image_b)
        self.assertTrue(dito.is_color(image_c))
        self.assertEqual(image_c.shape, image_b.shape + (3,))
        for n_channel in range(3):
            self.assertEqualImages(image_c[:, :, n_channel], image_b)

    def test_as_color_noop(self):
        image = dito.pm5544()
        self.assertEqualImages(image, dito.as_color(image))


class as_gray_Tests(TestCase):
    def test_as_gray(self):
        image = dito.pm5544()
        self.assertTrue(dito.is_color(image))
        image_g = dito.as_gray(image)
        self.assertTrue(dito.is_gray(image_g))
        self.assertEqual(image_g.shape, image.shape[:2])

    def test_as_gray_noop(self):
        image = dito.pm5544()[:, :, 0]
        self.assertEqualImages(image, dito.as_gray(image))

    def test_as_gray_with_keep_color_dimension_of_color_input(self):
        image = dito.pm5544()
        image_gray = dito.as_gray(image, keep_color_dimension=True)
        self.assertTrue(dito.is_gray(image_gray))
        self.assertEqual(image_gray.shape, image.shape[:2] + (1,))

    def test_as_gray_with_keep_color_dimension_of_gray_input(self):
        image = dito.pm5544()[:, :, 0]
        image_gray = dito.as_gray(image, keep_color_dimension=True)
        self.assertTrue(dito.is_gray(image_gray))
        self.assertEqual(image_gray.shape, image.shape + (1,))
        self.assertEqualImages(image, image_gray[:, :, 0])

    def test_as_gray_with_keep_color_dimension_noop(self):
        image = dito.pm5544()[:, :, 0]
        image.shape += (1,)
        image_gray = dito.as_gray(image, keep_color_dimension=True)
        self.assertTrue(dito.is_gray(image_gray))
        self.assertEqual(image_gray.shape, image.shape)
        self.assertEqualImages(image, image_gray)


class clip_Tests(TestCase):
    def test_clip_01(self):
        image = np.array([[-2.0, -1.0, 0.0, 1.0, 2.0]], dtype=np.float32)
        image_clipped = dito.clip_01(image=image)
        image_expected = np.array([[0.0, 0.0, 0.0, 1.0, 1.0]], dtype=np.float32)
        self.assertEqualImages(image_clipped, image_expected)

    def test_clip_input_unchanged(self):
        image = np.array([[-2.0, -1.0, 0.0, 1.0, 2.0]], dtype=np.float32)
        image_copy = image.copy()
        image_clipped = dito.clip_01(image=image)
        self.assertEqualImages(image, image_copy)


class clipped_diff_Tests(DiffTestCase):
    def test_clipped_diff_bool(self):
        result = dito.clipped_diff(image1=self.image1_bool, image2=self.image2_bool)
        expected_result = np.array([[False, True]], dtype=bool)
        self.assertEqualImages(result, expected_result)

    def test_clipped_diff_int8(self):
        result = dito.clipped_diff(image1=self.image1_int8, image2=self.image2_int8)
        expected_result = np.array([[-128, 127]], dtype=np.int8)
        self.assertEqualImages(result, expected_result)

    def test_clipped_diff_uint8(self):
        result = dito.clipped_diff(image1=self.image1_uint8, image2=self.image2_uint8)
        expected_result = np.array([[0, 255]], dtype=np.uint8)
        self.assertEqualImages(result, expected_result)

    def test_clipped_diff_float32(self):
        result = dito.clipped_diff(image1=self.image1_float32, image2=self.image2_float32)
        expected_result = np.array([[0.0, 1.0]], dtype=np.float32)
        self.assertEqualImages(result, expected_result)

    def test_clipped_diff_float64(self):
        result = dito.clipped_diff(image1=self.image1_float64, image2=self.image2_float64)
        expected_result = np.array([[0.0, 1.0]], dtype=np.float64)
        self.assertEqualImages(result, expected_result)


class colorize_Tests(TestCase):
    def test_colorize_colormap(self):
        image = dito.xslope(height=32, width=256)
        self.assertTrue(dito.is_gray(image=image))
        image_colorized = dito.colorize(image=image, colormap=dito.get_colormap(name="jet"))
        self.assertTrue(dito.is_color(image=image_colorized))

    def test_colorize_name(self):
        image = dito.xslope(height=32, width=256)
        self.assertTrue(dito.is_gray(image=image))
        image_colorized = dito.colorize(image=image, colormap="jet")
        self.assertTrue(dito.is_color(image=image_colorized))

    def test_colorize_identical_to_applyColormap(self):
        images = [
            dito.xslope(height=32, width=256),
            dito.pm5544(),
            dito.random_image(size=(128, 128), color=True),
        ]
        for image in images:
            image_colorized_dito = dito.colorize(image=image, colormap="jet")
            image_colorized_applyColormap = cv2.applyColorMap(src=image, colormap=cv2.COLORMAP_JET)
            self.assertEqualImages(image_colorized_dito, image_colorized_applyColormap)

    def test_colorize_float_image_raises_error(self):
        image = dito.xslope(height=32, width=256)
        image = dito.convert(image=image, dtype=np.float32)
        self.assertRaises(cv2.error, lambda: dito.colorize(image=image, colormap="jet"))


class constant_image_Tests(TestCase):
    def setUp(self):
        self.size = (128, 64)
        self.color = (50, 100, 200)
        self.result_image = dito.constant_image(size=self.size, color=self.color)

    def test_constant_image_size(self):
        self.assertEqual(dito.size(image=self.result_image), self.size)

    def test_constant_image_gray(self):
        result_image = dito.constant_image(size=self.size, color=self.color[:1])
        self.assertEqual(len(result_image.shape), 2)

    def test_constant_image_color(self):
        self.assertEqual(len(self.result_image.shape), 3)
        self.assertEqual(self.result_image.shape[2], 3)

    def test_constant_image_values(self):
        channel_count = len(self.color)
        for n_channel in range(channel_count):
            self.assertTrue(np.all(self.result_image[:, :, n_channel] == self.color[n_channel]))


class ContourFinder_Tests(TestCase):
    def setUp(self):
        self.image = dito.test_image_segments()
        self.contour_finder = dito.ContourFinder(image=self.image)

    def test_ContourFinder_copy(self):
        contour_finder_copy_1 = self.contour_finder.copy()
        contour_finder_copy_2 = contour_finder_copy_1.copy()
        contour_finder_copy_1[0].shift(offset_x=1)
        self.assertEqual(len(contour_finder_copy_1), len(contour_finder_copy_2))
        self.assertNotEqual(contour_finder_copy_1, contour_finder_copy_2)

    def test_CountourFinder_count(self):
        self.assertEqual(len(self.contour_finder), 40)

    def test_ContourFinder_filter_center_x(self):
        self.contour_finder.filter_center_x(min_value=128)
        self.assertEqual(len(self.contour_finder), 20)

    def test_ContourFinder_filter_center_y(self):
        self.contour_finder.filter_center_y(min_value=144)
        self.assertEqual(len(self.contour_finder), 16)

    def test_ContourFinder_filter_area(self):
        self.contour_finder.filter_area(min_value=400, max_value=800)
        self.assertEqual(len(self.contour_finder), 9)

    def test_ContourFinder_filter_area_calc(self):
        self.contour_finder.filter_area(min_value=400, max_value=800, mode="calc")
        self.assertEqual(len(self.contour_finder), 10)

    def test_ContourFinder_filter_perimeter(self):
        self.contour_finder.filter_perimeter(min_value=50, max_value=100)
        self.assertEqual(len(self.contour_finder), 16)

    def test_ContourFinder_filter_circularity(self):
        self.contour_finder.filter_circularity(min_value=0.95)
        self.assertEqual(len(self.contour_finder), 13)

    def test_ContourFinder_filter_multiple(self):
        self.contour_finder.filter_area(min_value=250, max_value=350)
        self.contour_finder.filter_perimeter(min_value=50, max_value=150)
        self.assertEqual(len(self.contour_finder), 5)


class convert_Tests(TestCase):
    def test_convert_identical(self):
        image = dito.xslope(height=32, width=256)
        image_converted = dito.convert(image=image, dtype=np.uint8)
        self.assertEqualImages(image, image_converted)

    def test_convert_loop(self):
        image = dito.xslope(height=32, width=256)
        image_converted = dito.convert(image=image, dtype=np.float32)
        image_converted_2 = dito.convert(image=image_converted, dtype=np.uint8)
        self.assertEqualImages(image, image_converted_2)

    def test_convert_uint8_float32(self):
        image = dito.xslope(height=32, width=256)
        image_converted = dito.convert(image=image, dtype=np.float32)
        self.assertAlmostEqual(np.min(image_converted), 0.0)
        self.assertAlmostEqual(np.max(image_converted), 1.0)

    def test_convert_bool_uint8(self):
        image = np.array([[False, True]], dtype=np.bool_)
        image_converted = dito.convert(image=image, dtype=np.uint8)
        self.assertEqual(image_converted[0, 0], 0)
        self.assertEqual(image_converted[0, 1], 255)

    def test_convert_color(self):
        image_gray = dito.xslope(height=32, width=256)
        image_color = dito.as_color(image=image_gray.copy())
        image_gray_converted = dito.convert(image=image_gray, dtype=np.float32)
        image_color_converted = dito.convert(image=image_color, dtype=np.float32)
        self.assertEqualImages(image_gray_converted, dito.as_gray(image=image_color_converted))

    def test_convert_input_unchanged(self):
        image = np.array([[-2.0, -1.0, 0.0, 1.0, 2.0]], dtype=np.float32)
        image_copy = image.copy()
        dito.convert(image=image, dtype=np.uint8)
        self.assertEqualImages(image, image_copy)

    def test_convert_float_clipped(self):
        image = np.array([[-2.0, -1.0, 0.0, 1.0, 2.0]], dtype=np.float32)
        image_clipped = dito.convert(image=image, dtype=np.float32)
        self.assertAlmostEqual(np.min(image_clipped), 0.0)
        self.assertAlmostEqual(np.max(image_clipped), 1.0)


class convert_color_Tests(TestCase):
    def test_convert_color_argument_is_color(self):
        bgr = (0, 255, 0)
        hsv = dito.convert_color(image_or_color=bgr, code=cv2.COLOR_BGR2HSV)
        self.assertEqual(hsv, (60, 255, 255))

    def test_convert_color_argument_is_image(self):
        image = dito.pm5544()
        image_hsv = dito.convert_color(image_or_color=image, code=cv2.COLOR_BGR2HSV)
        self.assertEqualImageContainers(image, image_hsv)

    def test_convert_color_alias_bgr_to_hsv(self):
        image = dito.pm5544()
        image_hsv_1 = dito.convert_color(image_or_color=image, code=cv2.COLOR_BGR2HSV)
        image_hsv_2 = dito.bgr_to_hsv(image_or_color=image)
        self.assertEqualImages(image_hsv_1, image_hsv_2)


    def test_convert_color_alias_hsv_to_bgr(self):
        image = dito.pm5544()
        image_bgr_1 = dito.convert_color(image_or_color=image, code=cv2.COLOR_HSV2BGR)
        image_bgr_2 = dito.hsv_to_bgr(image_or_color=image)
        self.assertEqualImages(image_bgr_1, image_bgr_2)


class cv_version_Tests(TestCase):
    def test_cv2_version(self):
        version = dito.cv2_version()
        self.assertIsInstance(version, tuple)
        self.assertEqual(len(version), 3)
        for number in version:
            self.assertIsInstance(number, int)


class dtype_common_Test(TestCase):
    def test_dtype_common_cases(self):
        cases = [
            {"arg": ["uint8"], "expected_result": np.uint8},
            {"arg": ["uint8", "uint8"], "expected_result": np.uint8},
            {"arg": ["uint8", "bool"], "expected_result": np.uint8},
            {"arg": ["bool", "uint8"], "expected_result": np.uint8},
            {"arg": ["bool", "uint8", "uint16"], "expected_result": np.uint16},
            {"arg": ["uint8", "uint16"], "expected_result": np.uint16},
            {"arg": ["uint8", "float32"], "expected_result": np.float32},
            {"arg": ["uint8", "float64"], "expected_result": np.float64},
            {"arg": ["float32", "float64"], "expected_result": np.float64},
            {"arg": ["double"], "expected_result": np.float64},
            {"arg": [np.uint8], "expected_result": np.uint8},
            {"arg": [np.bool_, "uint8", np.uint16], "expected_result": np.uint16},
        ]
        for case in cases:
            result = dito.dtype_common(dtypes=case["arg"])
            self.assertEqual(result, case["expected_result"])

    def test_dtype_common_raise(self):
        self.assertRaises(ValueError, lambda: dito.dtype_common(dtypes=["__non-existing-dtype__"]))


class dtype_range_Tests(TestCase):
    def test_dtype_range_uint8(self):
        range_ = dito.dtype_range(dtype=np.uint8)
        self.assertEqual(range_, (0, 2**8 - 1))
        
    def test_dtype_range_uint16(self):
        range_ = dito.dtype_range(dtype=np.uint16)
        self.assertEqual(range_, (0, 2**16 - 1))
    
    def test_dtype_range_uint32(self):
        range_ = dito.dtype_range(dtype=np.uint32)
        self.assertEqual(range_, (0, 2**32 - 1))
    
    def test_dtype_range_int8(self):
        range_ = dito.dtype_range(dtype=np.int8)
        self.assertEqual(range_, (-2**7, 2**7 - 1))
    
    def test_dtype_range_int16(self):
        range_ = dito.dtype_range(dtype=np.int16)
        self.assertEqual(range_, (-2**15, 2**15 - 1))
    
    def test_dtype_range_int32(self):
        range_ = dito.dtype_range(dtype=np.int32)
        self.assertEqual(range_, (-2**31, 2**31 - 1))
    
    def test_dtype_range_float(self):
        range_ = dito.dtype_range(dtype=float)
        self.assertEqual(range_, (0, 1.0))
    
    def test_dtype_range_float32(self):
        range_ = dito.dtype_range(dtype=np.float32)
        self.assertEqual(range_, (0, 1.0))
        
    def test_dtype_range_float64(self):
        range_ = dito.dtype_range(dtype=np.float64)
        self.assertEqual(range_, (0, 1.0))
        
    def test_dtype_range_bool(self):
        range_ = dito.dtype_range(dtype=np.bool_)
        self.assertEqual(range_, (False, True))


@unittest.skipIf(plt is None, "Skipped due to failed matplotlib import")
class fig_to_image_Tests(TestCase):
    def setUp(self):
        # create matplotlib plot
        (self.fig, self.ax) = plt.subplots()
        xs = list(range(10))
        ys = [x**2 for x in xs]
        self.ax.plot(xs, ys)

    def test_fig_to_image_shape(self):
        sizes = [
            (640, 480),
            (800, 600),
            (1600, 900),
        ]
        for size in sizes:
            image = dito.fig_to_image(fig=self.fig, size=size)
            self.assertNumpyShape(image, (size[1], size[0], 3))

    def test_fig_to_image_dtype(self):
        image = dito.fig_to_image(fig=self.fig)
        self.assertEqual(image.dtype, np.uint8)

    def test_fig_to_image_white_background(self):
        image = dito.fig_to_image(fig=self.fig, size=(800, 600))
        self.assertTrue(np.all(image[0, 0, :] == np.array([255, 255, 255], dtype=np.uint8)))

    def test_fig_to_image_savefig_kwargs(self):
        image_default = dito.fig_to_image(fig=self.fig, size=(300, 200))
        image_custom = dito.fig_to_image(fig=self.fig, size=(300, 200), savefig_kwargs=dict(facecolor="black"))
        self.assertEqualImageContainers(image_default, image_custom)
        self.assertDifferingImages(image_default, image_custom)


class encode_Tests(TestCase):
    def test_encode_extensions(self):
        image = dito.pm5544()
        extensions = ("jpg", "png")
        for extension in extensions:
            for prefix in ("", "."):
                dito.encode(extension="{}{}".format(prefix, extension), image=image)

    def test_encode_byte(self):
        image = dito.pm5544()
        result = dito.encode(extension=".png", image=image)
        self.assertIsInstance(result, bytes)

    def test_encode_decode(self):
        image = dito.pm5544()
        image_encoded = dito.encode(image=image)
        image_decoded = dito.decode(b=image_encoded)
        self.assertEqualImages(image, image_decoded)


class gamma_Tests(TestCase):
    def setUp(self):
        self.image = dito.pm5544()

    def test_gamma_input_unchanged(self):
        image_copy = self.image.copy()
        dito.gamma(image=self.image, exponent=0.5)
        self.assertEqualImages(self.image, image_copy)

    def test_gamma_shape_unchanged(self):
        image_gamma = dito.gamma(image=self.image, exponent=0.5)
        self.assertEqualImageContainers(image_gamma, self.image)

    def test_gamma_shape_with_gray_axis_unchanged(self):
        image_1 = dito.pm5544()
        image_1 = image_1[:, :, 0:1]
        image_gamma = dito.gamma(image=image_1, exponent=0.5)
        self.assertEqualImageContainers(image_gamma, image_1)

    def test_gamma_1_0_unchanged(self):
        image_gamma = dito.gamma(image=self.image, exponent=1.0)
        self.assertEqualImages(image_gamma, self.image)

    def test_gamma_0_5_brighter(self):
        image_gamma = dito.gamma(image=self.image, exponent=0.5)
        self.assertEqualImageContainers(image_gamma, self.image)
        self.assertTrue(np.mean(image_gamma) > np.mean(self.image))

    def test_gamma_2_0_darker(self):
        image_gamma = dito.gamma(image=self.image, exponent=2.0)
        self.assertEqualImageContainers(image_gamma, self.image)
        self.assertTrue(np.mean(image_gamma) < np.mean(self.image))


class get_colormap_Tests(TestCase):
    def test_get_colormap_plot(self):
        result = dito.get_colormap("plot")
        self.assertTrue(dito.is_colormap(result))
        self.assertEqual(result[0, 0, :].tolist(), [0, 0, 0])
        self.assertEqual(result[1, 0, :].tolist(), [0, 0, 255])
        self.assertEqual(result[2, 0, :].tolist(), [0, 255, 0])
        self.assertEqual(result[3, 0, :].tolist(), [255, 0, 0])
        self.assertEqual(result[255, 0, :].tolist(), [255, 255, 255])

    def test_get_colormap_jet(self):
        result = dito.get_colormap("jet")
        self.assertTrue(dito.is_colormap(result))

    def test_get_colormap_raise(self):
        self.assertRaises(ValueError, lambda: dito.get_colormap("__!?-non-existing_colormap-name-!?__"))


class hash_bytes_Tests(TestCase):
    def test_hash_bytes_sha512_test_vectors(self):
        digest = dito.hash_bytes(bytes_=b"", cutoff_position=None, return_hex=True)
        self.assertEqual(digest, "cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e")

        digest = dito.hash_bytes(bytes_=b"abc", cutoff_position=None, return_hex=True)
        self.assertEqual(digest, "ddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a2192992a274fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f")

    def test_hash_bytes_cutoff_positions(self):
        expected_digest = "ddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a2192992a274fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f"

        digest = dito.hash_bytes(bytes_=b"abc", cutoff_position=None, return_hex=True)
        self.assertEqual(digest, expected_digest)

        digest = dito.hash_bytes(bytes_=b"abc", cutoff_position=0, return_hex=True)
        self.assertEqual(digest, "")

        digest = dito.hash_bytes(bytes_=b"abc", cutoff_position=1, return_hex=True)
        self.assertEqual(digest, "d")

        digest = dito.hash_bytes(bytes_=b"abc", cutoff_position=8, return_hex=True)
        self.assertEqual(digest, expected_digest[:8])

        digest = dito.hash_bytes(bytes_=b"abc", cutoff_position=-126, return_hex=True)
        self.assertEqual(digest, expected_digest[:2])

    def test_hash_bytes_no_hex(self):
        expected_digest = "ddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a2192992a274fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f"

        digest = dito.hash_bytes(bytes_=b"abc", cutoff_position=None, return_hex=False)
        self.assertEqual(digest, bytes.fromhex(expected_digest))

        digest = dito.hash_bytes(bytes_=b"abc", cutoff_position=8, return_hex=False)
        self.assertEqual(digest, bytes.fromhex(expected_digest)[:8])


class hash_file_Tests(TestCase):
    def test_hash_file_pm5544(self):
        path = dito.RESOURCES_FILENAMES["image:PM5544"]
        digest = dito.hash_file(path=path, cutoff_position=None, return_hex=True)
        expected_digest = "293947fa7b569f8bb91caab5e24aacda5f6378215af07c3c7031418b30a6a5180680141706887042c57b281335ebbd038bdd95f81417bff4920a7247979b1f52"
        self.assertEqual(digest, expected_digest)


class hash_image_Tests(TestCase):
    def setUp(self):
        self.image = dito.pm5544()

    def test_hash_image_reference(self):
        hash_ = dito.hash_image(image=self.image, cutoff_position=None, return_hex=True)
        self.assertEqual(hash_, "265ea0683876d4b042854f1c129a12b1601aab1376ba8c55b97dd20020d1ee54e2da55a3bd78a53a838b4eadfe6898d069c9862a4185a135923c855ba0944aed")

    def test_hash_image_shape_dependence(self):
        image = self.image.copy()
        hash_original = dito.hash_image(image=image)

        image.shape = (1, -1)
        hash_flat = dito.hash_image(image=image)

        self.assertNotEqual(hash_original, hash_flat)

    def test_hash_image_dtype_dependence(self):
        image_empty_uint8 = np.zeros(shape=(0,), dtype=np.uint8)
        hash_empty_uint8 = dito.hash_image(image=image_empty_uint8)

        image_empty_float32 = image_empty_uint8.astype(np.float32)
        hash_empty_float32 = dito.hash_image(image=image_empty_float32)

        self.assertNotEqual(hash_empty_uint8, hash_empty_float32)


class hash_image_any_row_order_Tests(TestCase):
    def test_hash_image_any_row_order_reference(self):
        image = dito.pm5544()
        image_flip_ud = image[::-1, ...].copy()

        digest = dito.hash_image(image=image, cutoff_position=None, return_hex=True)
        digest_flip_ud = dito.hash_image(image=image_flip_ud, cutoff_position=None, return_hex=True)

        digest_any_row_order = dito.hash_image_any_row_order(image=image, cutoff_position=None, return_hex=True)
        digest_any_row_order_flip_ud = dito.hash_image_any_row_order(image=image_flip_ud, cutoff_position=None, return_hex=True)

        self.assertNotEqual(digest, digest_flip_ud)
        self.assertEqual(digest_any_row_order, digest_any_row_order_flip_ud)


class hash_image_any_col_order_Tests(TestCase):
    def test_hash_image_any_col_order_reference(self):
        image = dito.pm5544()
        image_flip_lr = image[:, ::-1, ...].copy()

        digest = dito.hash_image(image=image, cutoff_position=None, return_hex=True)
        digest_flip_lr = dito.hash_image(image=image_flip_lr, cutoff_position=None, return_hex=True)

        digest_any_col_order = dito.hash_image_any_col_order(image=image, cutoff_position=None, return_hex=True)
        digest_any_col_order_flip_lr = dito.hash_image_any_col_order(image=image_flip_lr, cutoff_position=None, return_hex=True)

        self.assertNotEqual(digest, digest_flip_lr)
        self.assertEqual(digest_any_col_order, digest_any_col_order_flip_lr)


class hash_image_any_pixel_order_Tests(TestCase):
    def test_hash_image_any_pixel_order_reference(self):
        image = dito.pm5544()
        image_shuffled = image.copy()
        np.random.default_rng(seed=123).shuffle(x=image_shuffled, axis=0)
        np.random.default_rng(seed=456).shuffle(x=image_shuffled, axis=1)

        digest = dito.hash_image(image=image, cutoff_position=None, return_hex=True)
        digest_shuffled = dito.hash_image(image=image_shuffled, cutoff_position=None, return_hex=True)

        digest_any_pixel_order = dito.hash_image_any_pixel_order(image=image, cutoff_position=None, return_hex=True)
        digest_any_pixel_order_shuffled = dito.hash_image_any_pixel_order(image=image_shuffled, cutoff_position=None, return_hex=True)

        self.assertNotEqual(digest, digest_shuffled)
        self.assertEqual(digest_any_pixel_order, digest_any_pixel_order_shuffled)


class human_bytes_Tests(TestCase):
    def test_human_bytes_exact(self):
        cases = [
            [0, "0 bytes"],
            [1, "1 bytes"],
            [123, "123 bytes"],
            [1000, "1000 bytes"],
            [1023, "1023 bytes"],
            [1024, "1.00 KiB"],
            [100000, "97.66 KiB"],
            [123456, "120.56 KiB"],
            [2000000, "1.91 MiB"],
            [5050505, "4.82 MiB"],
            [123456789, "117.74 MiB"],
            [12345678900, "11.50 GiB"],
        ]
        for (byte_count, expected_result) in cases:
            result = dito.human_bytes(byte_count=byte_count)
            self.assertEqual(result, expected_result)


class info_Tests(TestCase):
    def setUp(self):
        self.image = dito.pm5544()

    def test_info__noargs(self):
        info = dito.info(self.image)
        self.assertIsInstance(info, collections.OrderedDict)
        self.assertEqual(len(info.keys()), 7)
        self.assertEqual(info["shape"], (576, 768, 3))
        self.assertEqual(info["dtype"], np.uint8)
        self.assertEqual(info["hash"], "265ea068")

    def test_info__extended(self):
        info = dito.info(self.image, extended=True)
        self.assertEqual(len(info.keys()), 11)
        self.assertEqual(info["shape"], (576, 768, 3))
        self.assertEqual(info["dtype"], np.uint8)
        self.assertAlmostEqual(info["mean"], 121.3680261682581)
        self.assertAlmostEqual(info["std"], 91.194048489528782)
        self.assertEqual(info["min"], 0)
        self.assertAlmostEqual(info["3rd quartile"], 191.0)
        self.assertEqual(info["max"], 255)
        self.assertEqual(info["hash"], "265ea068")

    def test_info__minimal(self):
        info = dito.info(self.image, minimal=True)
        self.assertEqual(len(info.keys()), 2)
        self.assertEqual(info["shape"], (576, 768, 3))
        self.assertEqual(info["dtype"], np.uint8)

    def test_info__raise_on_extended_and_minimal(self):
        self.assertRaises(ValueError, lambda: dito.info(self.image, extended=True, minimal=True))

    def test_info__raise_on_non_image(self):
        self.assertRaises(ValueError, lambda: dito.info(image=1))

    def test_info__array_with_zero_axis_length(self):
        image = np.zeros(shape=(64, 32, 0), dtype=np.uint8)
        info = dito.info(image, extended=True)

        self.assertEqual(info["size"], "0 bytes")
        self.assertEqual(info["shape"], image.shape)
        self.assertEqual(info["dtype"], image.dtype)

        for (key, value) in info.items():
            if key not in ("size", "shape", "dtype", "hash"):
                self.assertTrue(np.isnan(value))


class insert_Tests(TestCase):
    def setUp(self):
        self.target_image = dito.pm5544()
        self.source_image = dito.random_image(size=dito.size(image=self.target_image))
        self.source_mask = dito.convert(image=dito.random_image(size=dito.size(image=self.target_image), color=False), dtype=np.float32)

    def test_insert_raise_on_int(self):
        self.assertRaises(
            ValueError,
            lambda: dito.insert(
                target_image=self.target_image,
                source_image=self.source_image,
                position=(0, 0),
                anchor="lt",
                source_mask=1,
            ),
        )

    def test_insert_full_replace_on_None(self):
        result_image = dito.insert(
            target_image=self.target_image,
            source_image=self.source_image,
            position=(0, 0),
            anchor="lt",
            source_mask=None,
        )
        self.assertEqualImages(result_image, self.source_image)

    def test_insert_full_replace_on_1(self):
        result_image = dito.insert(
            target_image=self.target_image,
            source_image=self.source_image,
            position=(0, 0),
            anchor="lt",
            source_mask=1.0,
        )
        self.assertEqualImages(result_image, self.source_image)

    def test_insert_full_replace_on_1_mask(self):
        result_image = dito.insert(
            target_image=self.target_image,
            source_image=self.source_image,
            position=(0, 0),
            anchor="lt",
            source_mask=np.ones(shape=self.source_image.shape[:2], dtype=np.float32),
        )
        self.assertEqualImages(result_image, self.source_image)

    def test_insert_full_retain_on_0(self):
        result_image = dito.insert(
            target_image=self.target_image,
            source_image=self.source_image,
            position=(0, 0),
            anchor="lt",
            source_mask=0.0,
        )
        self.assertEqualImages(result_image, self.target_image)

    def test_insert_full_retain_on_0_mask(self):
        result_image = dito.insert(
            target_image=self.target_image,
            source_image=self.source_image,
            position=(0, 0),
            anchor="lt",
            source_mask=np.zeros(shape=self.source_image.shape[:2], dtype=np.float32),
        )
        self.assertEqualImages(result_image, self.target_image)

    def test_insert_identical_lt_position_float_int(self):
        result_image_1 = dito.insert(
            target_image=self.target_image,
            source_image=self.source_image,
            position=(0, 0),
            anchor="lt",
            source_mask=None,
        )
        result_image_2 = dito.insert(
            target_image=self.target_image,
            source_image=self.source_image,
            position=(0.0, 0.0),
            anchor="lt",
            source_mask=None,
        )
        self.assertEqualImages(result_image_1, result_image_2)

    def test_insert_identical_rb_position_float_int(self):
        result_image_1 = dito.insert(
            target_image=self.target_image,
            source_image=self.source_image,
            position=(self.target_image.shape[1], self.target_image.shape[0]),
            anchor="lt",
            source_mask=None,
        )
        result_image_2 = dito.insert(
            target_image=self.target_image,
            source_image=self.source_image,
            position=(1.0, 1.0),
            anchor="lt",
            source_mask=None,
        )
        self.assertEqualImages(result_image_1, result_image_2)

    def test_insert_quadrants(self):
        target_size = dito.size(image=self.target_image)
        source_size = (target_size[0] // 2, target_size[1] // 2)

        source_image_1 = dito.random_image(size=source_size)
        source_image_2 = dito.random_image(size=source_size)
        source_image_3 = dito.random_image(size=source_size)
        source_image_4 = dito.random_image(size=source_size)

        result_image = self.target_image.copy()

        result_image = dito.insert(
            target_image=result_image,
            source_image=source_image_1,
            position=(0.0, 0.0),
            anchor="lt",
            source_mask=None,
        )
        result_image = dito.insert(
            target_image=result_image,
            source_image=source_image_2,
            position=(1.0, 0.0),
            anchor="rt",
            source_mask=None,
        )
        result_image = dito.insert(
            target_image=result_image,
            source_image=source_image_3,
            position=(0.0, 1.0),
            anchor="lb",
            source_mask=None,
        )
        result_image = dito.insert(
            target_image=result_image,
            source_image=source_image_4,
            position=(1.0, 1.0),
            anchor="rb",
            source_mask=None,
        )

        self.assertEqualImages(result_image[:source_size[1], :source_size[0], ...], source_image_1)
        self.assertEqualImages(result_image[:source_size[1], source_size[0]:, ...], source_image_2)
        self.assertEqualImages(result_image[source_size[1]:, :source_size[0]:, ...], source_image_3)
        self.assertEqualImages(result_image[source_size[1]:, source_size[0]:, ...], source_image_4)

    def test_insert_inputs_unchanged(self):
        target_image_copy = self.target_image.copy()
        source_image_copy = self.source_image.copy()
        source_mask_copy = self.source_mask.copy()

        _ = dito.insert(
            target_image=self.target_image,
            source_image=self.source_image,
            position=(0, 0),
            anchor="lt",
            source_mask=self.source_mask,
        )
        self.assertEqualImages(self.target_image, target_image_copy)
        self.assertEqualImages(self.source_image, source_image_copy)
        self.assertEqualImages(self.source_mask, source_mask_copy)


class invert_Tests(TestCase):
    def setUp(self):
        self.image = dito.pm5544()

    def test_invert_twice_identical(self):
        image_inverted = dito.invert(image=self.image)
        image_inverted_inverted = dito.invert(image=image_inverted)
        self.assertEqualImages(self.image, image_inverted_inverted)

    def test_invert_int_raise(self):
        image_int16 = dito.convert(image=self.image, dtype=np.int16)
        self.assertRaises(ValueError, lambda: dito.invert(image=image_int16))

    def test_invert_uint8(self):
        image_inverted = dito.invert(image=self.image)
        self.assertEqualImages(image_inverted, 255 - self.image)

    def test_invert_float32(self):
        image_float = dito.convert(image=self.image, dtype=np.float32)
        image_float_inverted = dito.invert(image=image_float)
        self.assertEqualImages(image_float_inverted, 1.0 - image_float)

    def test_invert_float64(self):
        image_float = dito.convert(image=self.image, dtype=np.float64)
        image_float_inverted = dito.invert(image=image_float)
        self.assertEqualImages(image_float_inverted, 1.0 - image_float)

    def test_invert_bool(self):
        image_bool = (self.image > 127)
        image_bool_inverted = dito.invert(image=image_bool)
        self.assertEqualImages(image_bool_inverted, np.logical_not(image_bool))


class is_color_Tests(TestCase):
    def setUp(self):
        self.image = dito.pm5544()

    def test_is_color_of_color_image(self):
        self.assertTrue(dito.is_color(self.image))

    def test_is_color_of_gray_image(self):
        self.assertFalse(dito.is_color(self.image[:, :, 0]))

    def test_is_color_of_gray_image_with_color_channel(self):
        self.assertFalse(dito.is_color(self.image[:, :, 0:1]))

    def test_is_color_of_image_with_two_channels(self):
        self.assertFalse(dito.is_color(self.image[:, :, 0:2]))


class is_gray_Tests(TestCase):
    def setUp(self):
        self.image = dito.pm5544()

    def test_is_gray_of_color_image(self):
        self.assertFalse(dito.is_gray(self.image))

    def test_is_gray_of_gray_image(self):
        self.assertTrue(dito.is_gray(self.image[:, :, 0]))

    def test_is_gray_of_gray_image_with_color_channel(self):
        self.assertTrue(dito.is_gray(self.image[:, :, 0:1]))

    def test_is_gray_of_image_with_two_channels(self):
        self.assertFalse(dito.is_gray(self.image[:, :, 0:2]))


class load_Tests(TempDirTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image_filename = os.path.join(dito.RESOURCES_FILENAMES["image:PM5544"])
        self.shape = (576, 768, 3)

    def test_load_default(self):
        image = dito.load(filename=self.image_filename)
        self.assertNumpyShape(image, self.shape)
        self.assertAlmostEqual(np.mean(image), 121.3680261682581)

    def test_load_grayscale(self):
        image = dito.load(filename=self.image_filename, color=False)
        self.assertNumpyShape(image, self.shape[:2])

    def test_load_and_decode_equal(self):
        image_load = dito.load(filename=self.image_filename)
        with open(self.image_filename, "rb") as f:
            image_decode = dito.decode(b=f.read())
        self.assertNumpyShape(image_load, self.shape)
        self.assertNumpyShape(image_decode, self.shape)
        self.assertTrue(np.all(image_load == image_decode))

    def test_load_str_and_pathlib_equal(self):
        image_str = dito.load(filename=str(self.image_filename))
        image_pathlib = dito.load(filename=pathlib.Path(self.image_filename))
        self.assertEqualImages(image_str, image_pathlib)

    def test_load_czi_no_keep_singleton_dimensions(self):
        image = dito.pm5544()
        image_path = pathlib.Path(self.temp_dir.name).joinpath("image.czi")
        dito.save(image_path, image[np.newaxis, np.newaxis, ...], czi_kwargs={"extra_dim_names": "TZ"})

        image_loaded = dito.load(image_path, czi_kwargs={"keep_singleton_dimensions": False, "keep_all_dimensions": False})
        self.assertEqual(image_loaded.shape, (576, 768, 3))

    def test_load_czi_keep_singleton_dimensions(self):
        image = dito.pm5544()
        image_path = pathlib.Path(self.temp_dir.name).joinpath("image.czi")
        dito.save(image_path, image[np.newaxis, np.newaxis, ...], czi_kwargs={"extra_dim_names": "TZ"})

        # according to pylibCZIrw, the dimensions T, Z, and C are always present, even if not available in the .czi file
        # so instead of the expected (1, 1, 576, 768, 3), we actually get (1, 1, 1, 576, 768, 3)
        image_loaded = dito.load(image_path, czi_kwargs={"keep_singleton_dimensions": True, "keep_all_dimensions": False})
        self.assertEqual(image_loaded.shape, (1, 1, 1, 576, 768, 3))

    def test_load_czi_keep_all_dimensions(self):
        image = dito.pm5544()
        image_path = pathlib.Path(self.temp_dir.name).joinpath("image.czi")
        dito.save(image_path, image[np.newaxis, np.newaxis, ...], czi_kwargs={"extra_dim_names": "TZ"})

        image_loaded = dito.load(image_path, czi_kwargs={"keep_singleton_dimensions": True, "keep_all_dimensions": True})
        self.assertEqual(image_loaded.shape, (1, 1, 1, 1, 1, 1, 1, 1, 576, 768, 3))


class mkdir_Tests(TempDirTestCase):
    def test_mkdir_str(self):
        dirname = os.path.join(str(self.temp_dir.name), "dir_str")
        self.assertFalse(os.path.exists(dirname))
        dito.mkdir(dirname=dirname)
        self.assertTrue(os.path.exists(dirname))

    def test_mkdir_pathlib(self):
        dir_path = pathlib.Path(self.temp_dir.name).joinpath("dir_pathlib")
        self.assertFalse(dir_path.exists())
        dito.mkdir(dirname=dir_path)
        self.assertTrue(dir_path.exists())

    def test_mkdir_existing(self):
        dir_path = pathlib.Path(self.temp_dir.name).joinpath("dir_pathlib")
        self.assertFalse(dir_path.exists())
        dito.mkdir(dirname=dir_path)
        self.assertTrue(dir_path.exists())
        dito.mkdir(dirname=dir_path)


class MultiShow_Tests(TempDirTestCase):
    def get_random_image(self):
        return dito.random_image(size=(256, 128))

    def test_MultiShow_image_count(self):
        mshow = dito.MultiShow()
        self.assertEqual(len(mshow.images), 0)

        mshow.show(image=self.get_random_image(), hide=True)
        self.assertEqual(len(mshow.images), 1)

        mshow.show(image=self.get_random_image(), hide=True)
        self.assertEqual(len(mshow.images), 2)

        mshow.show(image=self.get_random_image(), keep=False, hide=True)
        self.assertEqual(len(mshow.images), 2)

    def test_MultiShow_identical(self):
        mshow = dito.MultiShow()

        image1 = self.get_random_image()
        mshow.show(image=image1, scale=1.0, hide=True)

        image2 = self.get_random_image()
        mshow.show(image=image2, scale=1.0, hide=True)

        image3 = self.get_random_image()
        mshow.show(image=image3, scale=1.0, keep=False, hide=True)

        image4 = self.get_random_image()
        mshow.show(image=image4, scale=1.0, hide=True)

        self.assertEqualImages(image1, mshow.images[0])
        self.assertEqualImages(image2, mshow.images[1])
        self.assertEqualImages(image4, mshow.images[2])

    def test_MultiShow_shape(self):
        mshow = dito.MultiShow()

        image = dito.as_gray(self.get_random_image())
        mshow.show(image=image, scale=2.0, colormap="jet", hide=True)
        self.assertEqual((image.shape[0] * 2, image.shape[1] * 2, 3), mshow.images[0].shape)

    def test_MultiShow_save(self):
        mshow = dito.MultiShow(save_dir=self.temp_dir.name)

        image_count = 3
        images = []
        for n_image in range(image_count):
            image = self.get_random_image()
            images.append(image.copy())
            mshow.show(image=image, scale=1.0, hide=True)

        mshow.save_all(verbose=False)
        for n_image in range(image_count):
            filename = os.path.join(mshow.save_dir, "{:>08d}.png".format(n_image + 1))
            image_loaded = dito.load(filename=filename)
            self.assertEqualImages(image_loaded, images[n_image])


class nms_Tests(TestCase):
    @staticmethod
    def get_example_data():
        image = np.zeros(shape=(100, 200), dtype=np.float32)
        peak_xys = [
            [0, 0],
            [20, 20],
            [30, 20],
            [100, 50],
            [150, 50],
            [199, 99],
        ]

        for (n_peak, (peak_x, peak_y)) in enumerate(peak_xys):
            image[peak_y, peak_x] = 1.0 - min(0.9, n_peak * 0.1)

        image = dito.gaussian_blur(image, sigma=1.0)
        image = image / np.max(image)

        return (image, peak_xys)

    def test_input_image_unaltered(self):
        image = dito.test_image_segments()
        image = dito.as_gray(image)

        image_copy = image.copy()
        dito.nms(image=image, peak_radius=2)
        self.assertEqualImages(image, image_copy)

    def test_full_example(self):
        (image, peak_xys) = self.get_example_data()

        for dtype in (np.float32, np.uint8, np.uint16):
            image_converted = dito.convert(image, dtype=dtype)
            peaks_nms = dito.nms(image=image_converted, peak_radius=2, max_peak_count=1000, rel_max_value=0.1)
            self.assertEqual(len(peak_xys), len(peaks_nms))

            for n_peak in range(len(peak_xys)):
                self.assertEqual(tuple(peak_xys[n_peak]), peaks_nms[n_peak]["peak_xy"])

    def test_zero_image(self):
        image = np.zeros(shape=(100, 200), dtype=np.float32)

        for dtype in (np.float32, np.uint8, np.uint16):
            image_converted = dito.convert(image, dtype=dtype)
            peaks_nms = dito.nms(image=image_converted, peak_radius=2, max_peak_count=1000, rel_max_value=0.1)
            self.assertEqual(len(peaks_nms), 0)

    def test_invalid_image_shape(self):
        image = dito.pm5544()
        self.assertRaises(ValueError, lambda: dito.nms(image=image, peak_radius=2))

        image.shape = (1,) + image.shape
        self.assertRaises(ValueError, lambda: dito.nms(image=image, peak_radius=2))

        image = image[0, 0, :, 0]
        self.assertRaises(ValueError, lambda: dito.nms(image=image, peak_radius=2))

    def test_invalid_peak_radius(self):
        (image, _) = self.get_example_data()
        self.assertRaises(ValueError, lambda: dito.nms(image=image, peak_radius=-1))
        self.assertRaises(ValueError, lambda: dito.nms(image=image, peak_radius=2.0))

    def test_invalid_max_peak_count(self):
        (image, _) = self.get_example_data()
        self.assertRaises(ValueError, lambda: dito.nms(image=image, peak_radius=2, max_peak_count=0))
        self.assertRaises(ValueError, lambda: dito.nms(image=image, peak_radius=2, max_peak_count=-1))
        self.assertRaises(ValueError, lambda: dito.nms(image=image, peak_radius=2, max_peak_count=2.0))

    def test_invalid_rel_max_value(self):
        (image, _) = self.get_example_data()
        self.assertRaises(ValueError, lambda: dito.nms(image=image, peak_radius=2, rel_max_value=1))
        self.assertRaises(ValueError, lambda: dito.nms(image=image, peak_radius=2, rel_max_value=-1.0))
        self.assertRaises(ValueError, lambda: dito.nms(image=image, peak_radius=2, rel_max_value=2.0))


class normalize_Tests(TestCase):
    def run_in_out_test(self, image_in, image_out, **kwargs):
        image_normalized = dito.normalize(image=image_in, **kwargs)
        self.assertEqualImages(image_normalized, image_out)
    
    def test_normalize_none_uint8(self):
        self.run_in_out_test(
            image_in=np.array([[0, 1, 2]], dtype=np.uint8),
            image_out=np.array([[0, 1, 2]], dtype=np.uint8),
            mode="none",
        )
    
    def test_normalize_minmax_uint8(self):
        self.run_in_out_test(
            image_in=np.array([[0, 1, 2]], dtype=np.uint8),
            image_out=np.array([[0, 127, 255]], dtype=np.uint8),
            mode="minmax",
        )
    
    def test_normalize_minmax_int8(self):
        self.run_in_out_test(
            image_in=np.array([[0, 1, 2]], dtype=np.int8),
            image_out=np.array([[-128, 0, 127]], dtype=np.int8),
            mode="minmax",
        )
    
    def test_normalize_minmax_float32(self):
        self.run_in_out_test(
            image_in=np.array([[-1.0, 0.0, 1.0]], dtype=np.float32),
            image_out=np.array([[0.0, 0.5, 1.0]], dtype=np.float32),
            mode="minmax",
        )
    
    def test_normalize_zminmax_float32(self):
        self.run_in_out_test(
            image_in=np.array([[-1.0, 0.0, 1.0, 2.0]], dtype=np.float32),
            image_out=np.array([[0.25, 0.5, 0.75, 1.0]], dtype=np.float32),
            mode="zminmax",
        )
    
    def test_normalize_percentile_uint8_q(self):
        self.run_in_out_test(
            image_in=np.array([[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]], dtype=np.uint8),
            image_out=np.array([[0, 0, 31, 63, 95, 127, 159, 191, 223, 255, 255]], dtype=np.uint8),
            mode="percentile",
            q=10.0,
        )
    
    def test_normalize_percentile_uint8_p(self):
        self.run_in_out_test(
            image_in=np.array([[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]], dtype=np.uint8),
            image_out=np.array([[0, 0, 31, 63, 95, 127, 159, 191, 223, 255, 255]], dtype=np.uint8),
            mode="percentile",
            p=10.0,
        )
    
    def test_normalize_raise_invalid_mode(self):
        image = np.array([[0, 1, 2]], dtype=np.uint8)
        self.assertRaises(ValueError, lambda: dito.normalize(image=image, mode="__NON-EXISTING-MODE__"))


class now_str_Tests(TestCase):
    def test_now_str_length(self):
        cases = [
            {"kwargs": {"mode": "compact",  "date": True, "time": False, "microtime": False}, "expected_length": 8},
            {"kwargs": {"mode": "readable", "date": True, "time": False, "microtime": False}, "expected_length": 10},
            {"kwargs": {"mode": "print",    "date": True, "time": False, "microtime": False}, "expected_length": 10},
            {"kwargs": {"mode": "compact",  "date": True, "time": True,  "microtime": False}, "expected_length": 15},
            {"kwargs": {"mode": "readable", "date": True, "time": True,  "microtime": False}, "expected_length": 20},
            {"kwargs": {"mode": "print",    "date": True, "time": True,  "microtime": False}, "expected_length": 19},
        ]
        for case in cases:
            # assert equal length
            result = dito.now_str(**case["kwargs"])
            self.assertIsInstance(result, str)
            self.assertEqual(len(result), case["expected_length"])

            # assert greater length with microtime
            case["kwargs"]["microtime"] = True
            result_microtime = dito.now_str(**case["kwargs"])
            self.assertIsInstance(result_microtime, str)
            self.assertGreater(len(result_microtime), case["expected_length"])


class parse_shape_Tests(TestCase):
    def setUp(self):
        self.shape4 = (8, 100, 200, 3)

    def test_parse_shape_bad_inputs(self):
        cases = [
            (None, "b h w c"),
            ((8, 100, 200, 3), None),
            ("b h w c", "b h w c"),
            ((8, 100, 200, 3), 123),
            ((8, 100, 200, 3), (8, 100, 200, 3)),
            (123, "b h w c"),
            ([], "b h w c"),
        ]
        for (shape, shape_def) in cases:
            with self.assertRaises(TypeError):
                dito.parse_shape(shape, shape_def)

    def test_parse_shape_named_inputs(self):
        shape_def = "b h w c"
        results = [
            dito.parse_shape(self.shape4, shape_def),
            dito.parse_shape(self.shape4, shape_def=shape_def),
            dito.parse_shape(image_or_shape=self.shape4, shape_def=shape_def),
            dito.parse_shape(shape_def=shape_def, image_or_shape=self.shape4),
        ]
        for result in results[1:]:
            self.assertEqual(result, results[0])

    def test_parse_shape_ndarray_or_shape(self):
        image = dito.pm5544()
        cases = [
            (image, "h w c", {"h": 576, "w": 768, "c": 3}),
            (image.shape, "h w c", {"h": 576, "w": 768, "c": 3}),
            (image[:, :, 0], "h w", {"h": 576, "w": 768}),
            (image.shape[:2], "h w", {"h": 576, "w": 768}),
        ]
        for (image_or_shape, shape_def, expected_result) in cases:
            result = dito.parse_shape(image_or_shape, shape_def)
            self.assertEqual(result, expected_result)

    def test_parse_shape_values_only(self):
        cases = [
            "8 100 200 3",
            "8  100  200  3",
            "  8  100  200  3  ",
        ]
        for shape_def in cases:
            result = dito.parse_shape(self.shape4, shape_def)
            self.assertEqual(result, {})

    def test_parse_shape_named_axes(self):
        cases = [
            ("b h w c", {"b": 8, "h": 100, "w": 200, "c": 3}),
            ("b  h  w  c", {"b": 8, "h": 100, "w": 200, "c": 3}),
            ("  b  h  w  c  ", {"b": 8, "h": 100, "w": 200, "c": 3}),
            ("batch height width channel", {"batch": 8, "height": 100, "width": 200, "channel": 3}),
        ]
        for (shape_def, expected_result) in cases:
            result = dito.parse_shape(self.shape4, shape_def)
            self.assertEqual(result, expected_result)

    def test_parse_shape_named_axis_with_single_value(self):
        shape = (100, 200, 3)
        result = dito.parse_shape(shape, "h w c=3")
        self.assertEqual(result, {"h": 100, "w": 200, "c": 3})

    def test_parse_shape_named_axis_with_multiple_values(self):
        cases = [
            "b h w c=1|3",
            "b h w c=1|3|3",
            "b h w c=1|3|1000",
        ]
        for shape_def in cases:
            result = dito.parse_shape(self.shape4, shape_def)
            self.assertEqual(result, {"b": 8, "h": 100, "w": 200, "c": 3})

    def test_parse_shape_placeholder_names(self):
        cases = [
            ("_ _ _ _", {}),
            ("_ _ _ 3", {}),
            ("_ _ 200 3", {}),
            ("_ 100 200 3", {}),
            ("8 100 200 _", {}),
            ("8 100 _ _", {}),
            ("8 _ _ _", {}),
            ("8 _ 200 3", {}),
            ("8 100 _ 3", {}),
        ]
        for (shape_def, expected_result) in cases:
            result = dito.parse_shape(self.shape4, shape_def)
            self.assertEqual(result, expected_result)

    def test_parse_shape_with_nonempty_ellipsis(self):
        shape = (8, 100, 200, 3)
        cases = [
            ("... c=3", {"c": 3}),
            ("... c=1|3", {"c": 3}),
            ("b ... c=3", {"b": 8, "c": 3}),
            ("b=8 ... c=3", {"b": 8, "c": 3}),
            ("b=4|8 ... c=1|3", {"b": 8, "c": 3}),
            ("b ...", {"b": 8}),
            ("b h ... c", {"b": 8, "h": 100, "c": 3}),
            ("_ ... c", {"c": 3}),
        ]
        for (shape_def, expected_result) in cases:
            result = dito.parse_shape(shape, shape_def)
            self.assertEqual(result, expected_result)

    def test_parse_shape_with_empty_ellipsis(self):
        shape = (100, 200, 3)
        shape_defs = [
            "... h w c",
            "... h w c=3",
            "... h w c=1|3",
            "... h=100 w=200 c=1|3",
            "h ... w c=3",
            "h w ... c=3",
            "h w c=3 ...",
        ]
        for shape_def in shape_defs:
            result = dito.parse_shape(shape, shape_def)
            self.assertEqual(result, {"h": 100, "w": 200, "c": 3})

    def test_parse_shape_empty(self):
        shape = tuple()
        self.assertEqual(dito.parse_shape(shape, ""), {})

    def test_parse_shape_singleton(self):
        shape = (8,)
        self.assertEqual(dito.parse_shape(shape, "_"), {})
        self.assertEqual(dito.parse_shape(shape, "8"), {})
        self.assertEqual(dito.parse_shape(shape, "_=8"), {})
        self.assertEqual(dito.parse_shape(shape, "x=8"), {"x": 8})
        self.assertEqual(dito.parse_shape(shape, "x=1|2|4|8|16"), {"x": 8})

    def test_parse_shape_raise_definition_error(self):
        cases = [
            "b h w .",          # invalid character in name
            "b h w *",          # invalid character in name
            "b h w #",          # invalid character in name
            "b h h c",          # duplicate names
            "b ... h ... c",    # multiple ellipses
            "b h w =",          # neither name nor value
            "b h w c=",         # missing value
            "b h w c=|",        # missing value
            "b h w c=1|",       # missing value
            "b h w c=1||3",     # missing value
            "b h w c=1.0",      # invalid value
            "b h w c=a",        # invalid value
            "b h w c=0xff",     # invalid value
        ]
        for shape_def in cases:
            with self.assertRaises(dito.ParseShapeDefinitionError):
                dito.parse_shape(self.shape4, shape_def)

    def test_parse_shape_raise_mismatch_error(self):
        cases = [
            "",
            "3",
            "200 3",
            "100 200 3",
            "8 100 200 4",
            "8 100 200 3 1",
        ]
        for shape_def in cases:
            with self.assertRaises(dito.ParseShapeMismatchError):
                dito.parse_shape(self.shape4, shape_def)


class otsu_Tests(TestCase):
    def test_otsu_raise(self):
        image = dito.pm5544()
        self.assertRaises(ValueError, lambda: dito.otsu(image=image))

    def test_otsu_return(self):
        image = dito.pm5544()
        image_gray = dito.as_gray(image)
        result = dito.otsu(image=image_gray)
        self.assertIsInstance(result, tuple)
        self.assertTrue(len(result) == 2)
        self.assertIsInstance(result[0], float)
        self.assertIsInstance(result[1], np.ndarray)


class PaddedImageIndexer_Tests(TestCase):
    def setUp(self):
        self.image = dito.data.pm5544()
        self.indexer = dito.core.PaddedImageIndexer(self.image)

    def test_PaddedImageIndexer_no_pad(self):
        results = [
            self.indexer[:, :, :],
            self.indexer[:576, :768, :3],
            self.indexer[0:576, 0:768, 0:3],
            self.indexer[0:576:1, 0:768:1, 0:3:1],
        ]
        for result in results:
            self.assertEqualImages(result, self.image)

    def test_PaddedImageIndexer_ellipses(self):
        results = [
            self.indexer[...],
            self.indexer[:, ...],
            self.indexer[:, :, ...],
            self.indexer[:, :, :, ...],
        ]
        for result in results:
            self.assertEqualImages(result, self.image)

    def test_PaddedImageIndexer_less_axes(self):
        results = [
            self.indexer[tuple()],
            self.indexer[:],
            self.indexer[:, :],
        ]
        for result in results:
            self.assertEqualImages(result, self.image)

    def test_PaddedImageIndexer_full_out_of_bounds_black_image(self):
        result = self.indexer[-100:-50, :, :]
        self.assertNumpyShape(result, (50,) + self.image.shape[1:])
        self.assertEqualImages(result, np.zeros(shape=(50,) + self.image.shape[1:], dtype=self.image.dtype))

    def test_PaddedImageIndexer_resulting_axis_size(self):
        for start in (-100, -10, -1, 0, 1, 10, 100):
            for delta in (0, 1, 10, self.image.shape[0]):
                stop = start + delta
                result = self.indexer[start:stop, :, :]
                self.assertNumpyShape(result, (max(0, stop - start),) + self.image.shape[1:])

    def test_PaddedImageIndexer_large_step(self):
        for start in (None, 0, 1, 100):
            for step in (1, 10, 1000):
                result = self.indexer[slice(start, None, step), :, :]
                self.assertEqualImages(result, self.image[slice(start, None, step), :, :])

    def test_PaddedImageIndexer_mirror_pad(self):
        mirror_indexer = dito.core.PaddedImageIndexer(
            image=self.image,
            pad_kwargs=dict(
                mode="reflect",
            ),
        )
        result = mirror_indexer[-288:288, :, :]
        self.assertEqualImages(
            result,
            dito.visual.stack([
                [self.image[:289, :, :][::-1, :, :]],
                [self.image[1:288, :, :]]],
            ),
        )

    def test_PaddedImageIndexer_raise_on_negative_step(self):
        self.assertRaises(ValueError, lambda: self.indexer[::-1, :, :])
        self.assertRaises(ValueError, lambda: self.indexer[slice(0, 10, -1), :, :])
        self.assertRaises(ValueError, lambda: self.indexer[slice(10, None, -1), :, :])

    def test_PaddedImageIndexer_raise_on_start_larger_than_stop(self):
        self.assertRaises(ValueError, lambda: self.indexer[100:10, :, :])
        self.assertRaises(ValueError, lambda: self.indexer[slice(1000, None), :, :])


class otsu_theta_Tests(TestCase):
    def test_otsu_theta(self):
        image = dito.pm5544()
        image_gray = dito.as_gray(image)
        theta = dito.otsu_theta(image=image_gray)
        self.assertIsInstance(theta, float)
        self.assertAlmostEqual(theta, 89.0)


class pinfo_Tests(TempDirTestCase):
    def test_pinfo_file(self):
        image = dito.pm5544()
        info_filename = os.path.join(self.temp_dir.name, "pinfo.txt")
        with open(info_filename, "w") as f:
            dito.pinfo(image=image, file_=f)

        self.assertTrue(os.path.exists(info_filename))
        with open(info_filename, "r") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 5)


class random_image_Tests(TestCase):
    def test_random_image_color(self):
        image_size = (256, 128)
        image = dito.random_image(size=image_size, color=True)
        self.assertIsImage(image)
        self.assertNumpyShape(image, (image_size[1], image_size[0], 3))

    def test_random_image_gray(self):
        image_size = (256, 128)
        image = dito.random_image(size=image_size, color=False)
        self.assertIsImage(image)
        self.assertNumpyShape(image, (image_size[1], image_size[0]))


class resize_Tests(TestCase):
    def test_resize_scale(self):
        image = dito.pm5544()
        image_resized = dito.resize(image, 0.5)
        self.assertEqual(image_resized.shape, (288, 384, 3))

    def test_resize_size(self):
        image = dito.pm5544()
        image_resized = dito.resize(image, (384, 288))
        self.assertEqual(image_resized.shape, (288, 384, 3))

    def test_resize_bool(self):
        image = dito.pm5544()
        image_bool = image > 127
        image_resized = dito.resize(image_bool, 0.5)
        self.assertEqual(image_resized.shape, (288, 384, 3))


class rotate_Tests(TestCase):
    def setUp(self):
        self.image = dito.pm5544()

    def test_rotate_180_input_unchanged(self):
        image_copy = self.image.copy()
        dito.rotate_180(image=self.image)
        self.assertEqualImages(self.image, image_copy)

    def test_rotate_90_dtype_shape(self):
        image_rotated = dito.rotate_90(image=self.image)
        self.assertEqual(self.image.dtype, image_rotated.dtype)
        self.assertNumpyShape(image_rotated, self.image.shape[1::-1] + self.image.shape[2:])

    def test_rotate_180_gray(self):
        image_rotated = dito.rotate_180(image=self.image)
        image_rotated_gray = dito.as_gray(image=image_rotated)

        image_gray = dito.as_gray(image=self.image)
        image_gray_rotated = dito.rotate_180(image=image_gray)

        self.assertEqualImages(image_rotated_gray, image_gray_rotated)

    def test_rotate_90_4_times(self):
        image_rotated = self.image.copy()
        for n_rotation in range(4):
            image_rotated = dito.rotate_90(image=image_rotated)
        self.assertEqualImages(self.image, image_rotated)

    def test_rotate_90_270(self):
        image_rotated = dito.rotate_90(image=self.image)
        image_rotated_2 = dito.rotate_270(image=image_rotated)
        self.assertEqualImages(self.image, image_rotated_2)

    def test_rotate_all_to_180(self):
        image_rotated_90_2x = dito.rotate_90(image=dito.rotate_90(image=self.image))
        image_rotated_270_2x = dito.rotate_270(image=dito.rotate_270(image=self.image))
        image_rotated_180 = dito.rotate_180(image=self.image)
        self.assertEqualImages(image_rotated_90_2x, image_rotated_180)
        self.assertEqualImages(image_rotated_270_2x, image_rotated_180)


class save_Tests(TempDirTestCase):
    def _test_save_load(self, extension, basename="image", save_kwargs=None):
        image = dito.pm5544()

        if save_kwargs is None:
            save_kwargs = {}

        filename_str = str(os.path.join(self.temp_dir.name, "dir_str", "{}_str.{}".format(basename, extension)))
        dito.save(filename=filename_str, image=image, **save_kwargs)
        image_str_loaded = dito.load(filename=filename_str)

        filename_pathlib = pathlib.Path(os.path.join(self.temp_dir.name, "dir_pathlib", "{}_pathlib.{}".format(basename, extension)))
        dito.save(filename=filename_pathlib, image=image)
        image_pathlib_loaded = dito.load(filename=filename_pathlib)

        if extension == "jpg":
            # JPG compression is lossy
            self.assertEqualImageContainers(image, image_str_loaded)
            self.assertEqualImageContainers(image, image_pathlib_loaded)
        else:
            # all other formats should be lossless
            self.assertEqualImages(image, image_str_loaded)
            self.assertEqualImages(image, image_pathlib_loaded)

    def test_save_load_jpg(self):
        self._test_save_load(extension="jpg")

    def test_save_load_png(self):
        self._test_save_load(extension="png")

    def test_save_imwrite_params(self):
        self._test_save_load(extension="png", save_kwargs=dict(imwrite_params=None))
        self._test_save_load(extension="png", save_kwargs=dict(imwrite_params=tuple()))
        self._test_save_load(extension="png", save_kwargs=dict(imwrite_params=(cv2.IMWRITE_PNG_STRATEGY, cv2.IMWRITE_PNG_STRATEGY_RLE)))
        self._test_save_load(extension="png", save_kwargs=dict(imwrite_params=(cv2.IMWRITE_PNG_STRATEGY, cv2.IMWRITE_PNG_STRATEGY_HUFFMAN_ONLY)))

    def test_save_imwrite_params_jpg_size(self):
        image = dito.pm5544()

        filename_q90 = str(os.path.join(self.temp_dir.name, "jpg_size_q90.jpg"))
        filename_q50 = str(os.path.join(self.temp_dir.name, "jpg_size_q50.jpg"))

        dito.save(filename=filename_q90, image=image, imwrite_params=(cv2.IMWRITE_JPEG_QUALITY, 90))
        dito.save(filename=filename_q50, image=image, imwrite_params=(cv2.IMWRITE_JPEG_QUALITY, 50))

        self.assertGreater(os.stat(filename_q90).st_size, os.stat(filename_q50).st_size)

    def test_save_load_npy(self):
        self._test_save_load(extension="npy")

    def test_save_load_npz(self):
        self._test_save_load(extension="npz")

    def test_save_load_czi(self):
        self._test_save_load(extension="czi")

    def test_save_load_nonascii(self):
        # under Windows, OpenCV silently fails when trying to save an image
        # with a non-ASCII filename - dito.save fixes that
        self._test_save_load(extension="png", basename="image_äöü")
        self._test_save_load(extension="npy", basename="image_äöü")

    def test_save_czi_raise_on_invalid_shape(self):
        (X, Y) = (128, 64)
        invalid_shapes = [
            tuple(),
            (Y,),
            (Y, X, 2),
            (Y, X, 4),
        ]

        image_path = pathlib.Path(self.temp_dir.name).joinpath("image.czi")

        for invalid_shape in invalid_shapes:
            image = np.zeros(shape=invalid_shape, dtype=np.uint8)
            self.assertRaises(ValueError, lambda: dito.save(image_path, image))

    def test_save_czi_no_raise_on_valid_shape(self):
        (X, Y) = (128, 64)
        shapes = [
            (Y, X),
            (Y, X, 1),
            (Y, X, 3),
        ]

        image_path = pathlib.Path(self.temp_dir.name).joinpath("image.czi")

        for shape in shapes:
            image = np.zeros(shape=shape, dtype=np.uint8)
            dito.save(image_path, image)

    def test_save_czi_no_extra_dims_gray_implicit(self):
        image = dito.pm5544()[:, :, 0]
        image_path = pathlib.Path(self.temp_dir.name).joinpath("image.czi")
        dito.save(image_path, image)
        image_loaded = dito.load(image_path)
        self.assertEqual(image.shape + (1,), image_loaded.shape)
        self.assertEqualImages(image, image_loaded[:, :, 0])

    def test_save_czi_no_extra_dims_gray(self):
        image = dito.pm5544()[:, :, :1]
        image_path = pathlib.Path(self.temp_dir.name).joinpath("image.czi")
        dito.save(image_path, image)
        image_loaded = dito.load(image_path)
        self.assertEqualImages(image, image_loaded)

    def test_save_czi_no_extra_dims_color(self):
        image = dito.pm5544()
        image_path = pathlib.Path(self.temp_dir.name).joinpath("image.czi")
        dito.save(image_path, image)
        image_loaded = dito.load(image_path)
        self.assertEqualImages(image, image_loaded)

    def test_save_czi_raise_on_missing_extra_dim_names(self):
        image_path = pathlib.Path(self.temp_dir.name).joinpath("image.czi")

        # no extra dimension -> should not raise
        image_1 = np.zeros(shape=(64, 128, 3), dtype=np.uint8)
        dito.save(image_path, image_1)

        # extra dimension but no extra_dim_names -> should raise
        image_2 = np.zeros(shape=(2,) + image_1.shape, dtype=np.uint8)
        self.assertRaises(ValueError, lambda: dito.save(image_path, image_2))

    def test_save_czi_extra_dims(self):
        image = np.random.uniform(size=(2, 5, 64, 128, 3))
        image = dito.convert(image, np.uint8)
        image_path = pathlib.Path(self.temp_dir.name).joinpath("image.czi")
        dito.save(image_path, image, czi_kwargs={"extra_dim_names": "TZ"})

        # when loading, the Z dimension comes before the T dimension
        image_loaded = dito.load(image_path)
        self.assertEqual(image_loaded.shape, (5, 2, 64, 128, 3))

        image_transposed = np.transpose(image, (1, 0, 2, 3, 4)).copy()
        self.assertEqualImages(image_transposed, image_loaded, enforce_is_image=False)


class save_tmp_Tests(TestCase):
    def test_save_tmp_reload(self):
        image = dito.pm5544()
        filename = dito.save_tmp(image=image)
        image_loaded = dito.load(filename=filename)
        self.assertEqualImages(image, image_loaded)


class shifted_diff_Tests(DiffTestCase):
    def test_shifted_diff_bool(self):
        result = dito.shifted_diff(image1=self.image1_bool, image2=self.image2_bool)
        expected_result = np.array([[False, True]], dtype=bool)
        self.assertEqualImages(result, expected_result)

    def test_shifted_diff_int8(self):
        result = dito.shifted_diff(image1=self.image1_int8, image2=self.image2_int8)
        expected_result = np.array([[-128, 127]], dtype=np.int8)
        self.assertEqualImages(result, expected_result)

    def test_shifted_diff_uint8(self):
        result = dito.shifted_diff(image1=self.image1_uint8, image2=self.image2_uint8)
        expected_result = np.array([[0, 255]], dtype=np.uint8)
        self.assertEqualImages(result, expected_result)

    def test_shifted_diff_float32(self):
        result = dito.shifted_diff(image1=self.image1_float32, image2=self.image2_float32)
        expected_result = np.array([[0.0, 1.0]], dtype=np.float32)
        self.assertEqualImages(result, expected_result)

    def test_shifted_diff_float64(self):
        result = dito.shifted_diff(image1=self.image1_float64, image2=self.image2_float64)
        expected_result = np.array([[0.0, 1.0]], dtype=np.float64)
        self.assertEqualImages(result, expected_result)


class split_channels_Tests(TestCase):
    def test_split_channels_color_image(self):
        image = dito.pm5544()
        channel_images = dito.split_channels(image=image)
        self.assertEqual(len(channel_images), image.shape[2])
        for n_channel in range(3):
            self.assertEqualImages(image[:, :, n_channel], channel_images[n_channel])

    def test_split_channels_gray_image(self):
        image = dito.as_gray(dito.pm5544())
        channel_images = dito.split_channels(image=image)
        self.assertEqual(len(channel_images), 1)
        self.assertEqualImages(image, channel_images[0])

    def test_split_channels_raise_on_invalid_shape(self):
        image = dito.pm5544()
        image.shape += (1,)
        self.assertRaises(dito.InvalidImageShapeError, lambda: dito.split_channels(image=image))


class stack_Tests(TestCase):
    def test_stack_mixed(self):
        # TODO: create more individual tests
        rows = [
            [
                dito.xslope(height=32, width=256),
                dito.as_color(image=dito.xslope(height=64, width=128)),
            ],
            [
                np.ones(shape=(100, 100), dtype=np.bool_),
            ],
        ]
        image_stacked = dito.stack(rows, padding=8, background_color=127)
        self.assertTrue(image_stacked.dtype == np.uint8)
        self.assertTrue(dito.is_color(image=image_stacked))
        self.assertEqual(image_stacked.shape, (188, 408, 3))
        self.assertEqual(image_stacked[0, 0, 0], 127)
        self.assertEqual(image_stacked[90, 10, 0], 255)

    def test_stack_single_row(self):
        row = [
            dito.xslope(height=32, width=256),
            dito.as_color(image=dito.xslope(height=64, width=128)),
        ]
        image_stacked = dito.stack(images=row)
        image_stacked_2 = dito.stack(images=[row])
        self.assertEqualImages(image_stacked, image_stacked_2)

    def test_stack_raise_on_single_image(self):
        image = dito.xslope(height=32, width=256)
        self.assertRaises(ValueError, lambda: dito.stack(images=image))

    def test_stack_raise_on_non_image(self):
        rows = [[0, 1, 2], [3, 4, 5]]
        self.assertRaises(ValueError, lambda: dito.stack(images=rows))


class stack_channels_Tests(TestCase):
    def setUp(self):
        self.image = dito.dito_test_image_v1()

    def test_row_mode(self):
        stacked_image = dito.stack_channels(image=self.image, mode="row")
        self.assertEqual(len(stacked_image.shape), 2)
        self.assertEqual(stacked_image.shape[0], self.image.shape[0])
        self.assertEqual(stacked_image.shape[1], 3 * self.image.shape[1])
        self.assertEqualImages(stacked_image[:, :self.image.shape[1]], self.image[:, :, 0])

    def test_row_mode(self):
        stacked_image = dito.stack_channels(image=self.image, mode="col")
        self.assertEqual(len(stacked_image.shape), 2)
        self.assertEqual(stacked_image.shape[0], 3 * self.image.shape[0])
        self.assertEqual(stacked_image.shape[1], self.image.shape[1])
        self.assertEqualImages(stacked_image[:self.image.shape[0], :], self.image[:, :, 0])

    def test_auto_mode(self):
        stacked_image = dito.stack_channels(image=self.image, mode="auto")
        self.assertEqual(len(stacked_image.shape), 2)
        self.assertTrue((stacked_image.shape[0] > self.image.shape[0]) or (stacked_image.shape[1] > self.image.shape[1]))
        self.assertEqualImages(stacked_image[:self.image.shape[0], :self.image.shape[1]], self.image[:, :, 0])

    def test_kwargs(self):
        padding = 8
        kwargs = {"padding": padding}

        stacked_image = dito.stack_channels(image=self.image, mode="row", **kwargs)
        self.assertEqual(len(stacked_image.shape), 2)
        self.assertEqual(stacked_image.shape[0], self.image.shape[0] + 2 * padding)
        self.assertEqual(stacked_image.shape[1], 3 * self.image.shape[1] + 4 * padding)
        self.assertEqualImages(stacked_image[padding:(-padding), padding:(self.image.shape[1] + padding)], self.image[:, :, 0])

    def test_gray_image(self):
        image_gray = dito.as_gray(image=self.image)
        stacked_image = dito.stack_channels(image=image_gray)
        self.assertEqualImages(image_gray, stacked_image)


class text_Tests(TestCase):
    def setUp(self):
        self.image = dito.pm5544()
        self.text_kwargs = {
            "font": "source-25",
            "position": (0.5, 0.5),
            "anchor": "cc"
        }

    def test_text_input_unchanged(self):
        image_copy = self.image.copy()
        dito.text(image=self.image, message="Hello World", **self.text_kwargs)
        self.assertEqualImages(self.image, image_copy)

    def test_text_output_different(self):
        text_image = dito.text(image=self.image, message="Hello World", **self.text_kwargs)
        self.assertDifferingImages(self.image, text_image)

    def test_text_background(self):
        text_image = dito.text(image=self.image, message=" ", background_color=(40, 40, 40), **self.text_kwargs)
        self.assertDifferingImages(self.image, text_image)

    def test_text_no_background(self):
        text_image = dito.text(image=self.image, message=" ", background_color=None, **self.text_kwargs)
        self.assertEqualImages(self.image, text_image)

    def test_text_outline(self):
        text_image_background_none = dito.text(image=self.image, message="Hello World", background_color=None, **self.text_kwargs)
        text_image_background_outline = dito.text(image=self.image, message="Hello World", background_color=(40, 40, 40), background_as_outline=True, **self.text_kwargs)
        text_image_background_full = dito.text(image=self.image, message="Hello World", background_color=(40, 40, 40), **self.text_kwargs)
        self.assertDifferingImages(text_image_background_outline, text_image_background_none)
        self.assertDifferingImages(text_image_background_outline, text_image_background_full)

    def test_text_escape_bold(self):
        text_image_regular = dito.text(image=self.image, message="Hello World", **self.text_kwargs)
        text_image_bold = dito.text(image=self.image, message="Hello " + dito.Font.STYLE_BOLD + "World", **self.text_kwargs)
        self.assertDifferingImages(text_image_regular, text_image_bold)

    def test_text_escape_regular(self):
        text_image_regular = dito.text(image=self.image, message="Hello World", **self.text_kwargs)
        text_image_bold_regular = dito.text(image=self.image, message="Hello " + dito.Font.STYLE_BOLD + dito.Font.STYLE_REGULAR + "World", **self.text_kwargs)
        self.assertEqualImages(text_image_regular, text_image_bold_regular)

    def test_text_escape_reset(self):
        text_image_regular = dito.text(image=self.image, message="Hello World", color=(255, 255, 255), background_color=(40, 40, 40), **self.text_kwargs)
        text_image_reset = dito.text(image=self.image, message="Hello " + dito.Font.STYLE_BOLD + dito.Font.FOREGROUND_BGR(0, 255, 0) + dito.Font.BACKGROUND_BGR(127, 127, 0) + dito.Font.RESET + "World", color=(255, 255, 255), background_color=(40, 40, 40), **self.text_kwargs)
        self.assertEqualImages(text_image_regular, text_image_reset)

    def test_text_escape_foregound_color(self):
        text_image = dito.text(image=self.image, message="Hello World", color=(0, 127, 255), **self.text_kwargs)
        text_image_foreground = dito.text(image=self.image, message="Hello " + dito.Font.FOREGROUND_BGR(200, 100, 50) + "World", color=(0, 127, 255), **self.text_kwargs)
        self.assertDifferingImages(text_image, text_image_foreground)

    def test_text_escape_backgound_color(self):
        text_image = dito.text(image=self.image, message="Hello World", background_color=(0, 127, 255), **self.text_kwargs)
        text_image_background = dito.text(image=self.image, message="Hello " + dito.Font.BACKGROUND_BGR(200, 100, 50) + "World", background_color=(0, 127, 255), **self.text_kwargs)
        self.assertDifferingImages(text_image, text_image_background)

    def test_text_border_different(self):
        text_image_no_border = dito.text(image=self.image, message="Hello World", border=0, **self.text_kwargs)
        text_image_border = dito.text(image=self.image, message="Hello World", border=1, **self.text_kwargs)
        self.assertDifferingImages(text_image_no_border, text_image_border)

    def test_text_margin_different(self):
        text_image_no_margin = dito.text(image=self.image, message="Hello World", margin=0, **self.text_kwargs)
        text_image_margin = dito.text(image=self.image, message="Hello World", margin=1, **self.text_kwargs)
        self.assertDifferingImages(text_image_no_margin, text_image_margin)

    def test_text_padding_different(self):
        text_image_no_padding = dito.text(image=self.image, message="Hello World", padding=0, **self.text_kwargs)
        text_image_padding = dito.text(image=self.image, message="Hello World", padding=1, **self.text_kwargs)
        self.assertDifferingImages(text_image_no_padding, text_image_padding)

    def test_text_transparent(self):
        text_image = dito.text(image=self.image, message="Hello World", opacity=0.0, **self.text_kwargs)
        self.assertEqualImages(self.image, text_image)

    def test_text_opaque(self):
        text_image_opacity_1 = dito.text(image=self.image, message="Hello World", opacity=1.0, **self.text_kwargs)
        text_image_opacity_none = dito.text(image=self.image, message="Hello World", opacity=None, **self.text_kwargs)
        self.assertEqualImages(text_image_opacity_1, text_image_opacity_none)

    def test_text_alignment(self):
        text_image_left = dito.text(image=self.image, message="Hellooo\nWorld", alignment="left", **self.text_kwargs)
        text_image_center = dito.text(image=self.image, message="Hellooo\nWorld", alignment="center", **self.text_kwargs)
        text_image_right = dito.text(image=self.image, message="Hellooo\nWorld", alignment="right", **self.text_kwargs)
        self.assertDifferingImages(text_image_left, text_image_center)
        self.assertDifferingImages(text_image_left, text_image_right)
        self.assertDifferingImages(text_image_center, text_image_right)

    def test_text_scale_none(self):
        text_image_scale_none = dito.text(image=self.image, message="Hello World", scale=None, **self.text_kwargs)
        text_image_scale_0 = dito.text(image=self.image, message="Hello World", scale=1.0, **self.text_kwargs)
        self.assertEqualImages(text_image_scale_none, text_image_scale_0)

    def test_text_scale_different(self):
        text_image_scale_none = dito.text(image=self.image, message="Hello World", scale=None, **self.text_kwargs)
        text_image_scale_0 = dito.text(image=self.image, message="Hello World", scale=2.0, **self.text_kwargs)
        self.assertDifferingImages(text_image_scale_none, text_image_scale_0)

    def test_text_rotation_none(self):
        text_image_rotation_none = dito.text(image=self.image, message="Hello World", rotation=None, **self.text_kwargs)
        text_image_rotation_0 = dito.text(image=self.image, message="Hello World", rotation=0, **self.text_kwargs)
        text_image_rotation_0_0 = dito.text(image=self.image, message="Hello World", rotation=0.0, **self.text_kwargs)
        self.assertEqualImages(text_image_rotation_none, text_image_rotation_0)
        self.assertEqualImages(text_image_rotation_none, text_image_rotation_0_0)

    def test_text_rotation_different(self):
        text_image_no_rotation = dito.text(image=self.image, message="Hello World", rotation=None, **self.text_kwargs)
        text_image_rotation = dito.text(image=self.image, message="Hello World", rotation=90, **self.text_kwargs)
        self.assertDifferingImages(text_image_no_rotation, text_image_rotation)


class VideoSaver_Tests(TempDirTestCase):
    def test_VideoSaver_random_video(self):
        # video settings
        codec = "MJPG"
        fps = 12.0
        image_size = (320, 240)
        frame_count = int(1.0 * fps)
        min_file_size = 250000

        filename = os.path.join(self.temp_dir.name, "VideoSaver.avi")
        with dito.VideoSaver(filename=filename, codec=codec, fps=fps) as saver:
            # save video
            for n_frame in range(frame_count):
                image = dito.random_image(size=image_size, color=True)
                saver.append(image=image)

            # save summary
            summary_filename = os.path.join(self.temp_dir.name, "VideoSaver_summary.txt")
            with open(summary_filename, "w") as f:
                saver.print_summary(file=f)

        # check video file
        self.assertTrue(saver.file_exists())
        self.assertGreaterEqual(saver.get_file_size(), min_file_size)

        # check summary file
        self.assertTrue(os.path.exists(summary_filename))
        with open(summary_filename, "r") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 12)

    def test_VideoSaver_raise_on_invalid_size(self):
        filename = os.path.join(self.temp_dir.name, "VideoSaver.avi")
        codec = "MJPG"
        fps = 10.0
        image_size = (320, 240)

        with dito.VideoSaver(filename=filename, codec=codec, fps=fps) as saver:
            for n_frame in range(2):
                if n_frame == 0:
                    image = dito.random_image(size=image_size)
                    saver.append(image=image)
                else:
                    image = dito.random_image(size=tuple(value + 1 for value in image_size))
                    self.assertRaises(ValueError, lambda: saver.append(image=image))


####
#%%% test cases (old)
####


class core_Tests(TestCase):
    def test_flip_channels_values(self):
        image = dito.pm5544()
        image_flipped = dito.flip_channels(image=image)
        for n_channel in range(3):
            self.assertEqualImages(image[:, :, n_channel], image_flipped[:, :, 2 - n_channel])
        
    def test_flip_channels_once_neq(self):
        image = dito.pm5544()
        image_flipped = dito.flip_channels(image=image)
        self.assertDifferingImages(image, image_flipped)

    def test_flip_channels_twice(self):
        image = dito.pm5544()
        image_flipped = dito.flip_channels(image=image)
        image_flipped_flipped = dito.flip_channels(image=image_flipped)
        self.assertEqualImages(image, image_flipped_flipped)


class data_Tests(TestCase):
    def test_data_dir_exists(self):
        self.assertTrue(os.path.exists(dito.RESOURCES_DIR))
    
    def test_data_files_exists(self):
        for filename in dito.RESOURCES_FILENAMES.values():
            self.assertTrue(os.path.exists(filename), "Data file '{}' does not exist".format(filename))

    def test_pm5544_load(self):
        image = dito.pm5544()
        self.assertIsImage(image)
        self.assertEqual(image.shape, (576, 768, 3))
    
    def test_xslope_width256(self):
        for height in (1, 32):
            slope = dito.xslope(height=height, width=256)
            self.assertIsImage(slope)
            self.assertEqual(slope.dtype, np.uint8)
            self.assertEqual(slope.shape, (height, 256))
            for x in range(256):
                for y in range(height):
                    self.assertEqual(slope[y, x], x)
    
    def test_xslope_widthNot256(self):
        height = 1
        for width in (2, 32, 256, 1000):
            slope = dito.xslope(height=height, width=width)
            self.assertIsImage(slope)
            self.assertEqual(slope.dtype, np.uint8)
            self.assertEqual(slope.shape, (height, width))
            for y in range(height):
                self.assertEqual(slope[y, 0], 0)
                self.assertEqual(slope[y, width - 1], 255)

    def test_yslope(self):
        height = 256
        width = 32
        slope = dito.yslope(width=width, height=height)
        self.assertIsImage(slope)
        self.assertEqual(slope.dtype, np.uint8)
        self.assertEqual(slope.shape, (height, width))
        for x in range(width):
            for y in range(height):
                self.assertEqual(slope[y, x], y)


class geometry_Tests(TestCase):
    def test_size(self):
        image = dito.pm5544()
        self.assertEqual(dito.size(image), (768, 576))


class infos_Tests(TestCase):
    def test_hist_color(self):
        image = dito.pm5544()
        h = dito.hist(image, bin_count=256)
        self.assertAlmostEqual(h[0], 328389.0)
        self.assertAlmostEqual(h[6], 1512.0)
        self.assertAlmostEqual(h[86], 0.0)
        self.assertAlmostEqual(h[122], 330802.0)
        self.assertAlmostEqual(h[134], 7.0)
        self.assertAlmostEqual(h[191], 112044.0)
        self.assertAlmostEqual(h[195], 3.0)
        self.assertAlmostEqual(h[255], 212526.0)
        
    def test_hist_gray(self):
        image = dito.pm5544()
        image_b = image[:, :, 0]
        h = dito.hist(image_b, bin_count=256)
        self.assertAlmostEqual(h[11], 18036.0)
        self.assertAlmostEqual(h[73], 88.0)
        self.assertAlmostEqual(h[170], 2528.0)
        self.assertAlmostEqual(h[255], 70842.0)
    
    def test_hist_gray_2dim_vs_3dim(self):
        image = dito.pm5544()
        
        image_2dim = image[:, :, 0]
        h_2dim = dito.hist(image_2dim, bin_count=256)
        
        image_3dim = image_2dim.copy()
        image_3dim.shape = image_3dim.shape + (1,)
        h_3dim = dito.hist(image_3dim, bin_count=256)
        
        self.assertEqual(len(h_2dim), len(h_3dim))
        for (value_2dim, value_3dim) in zip(h_2dim, h_3dim):
            self.assertAlmostEqual(value_2dim, value_3dim)
            
    def test_hist_gray_vs_color(self):
        image = dito.pm5544()
        
        image_b = image[:, :, 0]
        image_g = image[:, :, 1]
        image_r = image[:, :, 2]

        h_sum = dito.hist(image_b, bin_count=256) + dito.hist(image_g, bin_count=256) + dito.hist(image_r, bin_count=256)
        h_color = dito.hist(image, bin_count=256)
        
        self.assertEqual(len(h_sum), len(h_color))
        for (value_sum, value_color) in zip(h_sum, h_color):
            self.assertAlmostEqual(value_sum, value_color)


class io_Tests(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image_filename = os.path.join(dito.RESOURCES_FILENAMES["image:PM5544"])
        self.shape = (576, 768, 3)
    
    def test_decode_default(self):
        with open(self.image_filename, "rb") as f:
            image = dito.decode(b=f.read())
        self.assertNumpyShape(image, self.shape)
        self.assertAlmostEqual(np.mean(image), 121.3680261682581)
        
    def test_decode_grayscale(self):
        with open(self.image_filename, "rb") as f:
            image = dito.decode(b=f.read(), color=False)
        self.assertNumpyShape(image, self.shape[:2])
        



class transforms_Tests(TestCase):
    pass

        
class utils_Tests(TestCase):
    def test_tir_args(self):
        items = (1.24, -1.87)
        self.assertEqual(dito.tir(*items), (1, -2))
        self.assertEqual(dito.tir(items), (1, -2))
        self.assertEqual(dito.tir(list(items)), (1, -2))

        
if __name__ == "__main__":
    unittest.main()
