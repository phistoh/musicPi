# -*- coding: utf-8 -*-

import os
import time
import random
import threading
import dothat.lcd as lcd
import dothat.backlight as backlight
from mpd import MPDClient

# shortens long strings to max. l characters and surrounds (shorter) strings with spaces
def center_str(str, l=16):
	if l < 3:
		return ''
	if len(str) > l:
		return str[0:l-3] + "..."
	else:
		return str.center(l)

# takes an integer s and returns a string "min:sec" with sec in [00, 59]
def convert_seconds_to_minutes(s):
	min, sec = divmod(s,60)
	min, sec = str(min), str(sec).rjust(2,'0')
	return ":".join((min, sec))
		
def get_artist_and_title():
	songinfo = client.currentsong()
	artist = songinfo['artist']
	title = songinfo['title']
	
	return artist, title

# returns a percentage
def get_progress():
	statusinfo = client.status()
	
	if statusinfo['state'] == 'stop':
		return 0
	
	elapsed, total = statusinfo['time'].split(':')
	elapsed = int(elapsed)
	total = int(total)
	
	pct = 0
	if total > 0:
		pct = round(elapsed/total, 2)
	
	return min(pct, 100)

# returns the time and duration of a song
def get_time_and_duration():
	statusinfo = client.status()
	
	if statusinfo['state'] == 'stop':
		return ''
	
	elapsed, total = statusinfo['time'].split(':')
	elapsed = convert_seconds_to_minutes(int(elapsed))
	total = convert_seconds_to_minutes(int(total))
	
	return '{} / {}'.format(elapsed, total)
	
# generates three integers in [0,255] to use as color for dothat.backlight.rgb()
# ensures that at least one integer is >= 100
def get_rgb(str):
	random.seed(str)
	r = random.randrange(255)
	g = random.randrange(255)
	b = random.randrange(255)
	while r < 100 and g < 100 and b < 100:
		r = random.randrange(255)
		g = random.randrange(255)
		b = random.randrange(255)	
	return r, g, b

# cleans either a single line or all lines on the display
def clear_display(line=3):
	display_lock.acquire(timeout=1)
	if line > 2:
		lcd.clear()
	else:
		lcd.set_cursor_position(0,line)
		lcd.write(16*" ")
	display_lock.release()

# writes a string at a given position on the display
# doesn't prohibit line breaks
def write_at_position(str, x, y):
	display_lock.acquire(timeout=1)
	if x < 16 and y < 3:
		lcd.set_cursor_position(x, y)
		lcd.write(str)
	display_lock.release()

# writes the display in the following form:
# +----------------+
# |     Artist     |
# |     Title      |
# |  0:35 / 3:56   |
# +----------------+
def music_display():
	global last_artist, last_song
	while running:
		current_artist, current_song = get_artist_and_title()
		song_time = get_time_and_duration()
		if last_artist != current_artist or last_song != current_song:
			last_artist, last_song = current_artist, current_song
			
			current_artist = center_str(current_artist)
			current_song = center_str(current_song)
			
			write_at_position(current_artist, 0, 0)
			write_at_position(current_song, 0, 1)
		
		song_time = center_str(song_time)
		write_at_position(song_time, 0, 2)
			
		time.sleep(1)		

# sets the display color depending on artist or status		
def color_display():
	global last_artist
	while running:
		current_artist, _ = get_artist_and_title()
		current_state = client.status()['state']
		# playing but with a different artist -> get associated color
		if last_artist != current_artist and current_state == 'play':
			last_artist = current_artist		
			r, g, b = get_rgb(current_artist)
			backlight.rgb(r,g,b)
		# paused -> get "pause-color"
		elif current_state == 'pause':
			backlight.rgb(50,50,50)
		# stopped -> turn color off
		elif current_state == 'stop':
			backlight.off()
		
		time.sleep(1)

# sets the progress bar leds
def progress_bar():
	global last_artist
	while running:
		progress = get_progress()
		backlight.set_graph(progress)			
		time.sleep(1)
		
# ============== GLOBVARS ==============
last_artist, last_song = "", ""
client = MPDClient()
		
# ============== MAIN ==============
try:
	client.connect("localhost", 6600)

	running = True
	
	display_lock = threading.Lock()
	
	music_display_thread = threading.Thread(target=music_display)
	music_display_thread.setDaemon(True)
	music_display_thread.start()
	
	color_display_thread = threading.Thread(target=color_display)
	color_display_thread.setDaemon(True)
	color_display_thread.start()
	
	progress_bar_thread = threading.Thread(target=progress_bar)
	progress_bar_thread.setDaemon(True)
	progress_bar_thread.start()
	
	while True:
		pass
	
except KeyboardInterrupt:
	running = False
	music_display_thread.join()
	color_display_thread.join()
	progress_bar_thread.join()
	lcd.clear()
	backlight.off()
	client.stop()
	client.close()
	print("Ende")
	
