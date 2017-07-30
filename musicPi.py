# -*- coding: utf-8 -*-

import os
import time
import random
import threading
import dothat.lcd as lcd
import dothat.backlight as backlight
from mpd import MPDClient

def get_artist_and_title():
	songinfo = client.currentsong()
	artist = songinfo['artist']
	title = songinfo['title']
	
	return artist, title

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
	
def get_time_and_date():
	current_time = time.strftime("%H:%M")
	current_date = time.strftime("%d-%m")
	return current_time, current_date

def get_weather():	
	random.seed()
	current_temp = str(random.randint(-30, 45))+"C"
	current_cond = random.choice(["Sonne", "Wolken", "Regen", "Schnee", "Blitz", "Hagel", "Nebel"])
	return current_temp, current_cond

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
	
def alarm_check():
	schedule = {'Monday': "09:42", 'Tuesday': "07:00", 'Wednesday': "07:00", 'Thursday': "07:00", 'Friday': "07:00", 'Saturday': "07:00", 'Sunday': "13:10"}
	current_time = time.strftime("%H:%M")
	current_weekday = time.strftime("%A")
	
	if schedule[current_weekday] == current_time:
		alarm()
		
def alarm():
	# TODO: load alarm playlist
	client.shuffle()
	client.play()

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

# music in first line
def music_display():
	global last_artist, last_song
	while running:
		current_artist, current_song = get_artist_and_title()
		progress = get_progress()
		backlight.set_graph(progress)
		if last_artist != current_artist or last_song != current_song:
			last_artist, last_song = current_artist, current_song
			
			now_playing = current_artist + ' - ' + current_song
			
			if len(now_playing) > 16:
				now_playing = now_playing[0:15]
			
			clear_display(0)
			
			write_at_position(now_playing, 0, 0)
			
			r, g, b = get_rgb(current_artist)
			backlight.rgb(r,g,b)
			
		# client.idle()
		time.sleep(1)
			
# weather in second line
def weather_display():
	global last_temp, last_cond
	while running:
		current_temp, current_cond = get_weather()
		if last_temp != current_temp or last_cond != current_cond:
			last_temp, last_cond = current_temp, current_cond
			clear_display(1)
			
			write_at_position(current_temp, 7-len(current_temp), 1)
			write_at_position(current_cond, 9, 1)
			
			time.sleep(5)
		
# date and time in third line
# also calls alarm_check()
def time_display():
	global last_time, last_date
	while running:
		current_time, current_date = get_time_and_date()
		
		if current_time != last_time or current_date != last_date:
			last_time, last_date = current_time, current_date
			clear_display(2)
			
			if alarm_status:
				write_at_position(".", 1, 2)
				alarm_check()
			else:
				write_at_position(" ", 1, 2)
			write_at_position(current_time, 2, 2)
			write_at_position(current_date, 9, 2)

		time.sleep(1)		
		
# ============== GLOBVARS ==============
last_time, last_date = "", ""
last_temp, last_cond = "", ""
last_artist, last_sond = "", ""
client = MPDClient()
		
# ============== MAIN ==============
try:
	client.connect("localhost", 6600)

	running = True
	alarm_status = True
	
	display_lock = threading.Lock()
	
	music_display_thread = threading.Thread(target=music_display)
	music_display_thread.setDaemon(True)
	music_display_thread.start()
	
	weather_display_thread = threading.Thread(target=weather_display)
	weather_display_thread.setDaemon(True)
	weather_display_thread.start()
	
	time_display_thread = threading.Thread(target=time_display)
	time_display_thread.setDaemon(True)
	time_display_thread.start()
	
	while True:
		pass
	
except KeyboardInterrupt:
	running = False
	music_display_thread.join()
	weather_display_thread.join()
	time_display_thread.join()
	lcd.clear()
	backlight.off()
	client.stop()
	client.close()
	print("Ende")
	
