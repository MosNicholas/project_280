
import os
import csv
import lmdb
import h5py
import shutil
import argparse
import subprocess
import numpy as np
import multiprocessing
from scipy.ndimage import imread
from moviepy.editor import VideoFileClip, AudioFileClip

try:
  import caffe
except ImportError, e:
  print 'No caffe module found, caffe not imported'

TRUMP_ID = 'RDrfE9I8_hs'
MOVIE_ID = 'XIeFKTbg3Aw'
DATA_FOLDER = 'data'
RAW_VIDEO_FOLDER = os.path.join(DATA_FOLDER, 'raw')
CLIPPED_VIDEO_FOLDER = os.path.join(DATA_FOLDER, 'clipped')

# For the movie
movie_path = os.path.join(RAW_VIDEO_FOLDER, 'hitch_hiker.mp4')
outfolder = os.path.join(CLIPPED_VIDEO_FOLDER, 'hitch_hiker')

# command line arguments
parser = argparse.ArgumentParser(description="""Generate the train 
  and test dataset for video alignment problems""")
parser.add_argument('--data_source', default=outfolder,
  help='The directory for the dataset.')
parser.add_argument('--target_folder', default=outfolder,
  help='The directory for the function output.')
args = parser.parse_args()

def greyscale(image):
  return np.dot(image[:, :, :3], [0.299, 0.587, 0.114])

def create_millisecond_subtitles(outfile):
  with open(os.path.join(RAW_VIDEO_FOLDER, outfile.replace('mp4', 'srt')), 'w') as subs:
    for i in xrange(1, 3 * 60 * 100):
      subs.write(str(i))
      time = 1 + i * 10
      subs.write("\n")
      seconds = (time / 1000) % 60
      minutes = (time / 60000) % 60
      currTime = "00:%02d:%02d,%03d" % (minutes, seconds, time % 1000)
      nextMillisecond = time % 1000 + 10
      if (nextMillisecond > 1000):
        nextMillisecond = 1
        seconds += 1
        minutes += seconds/60
        seconds = seconds % 60
      nextTime = "00:%02d:%02d,%03d" % (minutes, seconds, nextMillisecond)
      subs.write("%s --> %s" %(currTime, nextTime))
      subs.write("\n")
      subs.write("time: " + currTime)
      subs.write("\n")
      subs.write("\n")
  return True

def download_raw_youtube_video(youtube_id, target_folder, outfile_name, create_subtitles=False):
  command = 'youtube-dl %s -o %s' % (youtube_id, outfile_name)
  if subprocess.call(command, shell=True) == 0:
    if create_subtitles: create_millisecond_subtitles(outfile_name)
    if not os.path.isdir(target_folder): os.makedirs(target_folder)
    shutil.move(outfile_name, target_folder)
  else:
    return False
  return True

