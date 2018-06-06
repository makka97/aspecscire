"""
utility to view spectrum in template color file
"""

import sys
import csv
import cv2
import argparse
import numpy as np

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('color_file', type=str, help="Path to input color file")
    parser.add_argument('--output_file', '-o', default=None, type=str, help="Path to output file denoting spectrum")
    parser.add_argument('-q', '--quiet', default=False, action='store_true', help="Run without displaying spectrum")
    return parser.parse_args()


def read_color_file(color_file_path):
    """
    Function to read the color file at the specified path
    Args:
        color_file_path: Path to color file to read
    """
    with open(color_file_path) as file_obj:
        row_list = []
        reader = csv.reader(file_obj, delimiter=' ')
        for row in reader:
            row_list.append([np.float(r)/255 for r in row[:3]])
        
        return row_list


def write_output_file(color_array, output_file_path):
    """
    Function to write the displayed color_array to the specified output file path
    Args:
        color_array: 3D Color array to write 
        output_file_path: Path to output image file
    """
    cv2.imwrite(output_file_path, color_array)


def create_color_array(color_list, width=50, length=480):
    """
    Function to create a 3D color array to display, given the list of Colors as [R, G, B] values
    Args:
        color_list: List of colors as RGB
        width: Width of column, for each color
        length: Length of column, for each color

    Returns:
        color_array: 3D numpy array of color as Image
    """
    n_colors = len(color_list)
    color_array = np.zeros((length, width * n_colors, 3))
    for i in range(n_colors):
        # Flipping order as OpenCV expects colors to be ordered as BGR
        color_array[:, i*width:(i+1)*width] = color_list[i][::-1]
    
    return color_array

def show_image(color_array):
    """
    Function to display image
    Args:
        color_array: Numpy array of image to display
    """
    cv2.imshow('Color-Spectrum', color_array)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def main(color_file, output_file, quiet):
    color_list = read_color_file(color_file)
    color_array = create_color_array(color_list)
    if not quiet:
        show_image(color_array)
    
    if output_file is not None:
        write_output_file(color_array, output_file)
    

if __name__ == "__main__":
    args = get_args()
    sys.exit(main(args.color_file, args.output_file, args.quiet))