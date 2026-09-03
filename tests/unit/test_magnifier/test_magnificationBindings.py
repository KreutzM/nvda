# A part of NonVisual Desktop Access (NVDA)
# Copyright (C) 2026 NVDA contributors
# This file may be used under the terms of the GNU General Public License, version 2 or later, as modified by the NVDA license.
# For full terms and any additional permissions, see the NVDA license file: https://github.com/nvaccess/nvda/blob/master/copying.txt

import unittest
from ctypes import c_float, sizeof

from winBindings import magnification


class TestMagnificationControlBindings(unittest.TestCase):
	def testMagnifierControlClassAndStyles(self) -> None:
		self.assertEqual(magnification.WC_MAGNIFIER, "Magnifier")
		self.assertEqual(magnification.MS_SHOWMAGNIFIEDCURSOR, 0x0001)
		self.assertEqual(magnification.MS_CLIPAROUNDCURSOR, 0x0002)
		self.assertEqual(magnification.MS_INVERTCOLORS, 0x0004)

	def testMagnifierWindowFilterModes(self) -> None:
		self.assertEqual(magnification.MW_FILTERMODE_EXCLUDE, 0)
		self.assertEqual(magnification.MW_FILTERMODE_INCLUDE, 1)

	def testMagTransformIsThreeByThreeFloatMatrix(self) -> None:
		transform = magnification.MAGTRANSFORM()
		transform.v[0][0] = 2.5
		transform.v[1][1] = 2.5
		transform.v[2][2] = 1.0

		self.assertEqual(sizeof(transform), sizeof(c_float) * 9)
		self.assertEqual(transform.v[0][0], 2.5)
		self.assertEqual(transform.v[1][1], 2.5)
		self.assertEqual(transform.v[2][2], 1.0)
		self.assertEqual(transform.v[0][1], 0.0)