def create_trump_dataset(movie_path, target_folder):
  # To write video to file: clip.write_videofile(outfile, codec='libx264', audio_codec='aac', temp_audiofile='china-%02d.m4a' % i, remove_temp=True)
  # moviepy help: http://zulko.github.io/blog/2014/06/21/some-more-videogreping-with-python/ 
  #               https://zulko.github.io/moviepy/ref/ref.html
  cuts = [(1.7, 2.5), (4.2, 4.6), (4.7, 5.2), (5.35, 5.93), (5.95, 6.45), (6.45, 6.95), (7, 7.34), (7.38, 7.82), (7.85, 8.24), (8.44, 9.04), (9.43, 9.7), (16.44, 16.7), (16.77, 17), (17, 17.31), (17.39, 17.67), (17.9, 18), (18.56, 18.8), (19, 19.4), (19.41, 19.75), (19.78, 20), (20.75, 21), (21, 21.52), (21.9, 22.41), (23, 23.52), (23.7, 23.96), (24.4, 24.7), (24.73, 24.98), (25, 25.38), (26.63, 27.15), (30, 30.36), (31.3, 31.77), (31.9, 32.16), (32.2, 32.5), (32.9, 33.16), (33.23, 33.4), (33.47, 33.79), (33.81, 34.25), (34.3, 34.65), (34.75, 35.23), (35.27, 35.95), (36.03, 36.59), (36.63, 37.04), (38.66, 39.1), (39.85, 40.3), (40.4, 40.75), (40.83, 41.271), (41.59, 41.95), (42.96, 43.33), (43.58, 43.88), (44, 44.6), (47, 47.48), (50.45, 50.75), (51, 51.33), (52.15, 52.48), (58.3, 58.55), (59, 59.4), (60, 60.4), (61.35, 61.71), (62.44, 62.8), (64.3, 64.6), (65.15, 65.58), (67.45, 67.8), (68.8, 69.15), (69.27, 69.6), (70.63, 70.97), (71, 71.4), (72.35, 72.8), (73.3, 73.7), (74.2, 74.61), (76, 76.9), (80.3, 80.65), (81.1, 81.4), (82.4, 82.75), (83.52, 84), (84.14, 84.49), (85.3, 85.6), (86.1, 86.4), (86.8, 87), (87.1, 87.48), (88, 88.2), (88.9, 89.37), (90.3, 90.7), (90.9, 91.2), (91.3, 91.5), (91.55, 91.78), (91.79, 92.06), (92.33, 92.67), (93.3, 93.55), (94.2, 94.5), (96.6, 96.96), (98, 98.44), (98.9, 99.1), (99.14, 99.53), (100.68, 100.92), (100.93, 101.25), (101.45, 101.8), (102.7, 102.96), (103.7, 104), (105.2, 105.7), (105.88, 106.1), (106.2, 106.6), (106.65, 107), (107.05, 107.85), (108.57, 109), (109.1, 109.48), (110.24, 110.74), (113.5, 113.85), (115.12, 115.4), (115.8, 116.25), (116.56, 116.95), (117.95, 118.35), (118.9, 119.3), (119.6, 120.2), (120.4, 120.9), (121.48, 121.9), (122.95, 123.25), (124.25, 124.65), (125, 125.39), (129.58, 129.9), (130.9, 131.3), (131.8, 132.15), (135, 135.5), (135.75, 136.1), (136.2, 136.65), (137, 137.4), (138.55, 138.8), (145.3, 145.75), (152.1, 152.5), (154.8, 155.25), (156.68, 156.95), (157.3, 157.8), (159.4, 159.78), (159.8, 160), (160.46, 160.8), (162.6, 163), (163.9, 164.18), (164.25, 164.63), (164.64, 165.1), (165.33, 165.7), (165.73, 166.1), (166.28, 166.58), (166.6, 167.06), (167.27, 167.65), (167.69, 168), (168.05, 168.45), (168.93, 169.25), (169.28, 169.6), (169.7, 170.15), (171.82, 172.24), (172.8, 173.1), (173.2, 173.6), (174.6, 175.04), (175.2, 175.6), (177, 177.35), (178.55, 178.97)]
  video = VideoFileClip(movie_path)
  subclips = [video.subclip(start, end) for (start, end) in cuts]
  for i in xrange(len(subclips)):
    clip = subclips[i]
    video_outfile = os.path.join(target_folder, 'video', 'china-%03d.mp4' % i)
    audio_outfile = os.path.join(target_folder, 'audio', 'china-%03d.m4a' % i)
    clip.write_videofile(video_outfile, codec='libx264', audio=False)
    clip.audio.write_audiofile(audio_outfile, codec='aac')
  return True

def create_movie_process(video, target_folder, start_i, end_i, first_i, pnum, saved_frames):
  video_path = os.path.join(target_folder, 'frame-%06d.jpg')
  for i in xrange(start_i, end_i):
    shifted = i - first_i
    if shifted in saved_frames: continue
    video.save_frame(video_path % shifted, i)
    if (shifted % 500 == 0): print '%d frames saved on process %d' % (i - start_i, pnum)
  print 'process %d completed' % pnum

def create_movie_dataset(movie_path, target_folder):
  if not os.path.isdir(target_folder): os.makedirs(target_folder)
  video = VideoFileClip(movie_path)
  num_frames = int(video.fps * video.duration)
  video = video.set_fps(1).set_duration(num_frames).resize(0.5)
  first_frame = 650
  num_cpus = multiprocessing.cpu_count()

  saved_frames = set(map(lambda x: int(x) if x else 0, map(lambda f: ''.join(x for x in f if x.isdigit()), os.listdir(target_folder))))
  num_done = len(saved_frames)
  if num_done == 0:
    offsets = np.random.randint(0, 10, num_frames - first_frame - 9)
    offset_file = os.path.join(target_folder, 'offsets.npz')
    np.savez_compressed(offset_file, offsets=offsets)

  frames_per_process = (num_frames - first_frame) / num_cpus
  for i in xrange(num_cpus):
    start_i = i * frames_per_process + first_frame
    end_i = num_frames if i == num_cpus - 1 else start_i + frames_per_process
    print start_i, end_i
    multiprocessing.Process(
      target=create_movie_process,
      args=(video, target_folder, start_i, end_i, first_frame, i, saved_frames)
    ).start()

  return True

