import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from pytubefix import YouTube
import os

# Encoding setup
abc = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ://"
key = "passwordkevyn"
letters_to_value = {abc[i]: i for i in range(len(abc))}
value_to_letter = {v: k for k, v in letters_to_value.items()}
converted = [letters_to_value[char] for char in key]

CONFIG_FILE = "config.txt"
APP_VERSION = "1.0.0"

def encode_path(path):
    i = 0
    encoded = []
    for char in path:
        if char in letters_to_value:
            k = converted[i % len(converted)]
            sum = (letters_to_value[char] + k) % len(abc)
            encoded.append(value_to_letter[sum])
            i += 1
        else:
            encoded.append(char)
    return "".join(encoded)


def decode_path(encoded):
    i = 0
    decoded = []
    for char in encoded:
        if char in letters_to_value:
            k = converted[i % len(converted)]
            sum = (letters_to_value[char] - k) % len(abc)
            decoded.append(value_to_letter[sum])
            i += 1
        else:
            decoded.append(char)
    return "".join(decoded)


def save_config(video_path, audio_path, audio_quality, audio_ext):
    with open(CONFIG_FILE, "w") as f:
        f.write(encode_path(video_path) + "\n")
        f.write(encode_path(audio_path) + "\n")
        f.write(audio_quality + "\n")
        f.write(audio_ext + "\n")


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            lines = f.readlines()
            if len(lines) >= 4:
                try:
                    video_p = decode_path(lines[0].strip())
                    audio_p = decode_path(lines[1].strip())
                    quality = lines[2].strip()
                    ext = lines[3].strip()
                    return video_p, audio_p, quality, ext
                except Exception:
                    # fallback if decoding fails
                    return lines[0].strip(), lines[1].strip(), lines[2].strip(), lines[3].strip()
    cwd = os.getcwd()
    return cwd, cwd, "Highest", "mp3"


def browse_folder():
    folder = filedialog.askdirectory()
    if folder:
        folder_entry.delete(0, tk.END)
        folder_entry.insert(0, folder)
        save_config(folder_entry.get(), audio_folder_entry.get(), audio_quality_var.get(), audio_ext_var.get())


def browse_audio_folder():
    folder = filedialog.askdirectory()
    if folder:
        audio_folder_entry.delete(0, tk.END)
        audio_folder_entry.insert(0, folder)
        save_config(folder_entry.get(), audio_folder_entry.get(), audio_quality_var.get(), audio_ext_var.get())


