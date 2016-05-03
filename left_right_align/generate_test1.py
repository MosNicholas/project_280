# specify filenames of parts one per line

import argparse
import os
import random
import csv
import h5py
import numpy as np
from random import randint

parser = argparse.ArgumentParser(
  description='Generate the train and test LMDB for the left / right dataset. \
  This assumes all segments have ten left and ten right files. All ten frames \
  will be stacked in the channel dimension, then right will be stacked on \
  left likewise. Test gets 1000 segments and train gets the rest.')
parser.add_argument('--target_folder', default='/mnt/data/test1',
  help='The parent directory for the dataset.')
parser.add_argument('--num_to_process', default=False,
	help='How many of the provided segments to process.')
args = parser.parse_args()

def rgb2gray(rgb):
	return np.dot(rgb[...,:3], [0.299, 0.587, 0.114])


def main():
	num_segments_out = 20000 

	if not os.path.isdir(args.target_folder):
		os.mkdir(args.target_folder)

	test_inds_csv_path = os.path.join(args.target_folder, 'test_inds.csv')
	test_inds = random.sample(segment_inds, num_source_frames/10)
	with open(test_inds_csv_path, 'w') as test_inds_csv:
		w = csv.writer(test_inds_csv)
		test_inds_to_write = [[ind] for ind in test_inds]
		w.writerows(test_inds_to_write)
	offsets = np.ones((1, num_segments_out))
	offsets[::2] = 0
	np.savetxt(os.path.join(args.target_folder, 'offsets_bin.csv'), offsets, fmt="%i")

	in_train = np.array([True] * num_source_frames)
	in_train[test_inds] = False

	# Setup list of h5 filenames
	filenames_train = []
	filenames_test = []
	filenames_train_path = os.path.join(args.target_folder, 'examples_train.txt')
	filenames_test_path = os.path.join(args.target_folder, 'examples_test.txt')
	try:
		os.remove(filenames_train_path)
		os.remove(filenames_test_path)
	except OSError:
		pass

	full_file_path = ''

	seg1_ind = 0 # no offset
	seg2_ind = 1 # offset

	resume_from = 0 if not args.resume_from else args.resume_from

	base_asc = [float(num)/10 for num in range(0, 11)]
	asc = np.array(base_asc).reshape((1, 1, 10, 1, 1)).tile((1, 1, 1, 96, 64))

	for frame_ind in xrange(num_segments_out):

		if frame_ind % 2 == 0:
			assert offsets[seg1_ind] == 0
			assert offsets[seg2_ind] > 0
			offset = offsets[seg2_ind]

			h5_filename1 = 'seg-{:06d}.h5'.format(seg1_ind)
			h5_filename2 = 'seg-{:06d}.h5'.format(seg2_ind)
			h5_location1 = os.path.join(args.target_folder, h5_filename1)
			h5_location2 = os.path.join(args.target_folder, h5_filename2)

			#print(np.shape(curr_left_frames))
			stacked_left = np.zeros((1, 1, 10, 96, 64))
			#print(np.shape(curr_left_frames))
			#print(np.shape(curr_left_frames[:20:2,:,:]))
			#print(np.shape(stacked_left[0, :, :, :]))
			min_frame = np.randint(255)
			max_frame = np.randint(min_frame + 1, 256)
			stacked_left = asc * (max_frame - min_frame) + min_frame
			stacked_right = stacked_left
			min_frame = np.randint(255)
			max_frame = np.randint(min_frame + 1, 256)
			stacked_offset = asc * (max_frame - min_frame) + min_frame

			stacked_left *= 1.0/255
			stacked_right *= 1.0/255
			stacked_offset *= 1.0/255

			with h5py.File(h5_location1, 'w') as f:
				f['left'] = stacked_left
				f['right'] = stacked_right
				label_mat = np.zeros((1, 1, 1, 1))
				label_mat[0, 0, 0, 0] = offsets[seg1_ind]
				f['label'] = label_mat
				label_mat_bin = np.zeros((1, 1, 1, 1))
				label_mat_bin[0, 0, 0, 0] = offsets_bin[seg1_ind]
				f['label_bin'] = label_mat_bin
				#print("Writing to " + h5_location1)

			if in_train[seg1_ind]:
				filenames_train.append(h5_location1)
			else:
				filenames_test.append(h5_location1)

			with h5py.File(h5_location2, 'w') as f:
				if offset_left:
					f['left'] = stacked_offset
					f['right'] = stacked_right
				else:
					f['left'] = stacked_left
					f['right'] = stacked_offset
				label_mat = np.zeros((1, 1, 1, 1))
				label_mat[0, 0, 0, 0] = offsets[seg2_ind]
				f['label'] = label_mat
				label_mat_bin = np.zeros((1, 1, 1, 1))
				label_mat_bin[0, 0, 0, 0] = offsets_bin[seg2_ind]
				f['label_bin'] = label_mat_bin

			if in_train[seg2_ind]:
				filenames_train.append(h5_location2)
			else:
				filenames_test.append(h5_location2)

			if seg1_ind % 100 == 0 or seg2_ind % 100 == 0 or frame_ind == num_segments_out - 1:
				print str(seg2_ind) + ' segments processed...'
				with open(filenames_train_path, 'a') as f:
					for filename_train in filenames_train:
						f.write(filename_train + '\n')
				with open(filenames_test_path, 'a') as f:
					for filename_test in filenames_test:
						f.write(filename_test + '\n')
				filenames_train = []
				filenames_test = []
			seg1_ind += 2
			seg2_ind += 2
	with h5py.File(os.path.join(args.target_folder, 'seg-000000.h5'), 'r') as f:
		print 'Final datum written: '
		print f['left']
		print f['right']
		print f['label']

main()