def load_single_datum_into_lmdb(frames_train_path, labels_train_path, frames_test_path, labels_test_path, shape, offsets, train_values, frame_paths, offset_start, offset_end, pnum):
  stacked = np.zeros((shape[0], shape[1], 20))
  prev_stacked = np.zeros((shape[0], shape[1], 9))

  for i in xrange(9):
    prev_stacked[:, :, i] = greyscale(imread(frame_paths % (i + offset_start)))

  frames_train = lmdb.open(frames_train_path, map_size=int(1e12))
  labels_train = lmdb.open(labels_train_path, map_size=int(1e12))
  frames_test = lmdb.open(frames_test_path, map_size=int(1e12))
  labels_test = lmdb.open(labels_test_path, map_size=int(1e12))

  with frames_train.begin(write=True, buffers=True) as frames_train_writer, \
    labels_train.begin(write=True, buffers=True) as labels_train_writer, \
    frames_test.begin(write=True, buffers=True) as frames_test_writer, \
    labels_test.begin(write=True, buffers=True) as labels_test_writer:

    for split in xrange(offset_start, offset_end):
      stacked[:, :, 10:] = 0
      shifted = split - offset_start
      db_entry_title = str(split)
      stacked[:, :, :9] = prev_stacked
      stacked[:, :, 9] = greyscale(imread(frame_paths % (split + 9)))
      prev_stacked = stacked[:, :, 1:10]
      stacked[:, :, 10:] = stacked[:, :, offsets[shifted] - 1:9 + offsets[shifted]]
      stacked_data = caffe.io.array_to_datum(stacked)

      if train_values[shifted]:
        frames_train_writer.put(db_entry_title, stacked_data.SerializeToString())
        labels_train_writer.put(db_entry_title, str(offsets[shifted]))
      else:
        frames_test_writer.put(db_entry_title, stacked_data.SerializeToString())
        labels_test_writer.put(db_entry_title, str(offsets[shifted]))

      if shifted % 500 == 0:
        print '%s splits processed on process %d' % (shifted, pnum)

  print 'process %d completed' % pnum

  frames_train.close()
  labels_train.close()
  frames_test.close()
  labels_test.close()

def load_data_into_lmdb(data_source_folder, target_folder):
  offset_file_path = os.path.join(data_source_folder, 'offsets.npz')
  if not os.path.isdir(target_folder): os.makedirs(target_folder)
  train_test_file = os.path.join(target_folder, 'train_test_indices.npz')

  offsets = np.load(offset_file_path)['offsets']
  num_splits = len(offsets)

  if os.path.isfile(train_test_file):
    train = np.load(train_test_file)['train']
  else:
    train = np.ones((num_splits), dtype=bool)
    train[np.random.randint(0, num_splits, 1000)] = False
    np.savez_compressed(train_test_file, train=train)

  video_title = 'frame-%06d.jpg'
  frame_paths = os.path.join(data_source_folder, video_title)
  frame_shape = imread(frame_paths % 1).shape

  num_cpus = multiprocessing.cpu_count()

  indices_per_cpu = num_splits / num_cpus
  for i in xrange(num_cpus):
    offset_start = i * indices_per_cpu
    offset_end = num_splits if i == num_cpus - 1 else (i + 1) * indices_per_cpu
    multiprocessing.Process(target=load_single_datum_into_lmdb, args=(
      os.path.join(target_folder, 'frames_train_%d' % i),
      os.path.join(target_folder, 'labels_train_%d' % i),
      os.path.join(target_folder, 'frames_test_%d' % i),
      os.path.join(target_folder, 'labels_test_%d' % i),
      frame_shape, offsets[offset_start:offset_end], train[offset_start:offset_end],
      frame_paths, offset_start, offset_end, i
    )).start()

