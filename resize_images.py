import os, PySimpleGUI as sg, math
from PIL import Image

# this script runs a simple GUI for rapidly cropping many images into squares

input_dir = "original_pics"
png_dir = "png_pics" # PySimpleGUI needs pics as pngs to view them
output_dir = "cropped_pics"

if not os.path.exists(png_dir):
    os.mkdir(png_dir)
if not os.path.exists(output_dir):
    os.mkdir(output_dir)

def convert_to_png(replace_pngs=False, pix_area=300000):
    # take all photos in input_dir and save them as pngs in png_dir, resizes photos
    # to have a maximum pixel area of pix_area, will replace existing converted pngs
    # if replace_pngs is True, otherwise, will only deal with new files
    for path in os.listdir(input_dir):
        name, _ = os.path.splitext(path)
        if replace_pngs or not os.path.exists(os.path.join(png_dir, name+".png")):
            print("processing", path)
            im = Image.open(os.path.join(input_dir,path))
            factor = im.size[0]*im.size[1] / pix_area
            if factor > 1:
                new_dims = (int(im.size[0]/math.sqrt(factor)), int(im.size[1]/math.sqrt(factor)))
                im = im.resize(new_dims)
            im.save(os.path.join(png_dir, name+".png"))
            im.close()

convert_to_png()

def get_file_paths(redo_crop=False):
    # returns a list of png file paths that have not yet been cropped, or all png 
    # file paths in png_dir if redo_crop=True
    input_img_paths = []
    for path in os.listdir(png_dir):
        if redo_crop or not os.path.exists(os.path.join(output_dir, path)):
            input_img_paths.append(os.path.join(png_dir, path))
    return input_img_paths

input_img_paths = get_file_paths()
img_ind = 0

sg.theme("BluePurple")
progress_text = sg.Text("{} of {}".format(img_ind, len(input_img_paths)), size=(10,1))
view_size = 600
img_view = sg.Graph((view_size,view_size), (0,view_size), (view_size,0), 
                    enable_events=True, key="_GRAPH")
layout = [
    [progress_text],
    [img_view],
    [
        sg.Button("Ok"), 
        sg.Button("Rotate"),
        sg.Button("Clear"), 
        sg.Button("Skip"), 
        sg.Button("Help"), 
        sg.Button("Exit")
    ]
]

# set up window
window = sg.Window("Crop images", layout, return_keyboard_events=True)
window.finalize()
# add first image
img_handle = img_view.draw_image(input_img_paths[img_ind], location=(0,0))

im = Image.open(input_img_paths[img_ind])
upper_left, lower_right, guide_h, guide_v, guide_d, guide_r = None, None, None, None, None, None

def help_button():
    # provide some instruction on the controls
    text = '''Click on upper left corner of desired crop area first, then on lower right.
    Red line shows square area, will snap to closest point on that line for a square crop.
    Click "Ok" or 'a' to accept crop and move onto next photo, "Clear" or 'c' to unselect 
    points, "Skip" or 'q' to go to next photo without cropping, "Rotate" or 'r' to rotate
    90deg clockwise.'''
    print(text)

def clear_points():
    # remove clicked points
    global upper_left, lower_right
    upper_left, lower_right = None, None

def remove_guides():
    # remove any guide lines
    img_view.delete_figure(guide_d)
    img_view.delete_figure(guide_h)
    img_view.delete_figure(guide_v)
    img_view.delete_figure(guide_r)

def next_image():
    # display next image
    global img_ind, im, img_view, img_handle
    img_ind += 1
    im.close()
    im = Image.open(input_img_paths[img_ind])
    img_view.delete_figure(img_handle)
    img_handle = img_view.draw_image(filename=input_img_paths[img_ind], location=(0,0))
    progress_text.expand(expand_x=True)
    s = str(img_ind) + " of " + str(len(input_img_paths))
    print(s, type(s))
    progress_text.update(value=s)

def skip_image():
    # skip image without cropping
    # TODO add delete option or move out of folder
    next_image()
    clear_points()
    remove_guides()

def rotate_image():
    # rotate and save image
    global im, img_handle, img_view
    im = im.rotate(90, expand=True)
    im.save(input_img_paths[img_ind])
    remove_guides()
    clear_points()
    img_view.delete_figure(img_handle)
    img_handle = img_view.draw_image(filename=input_img_paths[img_ind], location=(0,0))

def add_point(click):
    # choose either upper_left or lower_right of cropped box
    global upper_left, lower_right, img_view, guide_d, guide_h, guide_r, guide_v
    if upper_left == None:
        upper_left = click
        guide_h = img_view.draw_line(click, (1000,click[1]), 'yellow')
        guide_v = img_view.draw_line(click, (click[0],1000), 'yellow')
        guide_d = img_view.draw_line(click, (click[0]+1000,click[1]+1000), "red")
    elif lower_right == None:
        remove_guides()
        y = (click[0] - upper_left[0] + click[1] + upper_left[1]) / 2
        lower_right = (y + upper_left[0] - upper_left[1], y)
        guide_r = img_view.draw_rectangle(upper_left, lower_right, line_color='yellow')

def save_crop():
    # save cropped photo to output_dir
    global im
    cropped_im = im.crop((*upper_left, *lower_right))
    name = input_img_paths[img_ind].split('\\')[-1]
    cropped_im.save(os.path.join(output_dir, name))
    cropped_im.close()
    clear_points()
    remove_guides()
    next_image()

# event loop
while True:
    event, values = window.read()
    if event in ("Exit", None):
        im.close()
        break
    elif event in ("Skip", "q"):
        skip_image()
    elif event == "Help":
        help_button()
    elif event in ("Clear", "c"):
        remove_guides()
        clear_points()
    elif event in ("Rotate", "r"):
        rotate_image()
    elif event == "_GRAPH":
        add_point(values['_GRAPH'])
    elif upper_left != None and lower_right != None and event in ("Ok", "a"):
        save_crop()


window.close()

