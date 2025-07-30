import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys
import json
import importlib.resources
from dircomply.version import (
	__version__,__email__,__release_date__,__author__
)

# Extensions to compare
def load_extensions():
    try:
        # Try reading from installed package
        with importlib.resources.open_text("dircomply.config", "extensions.json") as f:
            data = json.load(f)
    except (FileNotFoundError, ImportError):
        # Fallback to local file system (e.g., during development or direct run)
        local_path = os.path.join(os.path.dirname(__file__), "config", "extensions.json")
        with open(local_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    return tuple(data.get("extensions", [".txt", ".py", ".bat", ".html", ".ts"]))
ext_list = load_extensions()


# Function to display help
def print_help():
	help_message = """
Usage: dircomply [OPTIONS]

A small package to compare the files between two project folders.

Options:
	--version, -v      Show the version of dircomply and exit
	--help, -h         Show this help message and exit
	--email, -e        Show email and exit
	--author, -a       Show author and exit
	(No arguments)     Launch the GUI application
	[folder1_path] [folder2_path] compare contents form both folders.
	"""
	print(help_message)
	sys.exit(0)

# Function to read file content
def read_file(filepath):
	try:
		with open(filepath, 'r', encoding='utf-8') as file:
			return file.read()
	except UnicodeDecodeError:
		try:
			# Handles utf-8 with BOM
			with open(filepath, 'r', encoding='utf-8-sig') as file:
				return file.read()
		except UnicodeDecodeError:
			try:
				with open(filepath, 'r', encoding='latin-1') as file:
					return file.read()
			except Exception as e:
				return f"Error: {e}"
	except Exception as e:
		return f"Error: {e}"


# Function to get all files with specific extensions
def get_files_with_extensions(folder, extensions):
	all_files = set()
	for root_dir, _, files in os.walk(folder):
		for file in files:
			if file.endswith(extensions):
				relative_path = os.path.relpath(os.path.join(root_dir, file), folder)
				all_files.add(relative_path)
	return all_files

# Function to compare folders
def compare_folders(folder1, folder2):
	folder1_files = get_files_with_extensions(folder1, ext_list)
	folder2_files = get_files_with_extensions(folder2, ext_list)

	# Common files
	common_files = folder1_files & folder2_files

	# Unique files
	unique_to_folder1 = folder1_files - folder2_files
	unique_to_folder2 = folder2_files - folder1_files

	# Files with differences
	different_files = []
	for file in common_files:
		path1 = os.path.join(folder1, file)
		path2 = os.path.join(folder2, file)
		if read_file(path1) != read_file(path2):
			different_files.append(file)
	return sorted(different_files), sorted(unique_to_folder1), sorted(unique_to_folder2)

# GUI Application
def create_gui(folder1_path=None,folder2_path=None,compare_on_start=False):
	
	def select_folder1():
		path = filedialog.askdirectory(title="Select Folder 1")
		if path:
			folder1_var.set(path)
	
	def select_folder2():
		path = filedialog.askdirectory(title="Select Folder 2")
		if path:
			folder2_var.set(path)

	def compare():
		folder1 = folder1_var.get()
		folder2 = folder2_var.get()

		if not folder1 or not folder2:
			messagebox.showerror("Error", "Please select both folders")
			return
		
		if not os.path.exists(folder1) or not os.path.exists(folder2):
			messagebox.showerror("Error", "One or both folders do not exist")
			return

		# Compare folders
		different_files, unique_to_folder1, unique_to_folder2 = compare_folders(folder1, folder2)

		# Create result message
		result = f"Comparison Results: of {folder1} and {folder2}\n\n"
		if different_files:
			result += "Files with differences:\n" + "\n".join(different_files) + "\n\n"
		else:
			result += "No files with differences found.\n\n"

		if unique_to_folder1:
			result += f"Files unique to {folder1}:\n" + "\n".join(unique_to_folder1) + "\n\n"
		if unique_to_folder2:
			result += f"Files unique to {folder2}:\n" + "\n".join(unique_to_folder2) + "\n\n"
		
		# Display results in a popup window
		popup = tk.Toplevel(root)
		popup.title("Comparison Results")
		popup.geometry("600x400")

		result_text = tk.Text(popup, wrap=tk.WORD, font=("Arial", 10))
		result_text.pack(expand=True, fill=tk.BOTH)
		result_text.insert(tk.END, result)
		result_text.config(state=tk.DISABLED)
		scrollbar = tk.Scrollbar(popup, command=result_text.yview)
		scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
		result_text.config(yscrollcommand=scrollbar.set)


	# Main window
	root = tk.Tk()
	root.title("Folder File Comparator")
	root.geometry("500x300")

	folder1_var = tk.StringVar()
	folder2_var = tk.StringVar()
	if folder1_path:
		folder1_var.set(folder1_path)
	if folder2_path:
		folder2_var.set(folder2_path)

	# GUI Layout
	tk.Label(root, text="Folder 1 Path:", font=("Arial", 12)).pack(pady=5)
	tk.Entry(root, textvariable=folder1_var, width=50).pack()
	tk.Button(root, text="Select Folder 1", command=select_folder1).pack(pady=5)

	tk.Label(root, text="Folder 2 Path:", font=("Arial", 12)).pack(pady=5)
	tk.Entry(root, textvariable=folder2_var, width=50).pack()
	tk.Button(root, text="Select Folder 2", command=select_folder2).pack(pady=5)

	tk.Button(root, text="Compare Folders", command=compare, font=("Arial", 12, "bold"), bg="lightblue").pack(pady=20)
	if compare_on_start and folder1_path and folder2_path:
		compare()

	root.mainloop()

# Main entry point
def main():
	# Check for command-line arguments
	if "--version" in sys.argv or "-v" in sys.argv:
		print(f"version {__version__}")
		sys.exit(0)
	if "--help" in sys.argv or "-h" in sys.argv:
		print_help()
		sys.exit(0)
	if "--author" in sys.argv or "-a" in sys.argv:
		print(f"Author {__author__}")
		sys.exit(0)
	if "--email" in sys.argv or "-e" in sys.argv:
		print(f"Mailto {__email__}")
		sys.exit(0)
	if "--date" in sys.argv or "-d" in sys.argv:
		print(f"Release Date {__release_date__}")
		sys.exit(0)
	if len(sys.argv) == 2:
		print("Error: Please provide both folder paths.")
		sys.exit(1)
	if len(sys.argv) > 2:
		folder1_path = sys.argv[1]
		folder2_path = sys.argv[2]
		if not os.path.exists(folder1_path):
			print(f"Error: Directory '{folder1_path}' does not exist.")
			sys.exit(1)
		if not os.path.exists(folder2_path):
			print(f"Error: Directory '{folder2_path}' does not exist.")
			sys.exit(1)
		create_gui(folder1_path=folder1_path,folder2_path=folder2_path,compare_on_start=True)
	else:
		create_gui()


if __name__ == "__main__":
	main()