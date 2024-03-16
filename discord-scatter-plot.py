#!/usr/bin/env python3
import argparse
import glob
import json
import math
import os
import sys
from datetime import datetime

import dateutil.parser
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy
import pytz
from matplotlib.axis import Axis

# Based on https://gist.github.com/adryd325/f811e975bf8240fb6e6555e57c3db7d2
# Download your data dump and place this file in the root folder of your data dump.
# Then run it! Make sure you installed the dependencies first.

def utc_string_from_minutes(minutes: int) -> str:
	minutes_frac, hours = math.modf(minutes / 60)
	minutes_frac = int(abs(numpy.fix(minutes_frac * 60)))
	if minutes_frac == 0:
		return f"UTC{hours:+.0f}"

	return f"UTC{hours:+.0f}:{minutes_frac:02d}"


def main(args: argparse.Namespace):
	archive_dir = os.path.abspath(args.input)

	user_json_path = os.path.join(archive_dir, "account", "user.json")
	messages_path = os.path.join(archive_dir, "messages")
	now = datetime.now

	if not os.path.exists(user_json_path) or not os.path.exists(messages_path):
		print(f"{archive_dir} is not a valid discord data archive")
		sys.exit(1)

	with open(user_json_path, encoding="utf8") as user_json:
		user_info = json.load(user_json)

	user_name = user_info["global_name"]
	print(f"discord user: {user_name}")

	# this is an offset to UTC in negative minutes. a value of -60 equals UTC+1 because discord"s backend is deranged
	tz_offset = user_info["settings"]["settings"]["localization"]["timezoneOffset"]
	user_timezone = pytz.FixedOffset(-tz_offset)
	user_timezone_name = utc_string_from_minutes(-tz_offset)

	print("finding messages…")
	message_files = glob.glob(os.path.join(messages_path, "**", "messages.json"), recursive=True)
	message_dates: list[datetime] = []
	print("parsing messages…")
	for mf in message_files:
		with open(mf, encoding="utf8") as message_json:
			message_list = json.load(message_json)
			for msg in message_list:
				msg_date = dateutil.parser.parse(msg["Timestamp"]).astimezone(user_timezone)
				message_dates.append(msg_date)

	print(f"total messages: {len(message_dates)}")

	print("processing dates…")
	dates: list[datetime] = []
	times: list[datetime] = []
	for date in message_dates:
		only_date = datetime(date.year, date.month, date.day)
		only_time = datetime(1970, 1, 1, date.hour, date.minute, date.second)
		dates.append(only_date)
		times.append(only_time)

	print("creating graph…")
	date_major_loc = mdates.YearLocator()
	date_minor_loc = mdates.MonthLocator()
	date_major_fmt = mdates.DateFormatter("%Y")
	date_minor_fmt = mdates.DateFormatter("")
	time_major_loc = mdates.HourLocator(interval=6)
	time_minor_loc = mdates.HourLocator(interval=1)
	time_major_fmt = mdates.DateFormatter("%H:%M")

	fig, ax = plt.subplots(figsize=((max(dates) - min(dates)).days / 200, 3))
	ax.set_axisbelow(True)
	plt.grid(linewidth=1/3, which="minor", color="0.75")
	plt.grid(linewidth=2/3, which="major", color="0.66")

	plt.scatter(dates, times, s=2/3, linewidths=0, color="#5865F2")
	plt.xlim(min(dates), max(dates))
	plt.ylim(0, 1)
	date_axis: Axis = ax.xaxis
	time_axis: Axis = ax.yaxis

	# time goes downwards and to the right
	plt.gca().invert_yaxis()

	date_axis.set_major_locator(date_major_loc)
	date_axis.set_minor_locator(date_minor_loc)
	date_axis.set_major_formatter(date_major_fmt)
	date_axis.set_minor_formatter(date_minor_fmt)

	time_axis.set_major_locator(time_major_loc)
	time_axis.set_minor_locator(time_minor_loc)
	time_axis.set_major_formatter(time_major_fmt)

	time_axis.set_label("Time of Day")
	date_axis.set_label("Date")
	plt.title(f"When does {user_name} post on Discord? ({user_timezone_name})")

	print("rendering png…")
	plt.savefig(os.path.join(archive_dir, "out.png"), bbox_inches="tight", pad_inches=0.3, dpi=300)
	print("rendering svg…")
	plt.savefig(os.path.join(archive_dir, "out.svg"), bbox_inches="tight", pad_inches=0.3)

	print("done!")


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="plots the date/time of all of your discord messages on a graph")
	parser.add_argument("-i", "--input", type=str, default=".", help="the path to the unpacked discord data archive")

	main(parser.parse_args())
