# from https://github.com/z3ntu/QtWaitingSpinner/blob/master/waitingspinnerwidget.py

"""
The MIT License (MIT)

Copyright (c) 2012-2014 Alexander Turkin
Copyright (c) 2014 William Hallatt
Copyright (c) 2015 Jacob Dawid
Copyright (c) 2016 Luca Weiss

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import math

from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QColor, QPaintEvent, QPainter
from PyQt5.QtWidgets import QWidget


class QtWaitingSpinner(QWidget):
	def __init__(
		self,
		parent: QWidget,
		centerOnParent: bool = True,
		disableParentWhenSpinning: bool = False,
		modality: Qt.WindowModality = Qt.WindowModality.NonModal,
	) -> None:
		super().__init__(parent)

		self._centerOnParent = centerOnParent
		self._disableParentWhenSpinning = disableParentWhenSpinning

		# WAS IN initialize()
		self._color = QColor(Qt.GlobalColor.black)
		self._roundness = 100.0
		self._minimumTrailOpacity = 3.14159265358979323846
		self._trailFadePercentage = 80.0
		self._revolutionsPerSecond = 1.57079632679489661923
		self._numberOfLines = 20
		self._lineLength: float = 10
		self._lineWidth: float = 2
		self._innerRadius: float = 10
		self._currentCounter = 0
		self._isSpinning = False

		self._timer = QTimer(self)
		self._timer.timeout.connect(self.rotate)  # type: ignore
		self.updateSize()
		self.updateTimer()
		self.hide()
		# END initialize()

		self.setWindowModality(modality)
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

	def paintEvent(self, qpe: QPaintEvent) -> None:
		self.updatePosition()
		painter = QPainter(self)
		painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
		painter.setRenderHint(QPainter.Antialiasing, True)

		if self._currentCounter >= self._numberOfLines:
			self._currentCounter = 0

		painter.setPen(Qt.PenStyle.NoPen)
		for i in range(0, self._numberOfLines):
			painter.save()
			painter.translate(
				self._innerRadius + self._lineLength, self._innerRadius + self._lineLength
			)
			rotateAngle = float(360 * i) / float(self._numberOfLines)
			painter.rotate(rotateAngle)
			painter.translate(self._innerRadius, 0)
			distance = self.lineCountDistanceFromPrimary(
				i, self._currentCounter, self._numberOfLines
			)
			color = self.currentLineColor(
				distance,
				self._numberOfLines,
				self._trailFadePercentage,
				self._minimumTrailOpacity,
				self._color,
			)
			painter.setBrush(color)
			painter.drawRoundedRect(
				QRect(0, int(-self._lineWidth / 2), int(self._lineLength), int(self._lineWidth)),
				self._roundness,
				self._roundness,
				Qt.SizeMode.RelativeSize,
			)
			painter.restore()

	def start(self) -> None:
		self.updatePosition()
		self._isSpinning = True
		self.show()

		if self.parentWidget and self._disableParentWhenSpinning:
			self.parentWidget().setEnabled(False)

		if not self._timer.isActive():
			self._timer.start()
			self._currentCounter = 0

	def stop(self) -> None:
		self._isSpinning = False
		self.hide()

		if self.parentWidget() and self._disableParentWhenSpinning:
			self.parentWidget().setEnabled(True)

		if self._timer.isActive():
			self._timer.stop()
			self._currentCounter = 0

	def setNumberOfLines(self, lines: int) -> None:
		self._numberOfLines = lines
		self._currentCounter = 0
		self.updateTimer()

	def setLineLength(self, length: float) -> None:
		self._lineLength = length
		self.updateSize()

	def setLineWidth(self, width: float) -> None:
		self._lineWidth = width
		self.updateSize()

	def setInnerRadius(self, radius: float) -> None:
		self._innerRadius = radius
		self.updateSize()

	def color(self) -> QColor:
		return self._color

	def roundness(self) -> float:
		return self._roundness

	def minimumTrailOpacity(self) -> float:
		return self._minimumTrailOpacity

	def trailFadePercentage(self) -> float:
		return self._trailFadePercentage

	def revolutionsPersSecond(self) -> float:
		return self._revolutionsPerSecond

	def numberOfLines(self) -> int:
		return self._numberOfLines

	def lineLength(self) -> float:
		return self._lineLength

	def lineWidth(self) -> float:
		return self._lineWidth

	def innerRadius(self) -> float:
		return self._innerRadius

	def isSpinning(self) -> bool:
		return self._isSpinning

	def setRoundness(self, roundness: float) -> None:
		self._roundness = max(0.0, min(100.0, roundness))

	def setColor(self, color: QColor = QColor(Qt.GlobalColor.black)) -> None:
		self._color = QColor(color)

	def setRevolutionsPerSecond(self, revolutionsPerSecond: float) -> None:
		self._revolutionsPerSecond = revolutionsPerSecond
		self.updateTimer()

	def setTrailFadePercentage(self, trail: float) -> None:
		self._trailFadePercentage = trail

	def setMinimumTrailOpacity(self, minimumTrailOpacity: float) -> None:
		self._minimumTrailOpacity = minimumTrailOpacity

	def rotate(self) -> None:
		self._currentCounter += 1
		if self._currentCounter >= self._numberOfLines:
			self._currentCounter = 0
		self.update()

	def updateSize(self) -> None:
		size = int((self._innerRadius + self._lineLength) * 2)
		self.setFixedSize(size, size)

	def updateTimer(self) -> None:
		self._timer.setInterval(
			int(1000 / (self._numberOfLines * self._revolutionsPerSecond))
		)

	def updatePosition(self) -> None:
		if self.parentWidget() and self._centerOnParent:
			self.move(
				int(self.parentWidget().width() / 2 - self.width() / 2),
				int(self.parentWidget().height() / 2 - self.height() / 2),
			)

	def lineCountDistanceFromPrimary(
		self, current: int, primary: int, totalNrOfLines: int
	) -> int:
		distance = primary - current
		if distance < 0:
			distance += totalNrOfLines
		return distance

	def currentLineColor(
		self,
		countDistance: int,
		totalNrOfLines: int,
		trailFadePerc: float,
		minOpacity: float,
		colorinput: QColor,
	) -> QColor:
		color = QColor(colorinput)
		if countDistance == 0:
			return color
		minAlphaF = minOpacity / 100.0
		distanceThreshold = int(math.ceil((totalNrOfLines - 1) * trailFadePerc / 100.0))
		if countDistance > distanceThreshold:
			color.setAlphaF(minAlphaF)
		else:
			alphaDiff = color.alphaF() - minAlphaF
			gradient = alphaDiff / float(distanceThreshold + 1)
			resultAlpha = color.alphaF() - gradient * countDistance
			# If alpha is out of bounds, clip it.
			resultAlpha = min(1.0, max(0.0, resultAlpha))
			color.setAlphaF(resultAlpha)
		return color
