from tkinter import *
import os
import shutil
import random
import ctypes
from PIL import Image
from tkinter import filedialog, font
from PIL import Image, ImageTk
import tkinter as tk
import webbrowser
import sys


def select_files_by_orientation():
    source = source_path.get()
    num_files = int(num_files_to_select.get())
    destination = destination_path.get()
    orientation = orientation_option.get()
    extensions = ['.jpeg', '.png', '.gif', '.bmp', '.tiff', '.psd', '.ai', '.svg', '.eps', '.raw', '.pdf', '.jpg', '.ico', '.wmf', '.emf', '.exr', '.tga', '.webp', '.nef', '.cr2']
    files = []
    for root, _, files_list in os.walk(source):
        for file in files_list:
            if os.path.splitext(file)[1].lower() in extensions:
                files.append(os.path.join(root, file))
    if not files:
        MessageBox = ctypes.windll.user32.MessageBoxW
        MessageBox(None, 'No valid files found in the source folder', 'Error :(', 0x40000)
        return
    selected_files = []
    for file in files:
        img = Image.open(file)
        width = img.width
        height = img.height
        if orientation == 'horizontal' and width >= height:
            selected_files.append(file)
        elif orientation == 'vertical' and width < height:
            selected_files.append(file)
        elif orientation == 'any':
            selected_files.append(file)
        img.close()
    if len(selected_files) < num_files:
        MessageBox = ctypes.windll.user32.MessageBoxW
        MessageBox(None, 'There are not enough photos in that orientation in that folder...', 'Error :(', 0x40000)
        return
    selected_files = random.sample(selected_files, num_files)
    for file in selected_files:
        shutil.copy(file, destination)
    if move_copied_files.get() == 1 and move_to_path.get():
        for file in selected_files:
            shutil.move(file, move_to_path.get())
    MessageBox = ctypes.windll.user32.MessageBoxW
    MessageBox(None, f'{num_files} photos with the selected orientation have been randomly chosen', 'Done :)', 0x40000)


def get_path(filename):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, filename)
    else:
        return filename






def open_source_folder():
    source_path.delete(0, END)
    source = filedialog.askdirectory()
    source_path.insert(0, source)


def open_destination_folder():
    destination_path.delete(0, END)
    destination = filedialog.askdirectory()
    destination_path.insert(0, destination)


def open_move_to_folder():
    move_to_path.delete(0, END)
    move_to = filedialog.askdirectory()
    move_to_path.insert(0, move_to)


def start_program():

    select_files_by_orientation()


root = Tk()
root.withdraw()
root.title('Randomik')

# icon_path = os.path.join(os.getcwd(), "favicon2.ico")
root.iconbitmap(get_path('favicon2.ico'))
myFont = font.Font(family='Arial', size=18, weight='bold')
myFont2 = font.Font(family='Arial', size=10, weight='bold')
myFont3 = font.Font(family='Arial', size=10, weight='bold', slant='italic')
myFont4 = font.Font(family='Arial Black', size=10, weight='bold')

num_files_to_select_label = Label(root, text='Enter the number of photos \nyou want to randomly select:', font=myFont2)
num_files_to_select_label.pack()
num_files_to_select = Entry(root, width=10)
num_files_to_select.pack()
num_files_to_select.insert(END, "1")

source_path_label = Label(root, text='Enter the path of the source folder, \nor select it',font=myFont2)
source_path_label.pack(pady=3)
source_path = Entry(root,width=40)
source_path.pack()


source_button = Button(root, text='Browse', command=open_source_folder, bg='#A9A9A9', font=myFont2)
source_button.pack(pady=5)

destination_path_label = Label(root, text='Enter the path of the destination folder,\n or select it',font=myFont2)
destination_path_label.pack(pady=3)
destination_path = Entry(root,width=40)
destination_path.pack()


includeSubfolders = IntVar()
includeSubfoldersCheckbox = Checkbutton(root, text='Include files in subfolders', variable=includeSubfolders, font=myFont3)
includeSubfoldersCheckbox.pack()

destination_button = Button(root, text='Browse', command=open_destination_folder, bg='#A9A9A9', font=myFont2)
destination_button.pack()

orientation_label = Label(root, text='Select the orientation of the photo:',font=myFont3, pady=10)
orientation_label.pack()
orientation_option = StringVar(root)
orientation_option.set('any')
any_radio = Radiobutton(root, text="Doesn't matter", variable=orientation_option, value='any', font=myFont2)
any_radio.pack()
horizontal_radio = Radiobutton(root, text='Horizontal', variable=orientation_option, value='horizontal', font=myFont2)
horizontal_radio.pack()
vertical_radio = Radiobutton(root, text='Vertical', variable=orientation_option, value='vertical',font=myFont2)
vertical_radio.pack()


move_copied_files = IntVar()
move_checkbox = Checkbutton(root, text='Remove the copied photos \nfrom the original location', variable=move_copied_files, font=myFont4)
move_checkbox.pack()


move_to_path_label = Label(root, text='And move them to:', font=myFont2)
move_to_path_label.pack()
move_to_path = Entry(root,width=40)
move_to_path.pack()



move_to_button = Button(root, text='Browse', command=open_move_to_folder,bg='#A9A9A9', font=myFont2)
move_to_button.pack(pady=5)


start_button = Button(root, text='Start', command=start_program, bd=3, font=myFont, bg='#A9A9A9' )
start_button.pack(side="bottom", fill=BOTH, expand=True, padx=20, pady=50)

root.geometry("300x650")
root.resizable(width=False, height=False)
root.eval('tk::PlaceWindow . center')
img_path = os.path.join(os.getcwd(), "created.png")
created = Image.open(get_path('created.png'))
created.thumbnail((200, 200))  # Create a new image with maximum size of 200x200
photo = ImageTk.PhotoImage(created)
button = tk.Label(root, image=photo, borderwidth=4)

button = tk.Label(root, image=photo, borderwidth=4, highlightthickness=4)
button.bind("<Button-1>", lambda event: webbrowser.open("https://github.com/nyorbee"))
# Set the position and size of the button
button.place(relx=0.5, rely=1.0, anchor="s", width=created.width+20, height=created.height+20)



root.mainloop()








