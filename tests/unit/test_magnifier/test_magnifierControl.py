# A part of NonVisual Desktop Access (NVDA)
# Copyright (C) 2026 NVDA contributors
# This file may be used under the terms of the GNU General Public License, version 2 or later, as modified by the NVDA license.
# For full terms and any additional permissions, see the NVDA license file: https://github.com/nvaccess/nvda/blob/master/copying.txt

import unittest
from ctypes.wintypes import HWND, RECT
from unittest.mock import patch

from _magnifier.magnifierControl import MagnifierControl
from winBindings import magnification


class TestMagnifierControl(unittest.TestCase):
	def setUp(self) -> None:
		self.parentHwnd = HWND(100)
		self.childHwnd = HWND(200)
		self.user32Patcher = patch("_magnifier.magnifierControl.user32")
		self.magnificationPatcher = patch("_magnifier.magnifierControl.magnification")
		self.mockUser32 = self.user32Patcher.start()
		self.mockMagnification = self.magnificationPatcher.start()
		self.addCleanup(self.user32Patcher.stop)
		self.addCleanup(self.magnificationPatcher.stop)

		self.mockUser32.CreateWindowEx.return_value = self.childHwnd
		self.mockUser32.DestroyWindow.return_value = True
		self.mockMagnification.WC_MAGNIFIER = magnification.WC_MAGNIFIER
		self.mockMagnification.MS_SHOWMAGNIFIEDCURSOR = magnification.MS_SHOWMAGNIFIEDCURSOR
		self.mockMagnification.MW_FILTERMODE_EXCLUDE = magnification.MW_FILTERMODE_EXCLUDE
		self.mockMagnification.MAGTRANSFORM = magnification.MAGTRANSFORM

	def testCreateConfiguresChildAndExcludesHost(self) -> None:
		control = MagnifierControl(self.parentHwnd, 320, 240)
		control.create()

		self.assertEqual(control.hwnd, self.childHwnd)
		self.mockUser32.CreateWindowEx.assert_called_once_with(
			0,
			magnification.WC_MAGNIFIER,
			"NVDA Magnifier",
			0x40000000 | 0x10000000 | magnification.MS_SHOWMAGNIFIEDCURSOR,
			0,
			0,
			320,
			240,
			self.parentHwnd,
			None,
			None,
			None,
		)

		filterArgs = self.mockMagnification.MagSetWindowFilterList.call_args.args
		self.assertEqual(filterArgs[:3], (self.childHwnd, magnification.MW_FILTERMODE_EXCLUDE, 1))
		self.assertEqual(filterArgs[3][0], self.parentHwnd.value)

	def testCreateWithoutCursorOmitsCursorStyle(self) -> None:
		control = MagnifierControl(self.parentHwnd, 320, 240, showCursor=False)
		control.create()

		style = self.mockUser32.CreateWindowEx.call_args.args[3]
		self.assertEqual(style, 0x40000000 | 0x10000000)

	def testCreateIsIdempotent(self) -> None:
		control = MagnifierControl(self.parentHwnd, 320, 240)
		control.create()
		control.create()

		self.mockUser32.CreateWindowEx.assert_called_once()
		self.mockMagnification.MagSetWindowFilterList.assert_called_once()

	def testCreateCleansUpWhenFilterSetupFails(self) -> None:
		self.mockMagnification.MagSetWindowFilterList.side_effect = OSError("filter failed")
		control = MagnifierControl(self.parentHwnd, 320, 240)

		with self.assertRaisesRegex(OSError, "filter failed"):
			control.create()

		self.mockUser32.DestroyWindow.assert_called_once_with(self.childHwnd)
		with self.assertRaisesRegex(RuntimeError, "has not been created"):
			_ = control.hwnd

	def testDestroyIsIdempotent(self) -> None:
		control = MagnifierControl(self.parentHwnd, 320, 240)
		control.create()
		control.destroy()
		control.destroy()

		self.mockUser32.DestroyWindow.assert_called_once_with(self.childHwnd)
		with self.assertRaisesRegex(RuntimeError, "has not been created"):
			_ = control.hwnd

	def testSetZoomFactorBuildsDiagonalTransform(self) -> None:
		control = MagnifierControl(self.parentHwnd, 320, 240)
		control.create()
		control.setZoomFactor(2.5)

		transformArgs = self.mockMagnification.MagSetWindowTransform.call_args.args
		self.assertEqual(transformArgs[0], self.childHwnd)
		transform = transformArgs[1]
		self.assertEqual(transform.v[0][0], 2.5)
		self.assertEqual(transform.v[1][1], 2.5)
		self.assertEqual(transform.v[2][2], 1.0)
		self.assertEqual(transform.v[0][1], 0.0)

	def testSetSourceForwardsDesktopRect(self) -> None:
		control = MagnifierControl(self.parentHwnd, 320, 240)
		control.create()
		rect = RECT(-100, 25, 220, 265)

		control.setSource(rect)

		self.mockMagnification.MagSetWindowSource.assert_called_once_with(self.childHwnd, rect)

	def testRejectsInvalidDimensionsAndZoom(self) -> None:
		with self.assertRaisesRegex(ValueError, "dimensions must be positive"):
			MagnifierControl(self.parentHwnd, 0, 240)

		control = MagnifierControl(self.parentHwnd, 320, 240)
		control.create()
		with self.assertRaisesRegex(ValueError, "zoom factor must be positive"):
			control.setZoomFactor(0)
