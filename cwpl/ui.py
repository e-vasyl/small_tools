from datetime import date, datetime, timedelta
import json
from os import path
import os
import re
import subprocess
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkcalendar import Calendar

from db import ConfBool, get_all_users, add_user, delete_users_by_name
from db import get_all_paths, add_path, delete_paths_by_folder
from db import get_all_configs, update_config_by_name, Config


def get_previous_month_end(today):
    """Returns previous month"""
    return date(today.year, today.month, 1) + timedelta(-2)


def get_git_log(path, after, git_log_format, branches=None):
    """Returns git log"""
    # git log --pretty=format:'{%n  \"commit\": \"%H\",%n  \"author\": \"%an\",%n  \"date\": \"%ad\",%n  \"message\": \"%f\"%n},'

    res = []
    cwd = os.getcwd()
    try:
        os.chdir(path)
        args = [
            "git",
            "log",
            f"--pretty=format:{git_log_format}",
            f'--after="{after}"',
        ]
        # add branches if specified
        if branches:
            args.append(f"--branches={branches}")

        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = process.communicate()
        if err:
            print(err.decode("utf-8").splitlines())
            return res
        raw_res = out.decode("utf-8")

        # join multilines to pass into JSON parser
        joined_res = ""
        for line in raw_res.splitlines():
            joined_res += line
            if not line.endswith("},"):
                joined_res += "\\n"

        # remove last comma
        if joined_res.endswith(","):
            joined_res = joined_res[:-1]

        json_res = "[" + joined_res + "]"

        json_res_fixed = ""
        if not joined_res:
            json_res_fixed = json_res
        else:
            for l in json_res.replace("},{", "},\n{").splitlines():
                # print(l)
                match_msg = re.match(r"(^.*\"message\"\s*:\s*\")(.*)(\"},?)", l)
                if match_msg is None:
                    raise Exception(f"ERROR: wrong wormat: no message field!")
                msg_groups = match_msg.groups()
                if '"' in msg_groups[1]:
                    json_res_fixed += (
                        msg_groups[0]
                        + msg_groups[1].replace('"', '\\"')
                        + msg_groups[2]
                    )
                else:
                    json_res_fixed += l
        # print("=" * 10)

        # try to parse JSON
        res = json.loads(json_res_fixed)
    except Exception as e:
        print(f"EXCEPTION: {e}")
    finally:
        os.chdir(cwd)
    return res


class Entry:
    """Git log entry"""

    __PREFIX_PARSED = "x___"
    COMMIT = "commit"
    AUTHOR = "author"
    MESSAGE = "message"
    DATE = "date"
    DATE_PARSED = __PREFIX_PARSED + DATE
    CUSTOM_ID = __PREFIX_PARSED + "custom_id"

    @staticmethod
    def get_keys(item):

        if isinstance(item, dict):
            dict_keys = item.keys()
            __get_attr = lambda key: key
        else:
            dict_keys = item.__dict__.keys()
            __get_attr = lambda key: getattr(item, key)
        return [
            __get_attr(key)
            for key in dict_keys
            if not (
                key.startswith("_")
                or callable(__get_attr(key))
                or __get_attr(key).startswith(Entry.__PREFIX_PARSED)
            )
        ]


