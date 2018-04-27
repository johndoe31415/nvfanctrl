#!/usr/bin/python3
#	nvfanctrl - Control the fan speed of NVidia GPUs in software.
#	Copyright (C) 2018-2018 Johannes Bauer
#
#	This file is part of nvfanctrl.
#
#	nvfanctrl is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; this program is ONLY licensed under
#	version 3 of the License, later versions are explicitly excluded.
#
#	nvfanctrl is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#	Johannes Bauer <JohannesBauer@gmx.de>

import os
import sys
import time
import subprocess
from FriendlyArgumentParser import FriendlyArgumentParser

def daemonize():
	pid = os.fork()
	if pid == 0:
		# I'm the golden child!
		return

	# No country for old men.
	sys.exit(0)

class NvidiaRegulator(object):
	def __init__(self, args):
		self._args = args
		self._target = self._args.initial_pwm
		subprocess.check_call([ "nvidia-settings", "--assign", "[%s]/GPUFanControlState=1" % (self._args.gpu) ], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)

	def _get_temp(self):
		output = subprocess.check_output([ "nvidia-settings", "--query", "GPUCoreTemp", "--terse" ])
		temperature = float(output.decode("ascii").rstrip("\r\n"))
		return temperature

	def _set_speed(self, percent):
		if percent < self._args.min_speed:
			percent = self._args.min_speed
		elif percent > self._args.max_speed:
			percent = self._args.max_speed
		if percent < 0:
			percent = 0
		elif percent > 100:
			percent = 100
		percent = round(percent)
		if percent != self._target:
			subprocess.check_call([ "nvidia-settings", "--assign", "[%s]/GPUTargetFanSpeed=%d" % (self._args.fan, round(percent)) ], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
			self._target = percent
			return True
		else:
			return False

	def _calc_adjustment(self, error):
		abserror = abs(error)
		if abserror < self._args.regulation_deadzone:
			adj = 0
		elif abserror < 5:
			adj = 2
		elif abserror < 10:
			adj = 5
		else:
			adj = 10
		if error > 0:
			return adj
		else:
			return -adj

	def _iteration_regulate(self):
		temp = self._get_temp()
		error = temp - self._args.target_temp
		adjustment = self._calc_adjustment(error)

		did_adjust = self._set_speed(self._target + adjustment)
		if did_adjust:
			if self._args.verbose >= 1:
				print("Temperature %.0f°C, error %.0f°C, adjusting %+.0f%% PWM -> set %.0f%% PWM" % (temp, error, adjustment, self._target))
		else:
			if self._args.verbose >= 2:
				print("Temperature %.0f°C, error %.0f°C, not adjusting -> remaining %.0f%% PWM" % (temp, error, self._target))

	def _iteration_curve(self):
		raise Exception(NotImplemented)

	def run(self):
		while True:
			self._iteration_regulate()
			time.sleep(self._args.regulation_interval)

	def reset(self):
		# Reset automatic temperature determination
		subprocess.check_call([ "nvidia-settings", "--assign", "[%s]/GPUFanControlState=0" % (self._args.gpu) ], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)

parser = FriendlyArgumentParser()
parser.add_argument("-t", "--target-temp", metavar = "temp", type = float, default = 55, help = "Specifies the GPU target temperature in °C. Defaults to %(default).0f°C")
parser.add_argument("-i", "--regulation-interval", metavar = "secs", type = float, default = 2.5, help = "Gives the interval in which the fan target is checked and adjustments are made. Defaults to %(default).1f seconds.")
parser.add_argument("--regulation-deadzone", metavar = "temp", type = float, default = 3, help = "Gives the deadzone, i.e. +- degrees C in which not to change regulation parameters. Defaults to +-%(default).1f°C.")
parser.add_argument("--initial-pwm", metavar = "%", type = float, default = 50, help = "When initially starting, gives the initial PWM duty cycle in percent that should be given to the fan. Defaults to %(default).0f%%.")
parser.add_argument("--min-speed", metavar = "%", type = float, default = 20, help = "Defines the minimum fan target speed in percent that is chosen.")
parser.add_argument("--max-speed", metavar = "%", type = float, default = 100, help = "Defines the maximum fan target speed in percent that is chosen.")
parser.add_argument("--fan", metavar = "fan_id", type = str, default = "fan:0", help = "The ID of the fan that should be regulated. Defaults to %(default)s.")
parser.add_argument("--gpu", metavar = "gpu_id", type = str, default = "gpu:0", help = "The ID of the GPU that should be regulated. Defaults to %(default)s.")
parser.add_argument("--daemonize", action = "store_true", help = "Fork into background (but do not make init the parent process, so that nvfanctrl terminates when the X session terminates as well).")
parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Be more verbose.")
args = parser.parse_args(sys.argv[1:])

regulator = NvidiaRegulator(args)
if args.daemonize:
	daemonize()
try:
	regulator.run()
finally:
	regulator.reset()