def on_progress(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage = (bytes_downloaded / total_size) * 100
    progress_var.set(percentage)
    progress_bar.update()


def resolve_duplicate_path(folder, filename):
    base, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    while os.path.exists(os.path.join(folder, new_filename)):
        new_filename = f"{base} ({counter}){ext}"
        counter += 1
    return new_filename


def download_video():
    url = url_entry.get()
    folder = folder_entry.get()
    input_name = video_filename_entry.get().strip()

    if not url:
        messagebox.showerror("Error", "Please enter a YouTube URL")
        return

    if not folder or not os.path.isdir(folder):
        messagebox.showerror("Error", "Please choose a valid download folder")
        return

    try:
        progress_var.set(0)
        yt = YouTube(url, on_progress_callback=on_progress)
        ys = yt.streams.get_highest_resolution()

        original_filename = ys.default_filename
        base_name, ext = os.path.splitext(original_filename)
        if input_name:
            safe_filename = resolve_duplicate_path(folder, input_name + ext)
        else:
            safe_filename = resolve_duplicate_path(folder, original_filename)

        ys.download(output_path=folder, filename=safe_filename)
        messagebox.showinfo("Success", f"Downloaded video to:\n{os.path.join(folder, safe_filename)}")
        progress_var.set(0)
        progress_bar.update()
        video_filename_entry.delete(0, tk.END)
        save_config(folder_entry.get(), audio_folder_entry.get(), audio_quality_var.get(), audio_ext_var.get())
    except Exception as e:
        messagebox.showerror("Error", f"Download failed:\n{e}")
        progress_var.set(0)


def update_audio_qualities():
    url = audio_url_entry.get()
    if not url:
        messagebox.showwarning("Warning", "Enter a YouTube URL first to load audio qualities")
        return

    try:
        yt = YouTube(url)
        audio_streams = yt.streams.filter(only_audio=True).order_by('abr').desc()
        qualities = []
        for stream in audio_streams:
            if stream.abr:
                qualities.append(stream.abr)
        if not qualities:
            qualities = ["Unknown"]

        qualities = sorted(set(qualities), key=lambda x: int(x.replace("kbps", "")), reverse=True)
        qualities.insert(0, "Highest")

        audio_quality_dropdown['values'] = qualities
        # Restore last selected quality if available, else default to Highest
        if audio_quality_var.get() in qualities:
            audio_quality_dropdown.set(audio_quality_var.get())
        else:
            audio_quality_dropdown.current(0)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load audio qualities:\n{e}")


def download_audio():
    url = audio_url_entry.get()
    folder = audio_folder_entry.get()
    selected_ext = audio_ext_var.get()
    selected_quality = audio_quality_var.get()
    input_name = audio_filename_entry.get().strip()

    if not url:
        messagebox.showerror("Error", "Please enter a YouTube URL")
        return
    if not folder or not os.path.isdir(folder):
        messagebox.showerror("Error", "Please choose a valid download folder")
        return

    try:
        progress_var.set(0)
        yt = YouTube(url, on_progress_callback=on_progress)
        audio_streams = yt.streams.filter(only_audio=True).order_by('abr').desc()

        if selected_quality == "Highest":
            audio_stream = audio_streams.first()
        else:
            audio_stream = next((stream for stream in audio_streams if stream.abr == selected_quality), audio_streams.first())

        original_filename = audio_stream.default_filename
        base_name, _ = os.path.splitext(original_filename)

        if input_name:
            filename_with_ext = input_name + '.' + selected_ext
        else:
            filename_with_ext = base_name + '.' + selected_ext

        safe_filename = resolve_duplicate_path(folder, filename_with_ext)
        audio_stream.download(output_path=folder, filename=safe_filename)

        messagebox.showinfo("Success", f"Downloaded audio to:\n{os.path.join(folder, safe_filename)}")
        progress_var.set(0)
        progress_bar.update()
        audio_filename_entry.delete(0, tk.END)
        save_config(folder_entry.get(), audio_folder_entry.get(), audio_quality_var.get(), audio_ext_var.get())
    except Exception as e:
        messagebox.showerror("Error", f"Download failed:\n{e}")
        progress_var.set(0)


root = tk.Tk()
root.title("YouTube Downloader")
root.geometry("520x460")

notebook = ttk.Notebook(root)
notebook.pack(pady=10, expand=True, fill='both')

video_tab = ttk.Frame(notebook)
notebook.add(video_tab, text='Video Download')

audio_tab = ttk.Frame(notebook)
notebook.add(audio_tab, text='Audio Download')

# Load saved config
video_path, audio_path, saved_quality, saved_ext = load_config()

# --- Video Tab ---
tk.Label(video_tab, text="YouTube URL:").pack(pady=5)
url_entry = tk.Entry(video_tab, width=60)
url_entry.pack()

tk.Label(video_tab, text="Download Folder:").pack(pady=5)
folder_frame = tk.Frame(video_tab)
folder_frame.pack()

folder_entry = tk.Entry(folder_frame, width=45)
folder_entry.pack(side=tk.LEFT, padx=5)
folder_entry.insert(0, video_path)

browse_button = tk.Button(folder_frame, text="Browse", command=browse_folder)
browse_button.pack(side=tk.LEFT)

tk.Label(video_tab, text="Filename (optional):").pack(pady=5)
video_filename_entry = tk.Entry(video_tab, width=40)
video_filename_entry.pack()

download_button = tk.Button(video_tab, text="Download Video", command=download_video)
download_button.pack(pady=10)

# --- Audio Tab ---
tk.Label(audio_tab, text="YouTube URL:").pack(pady=5)
audio_url_entry = tk.Entry(audio_tab, width=60)
audio_url_entry.pack()

tk.Label(audio_tab, text="Download Folder:").pack(pady=5)
audio_folder_frame = tk.Frame(audio_tab)
audio_folder_frame.pack()

audio_folder_entry = tk.Entry(audio_folder_frame, width=45)
audio_folder_entry.pack(side=tk.LEFT, padx=5)
audio_folder_entry.insert(0, audio_path)

browse_audio_button = tk.Button(audio_folder_frame, text="Browse", command=browse_audio_folder)
browse_audio_button.pack(side=tk.LEFT)

tk.Label(audio_tab, text="Filename (optional):").pack(pady=5)
audio_filename_entry = tk.Entry(audio_tab, width=40)
audio_filename_entry.pack()

row_frame = tk.Frame(audio_tab)
row_frame.pack(pady=10)

tk.Label(row_frame, text="Quality:").grid(row=0, column=0, padx=5)
audio_quality_var = tk.StringVar(value=saved_quality)
audio_quality_dropdown = ttk.Combobox(row_frame, textvariable=audio_quality_var, state="readonly", width=10)
audio_quality_dropdown.grid(row=0, column=1)

# Removed Load button (no longer needed)
# Bind to update audio qualities automatically on URL change
def on_audio_url_change(event):
    url = audio_url_entry.get().strip()
    if url:
        update_audio_qualities()

audio_url_entry.bind("<FocusOut>", on_audio_url_change)
audio_url_entry.bind("<Return>", on_audio_url_change)

tk.Label(row_frame, text="Ext:").grid(row=0, column=3, padx=5)
audio_ext_var = tk.StringVar(value=saved_ext)
audio_ext_dropdown = ttk.Combobox(row_frame, textvariable=audio_ext_var, state="readonly", width=8)
audio_ext_dropdown['values'] = ['mp3', 'm4a', 'wav', 'ogg', 'flac', 'mp4']
audio_ext_dropdown.grid(row=0, column=4)

download_audio_button = tk.Button(audio_tab, text="Download Audio", command=download_audio)
download_audio_button.pack(pady=10)

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100, length=480)
progress_bar.pack(pady=10)

root.mainloop()
