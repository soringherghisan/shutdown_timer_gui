from tkinter import *
from tkinter import ttk
import time
import datetime
import subprocess


class ShutdownTimer:
    def __init__(self):
        ### flags & handles
        self.ACTION_SELECTED = False
        self.MINUTES_VALIDATED = False
        self.PROGRESS_BAR_ID = None

        ### root
        self.root = Tk()
        # self.root.resizable(False, False)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.title("Shutdown Timer")
        self.root.bind("<<Validate>>", self._validate_and_enable_buttons)
        self.minute_validator = self.root.register(self._validate_minutes)

        ### frame 1 - upper frame
        self.upper_frame = ttk.Frame(self.root, padding="20", )
        self.upper_frame.grid(row=0, rowspan=1)
        # static label
        ttk.Label(self.upper_frame, text="Select an action: ", font=('Times New Roman', 10)) \
            .grid(column=0, row=0)
        # combobox
        self.action_var = StringVar()
        self.action = ttk.Combobox(self.upper_frame, textvariable=self.action_var)
        self.action['values'] = ('Shutdown', 'Restart', 'Log off')
        self.action.state(["readonly"])
        self.action.bind('<<ComboboxSelected>>', lambda e: self.update_action_text())
        self.action.grid(column=1, row=0)

        ### frame 2 - middle frame
        self.middle_frame = ttk.Frame(self.root, padding="20", )
        self.middle_frame.grid(row=1, )
        # label - perform action in
        self.perform_action_label = ttk.Label(self.middle_frame, text=f"Perform action in: ",
                                              font=('Times New Roman', 10))
        self.perform_action_label.grid(column=0, row=0)
        # minutes spinbox
        self.minutes_var = StringVar()
        self.minutes_var.trace_add("write", self.generate_validate_event)
        self.minutes_spinner = ttk.Spinbox(self.middle_frame, from_=1.0, to=999.0, textvariable=self.minutes_var,
                                           width=5, wrap=True, validate='all',
                                           validatecommand=(self.minute_validator, "%P"),
                                           invalidcommand=self.clear_minutes_field)
        self.minutes_spinner.grid(column=1, row=0)
        # static label minutes
        ttk.Label(self.middle_frame, text="Minutes", font=('Times New Roman', 10)).grid(column=2, row=0)

        ### frame 2.1 - progrees bar and buttons
        self.progress_frame = ttk.Frame(self.root, padding="20", )
        self.progress_frame.grid(row=2)
        # start button
        self.start_button = ttk.Button(self.progress_frame, text='Start', command=self.start_button_command)
        self.start_button.grid(column=0, row=1, sticky=(N, W))
        self.start_button.state(['disabled'])
        # progress bar
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient=HORIZONTAL, length=200, mode='determinate')
        self.progress_bar.grid(column=1, row=1, sticky=(E, W))
        # stop button
        self.stop_button = ttk.Button(self.progress_frame, text='Stop', command=self.stop_button_command)
        self.stop_button.grid(column=2, row=1)
        self.stop_button.state(['disabled'])

        ### frame 3 - middle frame
        self.bottom_frame = ttk.Frame(self.root, padding="20", )
        self.bottom_frame.grid(row=3, rowspan=1)
        # system time
        self.system_time_var = StringVar()
        self.system_time_var.set(time.strftime("%H:%M:%S"))
        self.system_time_label_title = ttk.Label(self.bottom_frame,
                                                 text="Current system time:",
                                                 font=('Times New Roman', 10))
        self.system_time_label_title.grid(column=0, row=0, sticky=(N, W))
        self.system_time_label = ttk.Label(self.bottom_frame,
                                           text=self.system_time_var.get(),
                                           font=('Times New Roman', 10),
                                           textvariable=self.system_time_var)
        self.system_time_label.grid(column=1, row=0, sticky=(N, W))
        # action at time
        self.target_time_var = StringVar()
        self.target_time_label_title = ttk.Label(self.bottom_frame,
                                                 text="Action at:",
                                                 font=('Times New Roman', 10))
        self.target_time_label_title.grid(column=0, row=1, sticky=(N, W))
        self.target_time_label = ttk.Label(self.bottom_frame,
                                           text=self.target_time_var.get(),
                                           font=('Times New Roman', 10),
                                           textvariable=self.target_time_var)
        self.target_time_label.grid(column=1, row=1, sticky=(N, E))

        ### call functions
        self.update_system_time()

        ### run mainloop
        self.root.mainloop()

    def update_system_time(self):
        now = time.strftime("%H:%M:%S")
        self.system_time_var.set(now)
        self.root.after(1000, self.update_system_time)

    def update_action_text(self):
        self.perform_action_label.configure(text=f"{self.action_var.get()} in:")
        self.target_time_label_title.configure(text=f"{self.action_var.get()} at:")
        self.ACTION_SELECTED = True
        self.root.event_generate("<<Validate>>")

    def _validate_minutes(self, value):
        # print("validating")
        # print(self.MINUTES_VALIDATED)
        try:
            # print(value)
            val = int(value)
            if 0 < val <= 999:
                self.MINUTES_VALIDATED = True
                self.root.event_generate("<<Validate>>")
                return True
            else:
                self.MINUTES_VALIDATED = False
                self.root.event_generate("<<Validate>>")
                return False
        except ValueError:
            self.MINUTES_VALIDATED = False
            self.root.event_generate("<<Validate>>")
            return False

    def _validate_and_enable_buttons(self, *args):
        if self.ACTION_SELECTED and self.MINUTES_VALIDATED:
            self.enable_start_button()
        else:
            self.start_button.state(['disabled'])

    def start_button_command(self):
        self.disable_widgets_on_start()
        self.target_time_var.set(self.calculate_target_time())
        self.enable_stop_button()
        self.start_button.state(['!focus'])
        self.schedule_action()
        self.start_progress_bar()

    def stop_button_command(self):
        self.enable_widgets_on_stop()
        self.target_time_var.set("")
        self.disable_stop_button()
        self.stop_button.state(['!focus'])
        self.stop_scheduled_action()
        self.stop_progress_bar()

    def disable_widgets_on_start(self):
        self.action.state(['disabled'])
        self.minutes_spinner.state(['disabled'])
        self.start_button.state(['disabled'])

    def enable_widgets_on_stop(self):
        self.action.state(['!disabled'])
        self.minutes_spinner.state(['!disabled'])
        self.start_button.state(['!disabled'])

    def calculate_target_time(self):
        now = datetime.datetime.now()
        delta = datetime.timedelta(minutes=int(self.minutes_var.get()))
        future_time = now + delta
        return future_time.strftime("%H:%M:%S")

    def generate_validate_event(self, *args):
        if self.minutes_var.get():
            self.MINUTES_VALIDATED = True
            self.root.event_generate("<<Validate>>")

    def start_progress_bar(self):
        minutes_int = int(self.minutes_var.get())
        self.progress_bar.configure(maximum=minutes_int * 60.0, value=0.0)
        self.increment_progress_bar_by_one_every_second()

    def stop_progress_bar(self):
        self.progress_bar.after_cancel(self.PROGRESS_BAR_ID)
        self.progress_bar.configure(value=0.0)
        self.PROGRESS_BAR_ID = None

    def increment_progress_bar_by_one_every_second(self):
        self.progress_bar.configure(value=self.progress_bar['value'] + 1.0)
        self.PROGRESS_BAR_ID = self.progress_bar.after(1000, self.increment_progress_bar_by_one_every_second)
        # assignment fiecare secunda. cum as putea face pt a nu repeta ? poate nu e posibil? fiecare call de after
        # returneaza acelasi ID sau un ID diferit. Daca e diferit atunci nu as putea oricum

    def clear_minutes_field(self):
        self.minutes_var.set("")

    def enable_start_button(self):
        self.start_button.state(['!disabled'])

    def disable_start_button(self):
        self.start_button.state(['disabled'])

    def enable_stop_button(self):
        self.stop_button.state(['!disabled'])

    def disable_stop_button(self):
        self.stop_button.state(['disabled'])

    ## action funcs
    def schedule_action(self):
        action = self.action_var.get()
        if action == "Shutdown":
            subprocess.run(["shutdown", "/s", "/t", f"{int(self.minutes_var.get()) * 60}"])
            print("Shutdown was scheduled")

    def stop_scheduled_action(self):
        action = self.action_var.get()
        if action == "Shutdown":
            subprocess.run(["shutdown", "/a"])
            print("Shutdown was aborted")


if __name__ == '__main__':
    app = ShutdownTimer()
