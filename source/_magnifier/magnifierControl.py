# A part of NonVisual Desktop Access (NVDA)
# Copyright (C) 2026 NVDA contributors
# This file may be used under the terms of the GNU General Public License, version 2 or later, as modified by the NVDA license.
# For full terms and any additional permissions, see the NVDA license file: https://github.com/nvaccess/nvda/blob/master/copying.txt

"""Lifecycle wrapper for a Windows Magnifier child control."""

from ctypes import WinError
from ctypes.wintypes import HWND, RECT

from winBindings import magnification, user32


# Window styles from WinUser.h. These stay private because they are only implementation
# details of the native magnifier child control.
_WS_CHILD = 0x40000000
_WS_VISIBLE = 0x10000000
_CONTROL_WINDOW_NAME = "NVDA Magnifier"


class MagnifierControl:
	"""Own a ``WC_MAGNIFIER`` child window inside a caller-owned host window.

	The caller owns the Magnification API lifetime and must call ``MagInitialize`` before
	creating the control. The caller also owns the host HWND. This class only owns the
	child magnifier-control HWND and its per-control state.
	"""

	def __init__(self, parentHwnd: HWND, width: int, height: int, *, showCursor: bool = True) -> None:
		if width <= 0 or height <= 0:
			raise ValueError("magnifier control dimensions must be positive")
		if not parentHwnd:
			raise ValueError("magnifier control requires a valid parent HWND")

		self._parentHwnd = parentHwnd
		self._width = width
		self._height = height
		self._showCursor = showCursor
		self._hwnd: HWND | None = None

	@property
	def hwnd(self) -> HWND:
		"""Return the child-control HWND, or fail if the control has not been created."""
		if self._hwnd is None:
			raise RuntimeError("magnifier control has not been created")
		return self._hwnd

	def create(self) -> None:
		"""Create the child control and exclude its host from recursive magnification."""
		if self._hwnd is not None:
			return

		style = _WS_CHILD | _WS_VISIBLE
		if self._showCursor:
			style |= magnification.MS_SHOWMAGNIFIEDCURSOR

		hwnd = user32.CreateWindowEx(
			0,
			magnification.WC_MAGNIFIER,
			_CONTROL_WINDOW_NAME,
			style,
			0,
			0,
			self._width,
			self._height,
			self._parentHwnd,
			None,
			None,
			None,
		)
		if not hwnd:
			raise WinError()

		self._hwnd = hwnd
		try:
			excludedWindows = (HWND * 1)(self._parentHwnd)
			magnification.MagSetWindowFilterList(
				hwnd,
				magnification.MW_FILTERMODE_EXCLUDE,
				1,
				excludedWindows,
			)
		except Exception:
			# The control must not survive a partially failed setup because that could
			# recursively magnify its own host or leave an unmanaged native window.
			user32.DestroyWindow(hwnd)
			self._hwnd = None
			raise

	def destroy(self) -> None:
		"""Destroy the child control. Calling this repeatedly is safe."""
		if self._hwnd is None:
			return

		hwnd = self._hwnd
		if not user32.DestroyWindow(hwnd):
			raise WinError()
		self._hwnd = None

	def setZoomFactor(self, zoomFactor: float) -> None:
		"""Set a positive magnification factor on the child control."""
		if zoomFactor <= 0:
			raise ValueError("zoom factor must be positive")

		transform = magnification.MAGTRANSFORM()
		transform.v[0][0] = zoomFactor
		transform.v[1][1] = zoomFactor
		transform.v[2][2] = 1.0
		magnification.MagSetWindowTransform(self.hwnd, transform)

	def setSource(self, sourceRect: RECT) -> None:
		"""Set the desktop-coordinate source rectangle shown by the control."""
		magnification.MagSetWindowSource(self.hwnd, sourceRect)
