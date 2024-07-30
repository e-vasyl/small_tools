from datetime import date, timedelta
import json
from os import path
import os
import subprocess
import tkinter as tk
from tkinter import messagebox, filedialog
from tkcalendar import Calendar

from db import get_all_users, add_user, delete_users_by_name
from db import get_all_paths, add_path, delete_paths_by_folder


def get_previous_month_end():
    """Returns previous month"""
    today = date.today()
    return date(today.year, today.month, 1) + timedelta(-2)


def get_git_log(path, after):
    """Returns git log"""
    # git log --pretty=format:'{%n  \"commit\": \"%H\",%n  \"author\": \"%an\",%n  \"date\": \"%ad\",%n  \"message\": \"%f\"%n},'

    res = []
    cwd = os.getcwd()
    try:
        os.chdir(path)
        process = subprocess.Popen(
            [
                "git",
                "log",
                r'--pretty=format:{"commit": "%H", "author": "%an", "date": "%ad", "message": "%f"},',
                "--after",
                after,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = process.communicate()
        if err:
            print(err.decode("utf-8").splitlines())
            return res
        raw_res = out.decode("utf-8")
        if raw_res.endswith(","):
            raw_res = raw_res[:-1]
        json_res = "[" + raw_res + "]"
        res = json.loads(json_res)
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return res
    finally:
        os.chdir(cwd)
    return res


def show():
    """Shows Tk UI"""

    def cb_add_folder():
        folder = filedialog.askdirectory()
        if not folder:
            return

        # folder = path.abspath(folder)
        # if not path.exists(folder):
        #     messagebox.showerror("Error", f"Folder '{folder}' does not exist!")
        #     return

        folders = folders_list.get(0, tk.END)
        if folder in folders:
            return

        add_path(folder)

        # update list of folders
        list_all_folders()

    def cb_del_folder():
        if not folders_list.curselection():
            return

        path = folders_list.get(folders_list.curselection())
        deleted = delete_paths_by_folder(path)
        if deleted < 1:
            return

        # update list of folders
        list_all_folders()

    def list_all_folders():
        folders = [p.folder for p in get_all_paths()]
        sorted(folders)
        folders_list.delete(0, tk.END)
        for folder in folders:
            folders_list.insert(tk.END, folder)

    def cb_add_user():
        user = users_entry.get()
        if not user:
            return

        users = users_list.get(0, tk.END)
        if user in users:
            return

        add_user(user)

        # update list of users
        list_all_users()

    def cb_del_user():
        if not users_list.curselection():
            return
        user = users_list.get(users_list.curselection())
        deleted = delete_users_by_name(user)
        if deleted < 1:
            return
        # update list of users
        list_all_users()

    def list_all_users():
        users = [u.name for u in get_all_users()]
        sorted(users)
        users_list.delete(0, tk.END)
        for user in users:
            users_list.insert(tk.END, user)

    def cb_run_report():
        folders = folders_list.get(0, tk.END)
        users = users_list.get(0, tk.END)
        if not folders or not users:
            return

        after = data_calendar.get_date()
        print(after)
        res = get_git_log(folders[0], after)
        print(res)

    root = tk.Tk()
    root.geometry("1600x800")
    root.title("CWPL generator")

    # folders frame
    folders_frame = tk.LabelFrame(
        master=root, height=200, text=" folders to be processed: "
    )
    folders_list = tk.Listbox(master=folders_frame, selectmode=tk.SINGLE)
    folders_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    tk.Button(master=folders_frame, text="+", command=cb_add_folder).pack()
    tk.Button(master=folders_frame, text="-", command=cb_del_folder).pack()

    folders_frame.pack(side=tk.TOP, anchor=tk.NE, expand=True, fill=tk.X, pady=10)

    # user frame
    users_frame = tk.LabelFrame(master=root, height=200, text=" authors to look for: ")
    users_entry = tk.Entry(master=users_frame)
    users_entry.pack(side=tk.TOP, fill=tk.X, expand=True)
    users_list = tk.Listbox(master=users_frame, selectmode=tk.SINGLE, height=5)
    users_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    tk.Button(master=users_frame, text="+", command=cb_add_user).pack()
    tk.Button(master=users_frame, text="-", command=cb_del_user).pack()

    users_frame.pack(side=tk.TOP, anchor=tk.N, expand=True, fill=tk.X, pady=10)

    # gather data
    data_frame = tk.LabelFrame(master=root, height=200, text=" gathering data...")
    dt = get_previous_month_end()

    data_calendar = Calendar(
        master=data_frame,
        selectmode="day",
        date_pattern=r"y-mm-dd",
        year=dt.year,
        month=dt.month,
        day=dt.day,
    )
    data_calendar.grid(row=0, column=0)
    tk.Button(master=data_frame, text="CREATE!", command=cb_run_report).grid(
        row=1, column=0
    )

    data_frame.pack(side=tk.TOP, anchor=tk.N, expand=True, fill=tk.X, pady=10)

    # Update list of folders
    list_all_folders()
    # Update list of users
    list_all_users()

    root.mainloop()
