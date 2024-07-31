from datetime import date, datetime, timedelta
import json
from os import path
import os
import subprocess
import tkinter as tk
from tkinter import ttk
from tkcalendar import Calendar

from db import get_all_users, add_user, delete_users_by_name
from db import get_all_paths, add_path, delete_paths_by_folder
from db import get_all_configs, update_config_by_name, Config


def get_previous_month_end(today):
    """Returns previous month"""
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


class Entry:
    """Git log entry"""

    COMMIT = "commit"
    AUTHOR = "author"
    MESSAGE = "message"
    DATE = "date"
    DATE_PARSED = "x_date"


def transform_log_entry(git_log_entry, date_format):
    """Add data to log entry:
    * convert date
    * extract comments
    """

    date = datetime.strptime(git_log_entry[Entry.DATE], date_format)
    git_log_entry[Entry.DATE_PARSED] = date
    return git_log_entry


def get_unexisted_folders(folders_list):
    """Get unexisted folders"""

    folders = []
    for i in folders_list:
        if not path.exists(i):
            folders.append(i)

    return folders


def show():
    """Shows Tk UI"""

    def cb_add_folder():
        folder = tk.filedialog.askdirectory()
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

    def cb_get_git_log_data():
        treeview_data.delete()

        folders = folders_list.get(0, tk.END)
        users = users_list.get(0, tk.END)
        if not folders or not users:
            return

        unexisting_folders = get_unexisted_folders(folders)
        if unexisting_folders:
            tk.messagebox.showerror("Error", f"Folders not found: {unexisting_folders}")
            return

        after = data_calendar.get_date()
        raw_git_log = get_git_log(folders[0], after)
        if not raw_git_log:
            return

        date_format = config[Config.DEF_DATE_FORMAT]
        entries = [transform_log_entry(entry, date_format) for entry in raw_git_log]

        entries.sort(key=lambda entry: entry[Entry.DATE_PARSED])

        for entry in entries:
            treeview_data.insert(
                "",
                tk.END,
                text=entry[Entry.COMMIT],
                values=(entry[Entry.AUTHOR], entry[Entry.DATE], entry[Entry.MESSAGE]),
            )

    def cb_date_format_changed(event):
        new_date_format = var_date_format.get()
        old_date_format = config[Config.DEF_DATE_FORMAT]
        if new_date_format == old_date_format:
            return

        if not update_config_by_name(Config.DEF_DATE_FORMAT, new_date_format):
            tk.messagebox.showerror("Error", "Failed to update config")
            var_date_format.set(old_date_format)
            return
        config[Config.DEF_DATE_FORMAT] = new_date_format

    config = {}
    for cfg in get_all_configs():
        config[cfg.name] = cfg.value

    root = tk.Tk()
    root.geometry("1600x800")
    root.title("CWPL generator")

    # variables
    var_date_format = tk.StringVar(value=config[Config.DEF_DATE_FORMAT])

    # create tab control
    tab_control = ttk.Notebook(master=root)

    config_tab = ttk.Frame(tab_control)
    report_tab = ttk.Frame(tab_control)

    tab_control.add(report_tab, text="Report")
    tab_control.add(config_tab, text="Config")
    tab_control.pack(fill=tk.BOTH, expand=True)

    # folders frame
    folders_frame = tk.LabelFrame(
        master=config_tab, height=200, text=" folders to be processed: "
    )
    folders_list = tk.Listbox(master=folders_frame, selectmode=tk.SINGLE)
    folders_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    tk.Button(master=folders_frame, text="+", command=cb_add_folder).pack()
    tk.Button(master=folders_frame, text="-", command=cb_del_folder).pack()

    folders_frame.pack(side=tk.TOP, anchor=tk.NE, expand=True, fill=tk.X, pady=10)

    # user frame
    users_frame = tk.LabelFrame(
        master=config_tab, height=200, text=" authors to look for: "
    )
    users_entry = tk.Entry(master=users_frame)
    users_entry.pack(side=tk.TOP, fill=tk.X, expand=True)
    users_list = tk.Listbox(master=users_frame, selectmode=tk.SINGLE, height=5)
    users_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    tk.Button(master=users_frame, text="+", command=cb_add_user).pack()
    tk.Button(master=users_frame, text="-", command=cb_del_user).pack()

    users_frame.pack(side=tk.TOP, anchor=tk.N, expand=True, fill=tk.X, pady=10)

    # settings frame
    settings_frame = tk.LabelFrame(master=config_tab, text=" settings: ")
    tk.Label(master=settings_frame, text="date format: ").pack(side=tk.LEFT)
    __date_fmt_entry = tk.Entry(master=settings_frame, textvariable=var_date_format)
    __date_fmt_entry.bind("<FocusOut>", cb_date_format_changed)
    __date_fmt_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
    settings_frame.pack(side=tk.TOP, anchor=tk.N, expand=True, fill=tk.X, pady=10)

    # gather data
    data_frame = tk.LabelFrame(master=report_tab, height=200, text=" gathering data...")
    dt = get_previous_month_end(date.today())

    data_calendar = Calendar(
        master=data_frame,
        selectmode="day",
        date_pattern=r"y-mm-dd",
        year=dt.year,
        month=dt.month,
        day=dt.day,
    )
    data_calendar.grid(row=0, column=0)
    tk.Button(
        master=data_frame, text="FETCH GIT LOG", command=cb_get_git_log_data
    ).grid(row=1, column=0, sticky=tk.NW)

    treeview_data = ttk.Treeview(
        master=data_frame, columns=(Entry.AUTHOR, Entry.DATE, Entry.MESSAGE)
    )
    treeview_data.heading("#0", text="Commit")
    treeview_data.heading(Entry.AUTHOR, text="Author")
    treeview_data.heading(Entry.DATE, text="Date")
    treeview_data.heading(Entry.MESSAGE, text="Message")
    treeview_data.grid(row=0, column=1, rowspan=2, sticky=tk.NSEW)

    __scroll_treeview_data = ttk.Scrollbar(
        data_frame, orient=tk.VERTICAL, command=treeview_data.yview
    )
    __scroll_treeview_data.grid(row=0, column=2, rowspan=2, sticky=tk.NS)
    treeview_data.configure(yscrollcommand=__scroll_treeview_data.set)

    # TODO: remove panel?
    __date_btn_panel = tk.Frame(master=data_frame)
    tk.Button(master=__date_btn_panel, text=">>").pack(side=tk.TOP)
    __date_btn_panel.grid(row=0, column=3, sticky=tk.NW)

    data_frame.pack(side=tk.TOP, anchor=tk.N, expand=True, fill=tk.X, pady=10)
    data_frame.columnconfigure(1, weight=1)

    # Update list of folders
    list_all_folders()
    # Update list of users
    list_all_users()

    root.mainloop()
