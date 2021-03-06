import sys
import os
import subprocess
import datetime
from time import sleep
from PIL import Image

def nowString():
	return '{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())

def isffmpegReady():
	x = subprocess.Popen('which ffmpeg', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	return len(x.stdout.readlines()) != 0

def listFolderByDate(rootDir, howManyDays):
	folderList = []
	if rootDir.endswith('/') == False:
		rootDir += '/'

	if os.path.isdir(rootDir) == False:	
		return folderList
	
	today = datetime.date.today()
	for i in range(0, howManyDays):
		dateStr = (today - datetime.timedelta(days=i)).strftime('%Y%m%d')
		folderList.append('{0}{1}/'.format(rootDir, dateStr))

	return folderList

def listFilePath(rootDir, isDir=False, endswith=''):
	paths = ['{0}{1}'.format(rootDir, x) for x in os.listdir(rootDir) if os.path.isdir('{0}{1}'.format(rootDir, x)) == isDir]
	if isDir == False:
		paths = [x for x in paths if x.endswith(endswith)]
	else:
		paths = ['{0}/'.format(x) for x in paths]
	return paths


def transcodeThisClip(tmp):
	print('---> Transcode the video clip {0}'.format(tmp))
	
	mp4 = tmp.replace('.tmp', '.mp4')
	if os.path.exists(mp4):
		print '\n\t{0} is detected. Skip. \n\tPlease delete .mp4 file if you need re-transcode.'.format(mp4)
		return

	arf = tmp.replace('.tmp', '.arf')
	if os.path.exists(arf):
		print '\n\t{0} is detected. Skip. \n\t.arf is the middle file while transcoding is in progress.'.format(arf)
		return

	cmd = 'ffmpeg -i {0} -loglevel fatal -threads 2 -c:v libx264 -c:a copy -f mp4 {1}'.format(tmp, arf)
	print '\t{0}'.format(cmd)
	x = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	for log in x.stdout.readlines():
		print '[ffmpeg info] {0}'.format(log)
	for log in x.stderr.readlines():
		print '[ffmpeg error] {0}'.format(log)
	
	try:
		os.rename(arf, mp4)
	except Exception, e:
		print 'fail to rename {0} -> {1}. error: {2}'.format(arf, mp4, e)
		return

	print '\tSuccess! {0} -> {1}\n'.format(tmp, mp4)


def separateMp4ToMp3(tmp):
	mp4 = tmp.replace('.tmp', '.mp4')
	print('---> Separate the video clip {0}'.format(mp4))

	mp3 = tmp.replace('.tmp', '.mp3')
	if os.path.exists(mp3):
		print '\n\t{0} is detected. Skip. \n\tPlease delete .mp3 file if you need re-separate.'.format(mp3)
		return

	cmd = 'ffmpeg -i {0} -f mp3 -vn -loglevel fatal {1}'.format(mp4, mp3)
	print '\t{0}'.format(cmd)

	x = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	
	for log in x.stdout.readlines():
		print '[ffmpeg info] {0}'.format(log)
	for log in x.stderr.readlines():
		print '[ffmpeg error] {0}'.format(log)

	print '\tSuccess! {0} -> {1}\n'.format(mp4, mp3)


def composeMp3ToMp3(arr = []):
	if len(arr) <=0 :
		print('--->Operate audio array is empty!')
		return
	
	thisDir = os.path.dirname(arr[0])
	if (os.path.exists(thisDir + "/composeAudio.mp3")):
		print('--->{0}/composeAudio.mp3 is exist, if you need re-gennerate,Please delete it!'.format(thisDir))
		return
		
	print('---> Compose the audio :')
	var = ''
	for tem in arr:
		if os.path.exists(tem) == False:
			print '\n\t{0} is not exist! \n\tPlease make sure audio file be exist if you need compose.'.format(tem)
			return
		var = var + " -i " + tem
		
	if var == '':
		print '\n\t{0} is empty. \n\tPlease check .mp3 file if you need compose.'.format(var)
		return
		
	cmd = 'ffmpeg {0} -filter_complex amix=inputs=2:duration=first:dropout_transition=2 -f mp3 -loglevel fatal {1}/composeAudio.mp3'.format(var, thisDir)
	print '\t{0}'.format(cmd)
	x = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	
	for log in x.stdout.readlines():
		print '[ffmpeg info] {0}'.format(log)
	for log in x.stderr.readlines():
		print '[ffmpeg error] {0}'.format(log)

	print '\tSuccess! {0} -> {1}\n'.format(var, thisDir + "/composeAudio.mp3")


#deal with video:
def composeMp4ToMp4(arr = []):
	if len(arr) <= 0:
		print('--->Operate video array is empty!')
		return
	
	thisDir = os.path.dirname(arr[0])
	if (os.path.exists(thisDir + "/composeVideo.mp4")):
		print('--->{0}/composeVideo.mp4 is exist, if you need re-gennerate,Please delete it!'.format(thisDir))
		return
	
	print('---> Compose the video :')
	var = ''
	for tem in arr:
		if os.path.exists(tem) == False:
			print'\n\t{0} is not exist! \n\tPlease make sure video file be exist if you need compose.'.format(tem)
			return
		
		var = var + " -i " + tem
	
	if var == '':
		print '\n\t{0} is empty. \n\tPlease check video file if you need compose.'.format(var)
		return
	
	cmd = 'ffmpeg ' + var + ' -filter_complex "[1:v]scale=w=176:h=144:force_original_aspect_ratio=decrease[ckout];[0:v]' \
		  '[ckout]overlay=x=W-w-10:y=10[out]" -map "[out]" -movflags faststart -loglevel fatal ' + thisDir + '/composeVideo.mp4'.format(var, thisDir)
	print '\t{0}'.format(cmd)
	x = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	
	for log in x.stdout.readlines():
		print '[ffmpeg info] {0}'.format(log)
	for log in x.stderr.readlines():
		print '[ffmpeg error] {0}'.format(log)
	
	print '\tSuccess!\n {0} -> {1}\n'.format(var, thisDir + "/composeVideo.mp4")


def communicateAudioVideo(folder):
	if (os.path.exists(folder + "/communicateVideo.mp4")):
		print('--->{0}/communicateVideo.mp4 is exist, if you need re-gennerate,Please delete it!'.format(folder))
		return
	
	if ((os.path.exists(folder + "/composeVideo.mp4") == False) or
			(os.path.exists(folder + "/composeAudio.mp3") == False)):
		print('--->{0}/composeVideo.mp4  or composeAudio.mp3 must be exist!'.format(folder))
		return
	
	print('---> Communicate the video :')
	cmd = 'ffmpeg -i ' + folder + '/composeVideo.mp4 -i ' + folder + '/composeAudio.mp3 -f mp4 ' \
			' -loglevel fatal ' + folder +'/communicateVideo.mp4'
	print '\t{0}'.format(cmd)
	x = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	
	for log in x.stdout.readlines():
		print '[ffmpeg info] {0}'.format(log)
	for log in x.stderr.readlines():
		print '[ffmpeg error] {0}'.format(log)
	
	print '\tSuccess!\n {0}  and {1} -> {2}\n'.format(folder + '/composeVideo.mp4', folder + '/composeAudio.mp3', folder +'/communicateVideo.mp4')
	

#handle chennel:
def transcodeThisChannel(folder):
	print('''
    +---------------------------------------------------------------------
    | Channel {0}
    | Time @{1}
    +---------------------------------------------------------------------
	'''.format(folder, nowString()))
	
	recordingStatus = '{0}recording-done.txt'.format(folder)
	if os.path.exists(recordingStatus) == False:
		print '\n\tWarning: No {0}. Recording files are not ready. Skip'.format(recordingStatus)
		return
	
	composeFile = '{0}/compose-run.txt'.format(folder)
	if os.path.exists(composeFile) == True:
		print '\n\tWarning: video of channel {0} has been handle. Skip'.format(folder)
		return

	#step 1:
	ft = open("{0}compose-run.txt".format(folder), "w+")
	ft.close()
	files = listFilePath(folder, isDir=False, endswith='.tmp')
	for f in files:
		transcodeThisClip(f)
		separateMp4ToMp3(f)

	
	#step 2:
	files = listFilePath(folder, isDir=False, endswith='.mp3')
	composeMp3ToMp3(files)

	#step 3:
	files = listFilePath(folder, isDir=False, endswith='.mp4')
	composeMp4ToMp4(files)
	
	
	#step 4:
	communicateAudioVideo(folder)
	

def main():
	if len(sys.argv) != 2:
		print "\n\t Usage: python agora_video_record.py RECORDING_FILE_ROOT_PATH\n"
		return

	if isffmpegReady() == False:
		print "\n\t Error: fail to find ffmpeg by cmd 'which ffmpeg'.\n"

	allDates = listFolderByDate(sys.argv[1], 1)
	for folder in allDates:
		
		if os.path.isdir(folder) == False:
			print "\n\t Warn: {0} is not exist'.\n".format(folder)
			continue
		
		allChannels = listFilePath(folder, isDir=True)
		
		for channel in allChannels:
			transcodeThisChannel(channel)
		

if __name__ == '__main__':
	main()
