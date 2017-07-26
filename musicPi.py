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
	
# def alarm_check(schedule):
	# while running:
		# if alarm_status:
			# current_time = time.localtime()
			# # current_hour_and_minute = time.strftime("%H:%M", current_time)
			# current_hour_and_minute = "09:42"
			# current_weekday = time.strftime("%A", current_time)
			# if schedule[current_weekday] == current_hour_and_minute:
				# alarm()
		# time.sleep(1)
		
# def alarm():
	# write_at_position("ALARM!", 0, 1)

def clear_display(line=4):
	display_lock.acquire(timeout=1)
	if line > 3:
		lcd.clear()
	else:
		lcd.set_cursor_position(0,line)
		lcd.write(16*" ")
	display_lock.release()

def write_at_position(str, x, y):
	display_lock.acquire(timeout=1)
	if x < 16 and y < 3:
		lcd.set_cursor_position(x, y)
		lcd.write(str)
	display_lock.release()

# music in second line
def music_display():
	global last_artist, last_song
	while running:
		current_artist, current_song = get_artist_and_title()
		if last_artist != current_artist or last_song != current_song:
			last_artist, last_song = current_artist, current_song
			
			now_playing = current_artist + '-' + current_song
			
			if len(now_playing) > 16:
				now_playing = now_playing[0:15]
			
			clear_display(0)
			
			write_at_position(now_playing, 0, 0)
			
			client.idle()
	
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

			r, g, b = get_rgb(current_cond)
			backlight.rgb(r,g,b)
			
			time.sleep(5)
		
# date and time in third line		
def time_display():
	global last_time, last_date
	while running:
		current_time, current_date = get_time_and_date()
		
		if current_time != last_time or current_date != last_date:
			last_time, last_date = current_time, current_date
			clear_display(2)
			
			if alarm_status:
				write_at_position(".", 1, 2)
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
	alarm_status = False
	
	alarm_dict = {'Monday': "09:42", 'Tuesday': "07:00", 'Wednesday': "07:00", 'Thursday': "07:00", 'Friday': "07:00", 'Saturday': "07:00", 'Sunday': "07:00"}
	
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
	
	# alarm_thread = threading.Thread(target=alarm_check,args=(alarm_dict,))
	# alarm_thread.setDaemon(True)
	# alarm_thread.start()
	
	while True:
		pass
	
except KeyboardInterrupt:
	running = False
	music_display_thread.join()
	weather_display_thread.join()
	time_display_thread.join()
	# alarm_thread.join()
	lcd.clear()
	backlight.off()
	print("Ende")
	