def transform_log_entry(git_log_entry, date_format):
    """Add data to log entry:
    * convert date
    * extract comments
    """

    date = datetime.strptime(git_log_entry[Entry.DATE], date_format)
    git_log_entry[Entry.DATE_PARSED] = date

    # TODO: customize it
    custom_id_match = re.search(
        r"change-id\s*:\s*([A-Za-z0-9]+)",
        git_log_entry[Entry.MESSAGE],
        flags=re.I,
    )
    if custom_id_match:
        git_log_entry[Entry.CUSTOM_ID] = custom_id_match.group(1)
    else:
        git_log_entry[Entry.CUSTOM_ID] = ""

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

    def get_git_log_entries():
        folders = folders_list.get(0, tk.END)
        users = users_list.get(0, tk.END)
        if not folders:
            return []

        git_log_format = var_git_log_format.get()
        date_format = var_date_format.get()

        unexisting_folders = get_unexisted_folders(folders)
        if unexisting_folders:
            folder_error_str = r"\n".join(unexisting_folders)
            tk.messagebox.showerror("Error", f"Folders not found: {folder_error_str}")
            return []

        after = data_calendar.get_date()
        branches_names = None
        if var_git_log_in_branches.get():
            # TODO: change to variable
            branches_names = config[Config.DEF_GIT_LOG_BRANCHES]

        raw_git_log = get_git_log(
            folders[0], after, git_log_format, branches=branches_names
        )
        if not raw_git_log:
            return []

        filtered_git_log = []
        for git_log in raw_git_log:
            for author in users:
                if author in git_log[Entry.AUTHOR]:
                    filtered_git_log.append(git_log)
                    break

        entries = [
            transform_log_entry(entry, date_format) for entry in filtered_git_log
        ]

        # delete entries with same commit
        unique_commits = {}
        for entry in entries:
            entry_commit = entry[Entry.COMMIT]
            found_same = False
            if entry_commit in unique_commits:
                # check that messages are the same
                # if they are different - then it could be a coincidence
                for i in unique_commits[entry_commit]:
                    if i[Entry.MESSAGE] == entry[Entry.MESSAGE]:
                        found_same = True
                        break
            else:
                unique_commits[entry_commit] = []
            if found_same:
                entries.remove(entry)
            else:
                unique_commits[entry_commit].append(entry)

        return entries

    git_log_entries = {"data": [], "sort": (Entry.DATE_PARSED, True)}

    def set_columns_sort(column_name):
        sort_field, is_asc = git_log_entries["sort"]
        # transform to data key
        if column_name == Entry.DATE:
            column_name = Entry.DATE_PARSED

        if sort_field == column_name:
            is_asc = not is_asc
        else:
            sort_field = column_name
            is_asc = True

        git_log_entries["sort"] = (column_name, is_asc)
        set_git_log_data_tv()

    def cb_get_git_log_data():
        git_log_entries["data"] = get_git_log_entries()
        set_git_log_data_tv()

    def set_git_log_data_tv():
        entries = git_log_entries["data"]
        treeview_data.delete(*treeview_data.get_children())
        if not entries:
            return

        column_sort_field, column_sort_asc = git_log_entries["sort"]
        # sort commits by date
        entries.sort(
            key=lambda entry: entry[column_sort_field], reverse=not column_sort_asc
        )

        for entry in entries:
            store_dict = {k: entry[k] for k in Entry.get_keys(entry)}
            entry_str = json.dumps(store_dict)
            lines = [l for l in entry[Entry.MESSAGE].split("\n") if l.strip()]

            line_item = treeview_data.insert(
                "",
                tk.END,
                text=entry[Entry.COMMIT],
                values=(
                    entry[Entry.AUTHOR],
                    entry[Entry.DATE],
                    lines[0],
                    entry[Entry.CUSTOM_ID],
                    entry_str,
                ),
            )
            for line in lines[1:]:
                treeview_data.insert(line_item, tk.END, text="", values=("", "", line))

    def cb_append_to_report():
        """append item from treeview to report"""

        selected = treeview_data.selection()
        if not selected:
            return

        report_logs = []
        for sel in selected:
            # TODO: add parent if it was not already selected
            if treeview_data.parent(sel):
                continue

            item = treeview_data.item(sel)
            values = item["values"]
            entry = json.loads(values[-1])
            report_logs.append(entry)

        report_entry_log_format = var_entry_log_format.get()
        for report in report_logs:
            report_text.insert(
                tk.END,
                report_entry_log_format.format(**report).replace(r"\n", "\n"),
            )

    config = Config.DEF_CONFIG.copy()
    for cfg in get_all_configs():
        config[cfg.name] = cfg.value

    root = tk.Tk()
    root.geometry("1600x600")
    root.title("CWPL generator")

    # create tab control
    tab_control = ttk.Notebook(master=root)

    config_tab = ttk.Frame(tab_control)
    report_tab = ttk.Frame(tab_control)

    tab_control.add(report_tab, text="Report")
    tab_control.add(config_tab, text="Config")
    tab_control.pack(fill=tk.BOTH, expand=True)

    config_tab.columnconfigure(0, weight=1)

    # folders frame
    folders_frame = tk.LabelFrame(
        master=config_tab, height=200, text=" folders to be processed: "
    )
    folders_list = tk.Listbox(master=folders_frame, selectmode=tk.SINGLE)
    folders_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    tk.Button(master=folders_frame, text="+", command=cb_add_folder).pack()
    tk.Button(master=folders_frame, text="-", command=cb_del_folder).pack()

    folders_frame.grid(row=0, column=0, sticky=tk.NSEW)

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

    users_frame.grid(row=1, column=0, sticky=tk.NSEW)

    # settings frame
    settings_frame = tk.LabelFrame(master=config_tab, text=" settings: ")

    def create_config_ui(
        master, text, row, config_name, default_value, validator_cb=None
    ):
        var_value = tk.StringVar(value=config[config_name])

        def cb_value_changed(event):
            new_value = var_value.get()
            old_value = config[config_name]
            if new_value == old_value:
                return

            if not update_config_by_name(config_name, new_value):
                tk.messagebox.showerror("Error", "Failed to update config")
                var_value.set(old_value)
                return
            config[config_name] = new_value

        def cb_set_default():
            var_value.set(default_value)
            cb_value_changed(None)

        tk.Label(master=master, text=text).grid(row=row, column=0)
        __entry = tk.Entry(master=master, textvariable=var_value)
        __entry.grid(row=row, column=1, sticky=tk.EW)
        tk.Button(master=settings_frame, text="default", command=cb_set_default).grid(
            row=row, column=2
        )
        __entry.bind("<FocusOut>", cb_value_changed)

        if validator_cb:

            def cb_validate_value(*args):
                is_valid = validator_cb(var_value.get())
                if is_valid or is_valid == None:
                    color = "White"
                else:
                    color = "Red"
                __entry.config({"background": color})

            # add validator callback
            var_value.trace_add("write", cb_validate_value)
            # run validator on init
            cb_validate_value()

        return (var_value, __entry)

    def create_config_ui_bool(master, text, row, config_name, default_value):
        start_val = ConfBool.from_string(config[config_name]).int()
        var_value = tk.IntVar(value=start_val)

        def cb_value_changed(event):
            new_value = ConfBool.from_int(var_value.get()).value
            old_value = config[config_name]
            if new_value == old_value:
                return

            if not update_config_by_name(config_name, new_value):
                tk.messagebox.showerror("Error", "Failed to update config")
                var_value.set(old_value)
                return
            config[config_name] = new_value

        def cb_set_default():
            var_value.set(ConfBool.from_string(default_value).int())
            cb_value_changed(None)

        tk.Label(master=master, text=text).grid(row=row, column=0)
        __cb = tk.Checkbutton(master=master, variable=var_value)
        __cb.grid(row=row, column=1, sticky=tk.W, padx=(0, 5))
        tk.Button(master=settings_frame, text="default", command=cb_set_default).grid(
            row=row, column=2
        )
        var_value.trace_add("write", lambda *args: cb_value_changed(None))

        return (var_value, __cb)

    settings_frame_row_idx = 0
    var_date_format, _ = create_config_ui(
        settings_frame,
        "date format: ",
        settings_frame_row_idx,
        Config.DEF_DATE_FORMAT,
        Config.DEF_DATE_FORMAT_VALUE,
    )

    def edit_git_log_validator(str_value):
        try:
            if not str_value.endswith(","):
                return False
            entity_val = json.loads(str_value[:-1])
            existing_keys = set(entity_val.keys())
            expected_keys = set(Entry.get_keys(Entry))
            return expected_keys.issubset(existing_keys)
        except Exception as e:
            print(e)
        return False

    settings_frame_row_idx += 1
    var_git_log_format, _ = create_config_ui(
        settings_frame,
        "git log format: ",
        settings_frame_row_idx,
        Config.DEF_GIT_LOG_FORMAT,
        Config.DEF_GIT_LOG_FORMAT_VALUE,
        validator_cb=edit_git_log_validator,
    )

    settings_frame_row_idx += 1
    var_git_log_in_branches, _ = create_config_ui_bool(
        settings_frame,
        "look in branches: ",
        settings_frame_row_idx,
        Config.DEF_GIT_LOG_IN_BRANCHES,
        Config.DEF_GIT_LOG_IN_BRANCHES_VALUE,
    )

    def edit_entry_log_validator(str_value):
        try:
            entity_str = var_git_log_format.get()
            entity_val = json.loads(entity_str[:-1])
            s = str_value.format(Entry, **entity_val)
            return True
        except Exception as e:
            print(e)
        return False

    settings_frame_row_idx += 1
    var_entry_log_format, _ = create_config_ui(
        settings_frame,
        "report format: ",
        settings_frame_row_idx,
        Config.DEF_ENTRY_LOG_FORMAT,
        Config.DEF_ENTRY_LOG_FORMAT_VALUE,
        validator_cb=edit_entry_log_validator,
    )

    settings_frame_row_idx += 1
    var_entry_show_custom_id, _ = create_config_ui_bool(
        settings_frame,
        "show custom id: ",
        settings_frame_row_idx,
        Config.DEF_ENTRY_SHOW_CUSTOM_ID,
        Config.DEF_ENTRY_SHOW_CUSTOM_ID_VALUE,
    )

    def on_toggle_show_custom_id_column():
        show = var_entry_show_custom_id.get()
        if show:
            treeview_data.column(
                Entry.CUSTOM_ID, minwidth=0, width=340, stretch=tk.NO, anchor=tk.E
            )
        else:
            treeview_data.column(
                Entry.CUSTOM_ID, minwidth=0, width=0, stretch=tk.NO, anchor=tk.E
            )

    var_entry_show_custom_id.trace_add(
        "write", lambda *args: on_toggle_show_custom_id_column()
    )

    settings_frame.grid(row=2, column=0, sticky=tk.NSEW)
    settings_frame.columnconfigure(1, weight=1)

    # TODO: remove?
    # filler tab in the bottom
    # tk.Frame(master=config_tab).pack(side=tk.BOTTOM, expand=True, fill=tk.BOTH)

    ### REPORT TAB

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

    def _g_cb(name):
        return lambda: set_columns_sort(name)

    treeview_data = ttk.Treeview(
        master=data_frame,
        columns=(Entry.AUTHOR, Entry.DATE, Entry.MESSAGE, Entry.CUSTOM_ID),
    )
    treeview_data.heading("#0", text="Commit", command=_g_cb(Entry.COMMIT))
    treeview_data.column("#0", minwidth=0, width=300, stretch=tk.NO)
    treeview_data.heading(Entry.AUTHOR, text="Author", command=_g_cb(Entry.AUTHOR))
    treeview_data.column(Entry.AUTHOR, minwidth=0, width=200, stretch=tk.NO)
    treeview_data.heading(Entry.DATE, text="Date", command=_g_cb(Entry.DATE))
    treeview_data.column(Entry.DATE, minwidth=0, width=200, stretch=tk.NO)
    treeview_data.heading(Entry.MESSAGE, text="Message", command=_g_cb(Entry.MESSAGE))
    treeview_data.heading(
        Entry.CUSTOM_ID, text="Custom ID", command=_g_cb(Entry.CUSTOM_ID)
    )
    on_toggle_show_custom_id_column()

    treeview_data.grid(row=0, column=1, rowspan=2, sticky=tk.NSEW)

    def create_vs(master, owner):
        vs = ttk.Scrollbar(master, orient=tk.VERTICAL, command=owner.yview)
        owner.configure(yscrollcommand=vs.set)
        return vs

    create_vs(data_frame, treeview_data).grid(row=0, column=2, rowspan=2, sticky=tk.NS)

    # TODO: remove panel?
    __date_btn_panel = tk.Frame(master=data_frame)
    tk.Button(master=__date_btn_panel, text=">>", command=cb_append_to_report).pack(
        side=tk.TOP
    )
    __date_btn_panel.grid(row=0, column=3, sticky=tk.NW)

    data_frame.pack(side=tk.TOP, anchor=tk.N, expand=True, fill=tk.X, pady=10)
    data_frame.columnconfigure(1, weight=1)

    report_frame = tk.Frame(master=report_tab)
    # TODO: fix text area
    __report_text_frame = tk.Frame(master=report_frame)
    report_text = tk.Text(master=__report_text_frame, height=100, width=100)
    report_text.config(spacing3=5, spacing2=2)
    # report_text.grid(row=0, column=0, sticky=tk.NSEW)
    report_text.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

    # bind handler of <ctrl-a> to report text widget
    report_text.bind(
        "<Control-KeyRelease-a>",
        lambda event: event.widget.tag_add(tk.SEL, "1.0", tk.END),
    )
    __report_text_frame.grid(row=0, column=0, sticky=tk.NSEW)
    create_vs(report_frame, report_text).grid(row=0, column=1, sticky=tk.NS)

    tk.Button(
        master=report_frame,
        text="CLEAR",
        command=lambda: report_text.delete("1.0", tk.END),
    ).grid(row=0, column=2, sticky=tk.S)
    # tk.Frame(master=report_frame).pack(side=tk.LEFT, anchor=tk.W, expand=True, fill=tk.BOTH)

    report_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
    report_frame.columnconfigure(0, weight=1)
    report_frame.rowconfigure(0, weight=1)

    # Update list of folders
    list_all_folders()
    # Update list of users
    list_all_users()

    root.mainloop()