def load_data_hdf5_process(frame_paths, target_folder, shape, offsets, offset_start, offset_end, saved_files, pnum):
  stacked = np.zeros((1, 20, shape[0], shape[1]))
  prev_stacked = np.zeros((9, shape[0], shape[1]))

  for i in xrange(9):
    prev_stacked[i, :, :] = greyscale(imread(frame_paths % (i + offset_start)))
    prev_stacked[i, :, :] = prev_stacked[i, :, :]/prev_stacked[i, :, :].max()

  for split in xrange(offset_start, offset_end):
    if split in saved_files: continue
    shifted = split - offset_start
    stacked[0, 10:, :, :] = 0
    stacked[0, :9, :, :] = prev_stacked
    stacked[0, 9, :, :] = greyscale(imread(frame_paths % (split + 9)))
    stacked[0, 9, :, :] = stacked[0, 9, :, :]/stacked[0, 9, :, :].max()
    prev_stacked = stacked[0, 1:10, :, :]
    stacked[0, 10:, :, :] = stacked[0, offsets[shifted] - 1:9 + offsets[shifted], :, :]

    outfile = target_folder % split

    with h5py.File(outfile, 'w') as f:
      f.create_dataset(
        'left', data=stacked[:, :10, :, :],
        compression='gzip', compression_opts=1
      )
      f.create_dataset(
        'right', data=stacked[:, 10:, :, :],
        compression='gzip', compression_opts=1
      )
      label = np.zeros((1, 1, 1, 1))
      label[0, 0, 0, 0] = offsets[shifted]
      f.create_dataset(
        'label', data=label,
        compression='gzip', compression_opts=1
      )

    if shifted % 500 == 0:
      print '%s splits processed on process %d' % (shifted, pnum)

  print 'process %d completed' % pnum

def load_data_into_hdf5(data_source_folder, target_folder):
  offset_file_path = os.path.join(data_source_folder, 'offsets.npz')
  if not os.path.isdir(target_folder): os.makedirs(target_folder)
  train_test_file = os.path.join(target_folder, 'train_test_indices.npz')
  training_examples = os.path.join(target_folder, 'training_examples.txt')
  test_examples =  os.path.join(target_folder, 'test_examples.txt')
  h5_output_dir = os.path.join(target_folder, 'frame-%06d.h5')

  offsets = np.load(offset_file_path)['offsets']
  num_splits = len(offsets)
  saved_files = set(map(lambda x: int(x.split('.')[0].split('-')[1]) if x.endswith('.h5') else 0, os.listdir(target_folder)))

  if os.path.isfile(train_test_file):
    train = np.load(train_test_file)['train']
  else:
    train = np.ones((num_splits), dtype=bool)
    train[np.random.randint(0, num_splits, int(num_splits * 0.2))] = False
    np.savez_compressed(train_test_file, train=train)
    np.savetxt(training_examples, map(lambda x: h5_output_dir % x, np.where(train==True)[0]), fmt="%s")
    np.savetxt(test_examples, map(lambda x: h5_output_dir % x, np.where(train==False)[0]), fmt="%s")

  video_title = 'frame-%06d.jpg'
  frame_paths = os.path.join(data_source_folder, video_title)
  frame_shape = imread(frame_paths % 1).shape

  num_cpus = multiprocessing.cpu_count()
  indices_per_cpu = num_splits / num_cpus
  for i in xrange(num_cpus):
    offset_start = i * indices_per_cpu
    offset_end = num_splits if i == num_cpus - 1 else (i + 1) * indices_per_cpu
    multiprocessing.Process(target=load_data_hdf5_process, args=(
      frame_paths, h5_output_dir, frame_shape,
      offsets[offset_start:offset_end], offset_start, offset_end,
      saved_files, i
    )).start()
    
def download_trump():
  return download_raw_youtube_video(TRUMP_ID, args.target_folder, 'china.mp4', True)

def download_movie():
  return download_raw_youtube_video(MOVIE_ID, args.target_folder, 'hitch_hiker.mp4')

if __name__ == '__main__':
  # Pipeline: Download movie -> create dataset -> load into lmdb
  # download_movie()
  # create_movie_dataset(args.data_source, args.target_folder)
  load_data_into_hdf5(args.data_source, args.target_folder)
