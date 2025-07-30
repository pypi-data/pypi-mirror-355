import json
from pathlib import Path
import PIL
import PIL.Image
import PIL.ImageTk
import subprocess
import threading 
import yaml
import csv

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog
import tkinter.messagebox 

import painfacelib.common.video as vid
import painfacelib.ml.estimate as e 
import painfacelib.common as common


logger=common.logger.write 
color= common.Color

class LabelArray(tk.Frame):
    def __init__(self, master, labels_dict,  *args, **kwargs):
        tk.Frame.__init__(self, master, *args, **kwargs)
        
        i=0
        for k, v in labels_dict.items():
            lbl_key = tk.Label(master=self, text=k)
            lbl_val = tk.Label(master=self, text=v)
            lbl_key.grid(row=i, column=0)
            lbl_val.grid(row=i, column=1)
            i+=1

class ImageViewer(tk.Frame):
    def __init__(self, master, image_dir,  *args, **kwargs):
        tk.Frame.__init__(self, master, *args, **kwargs)
        self.image_dir = Path(image_dir)
        self.files = list(self.image_dir.glob('*.jpeg'))
        self.files = sorted(self.files, key=lambda x: x.name)


        self.lbl_image = tk.Label(master=self )
        self.lbl_image.grid(row=0,column=0,columnspan=2, pady=5, padx=20)
        self.current_index =  -1
        
        self.btn_prev = tk.Button(master=self,text=r"<", command=self.previous)
        self.btn_prev.grid(row=2, column=0, sticky='w')

        self.sv_count = tk.StringVar()
        self.sv_count.set(f"{self.current_index+1}/{len(self.files)}")
        self.lbl_counts = tk.Label(master=self, textvariable=self.sv_count)
        self.lbl_counts.grid(row=1,columnspan=2)

        self.btn_next = tk.Button(master=self,text=r">", command=self.next)
        self.btn_next.grid(row=2, column=1, sticky='e')
        
        self.next()

    def next(self):
        if self.current_index+1 < len(self.files):
            self.current_index+=1
            image = PIL.Image.open(self.files[self.current_index])
            image_tk = PIL.ImageTk.PhotoImage(image)
            self.lbl_image.config(image = image_tk)
            self.lbl_image.photo = image_tk
            self.sv_count.set(f"{self.current_index+1}/{len(self.files)}")
        else:
            pass

    def previous(self):
        if self.current_index > 0:
            self.current_index-=1
            image = PIL.Image.open(self.files[self.current_index])
            image_tk = PIL.ImageTk.PhotoImage(image)
            self.lbl_image.config(image = image_tk)
            self.lbl_image.photo = image_tk
            self.sv_count.set(f"{self.current_index+1}/{len(self.files)}")
        else:
            pass


class VideoLoading(ttk.Frame):
    def __init__(self, master, *args, configuration=None, **kwargs):
        tk.Frame.__init__(self, master, *args,  **kwargs)
        
        self.configuration = configuration
        
        self.current_parameters = self.configuration.get('last_parameters_gui')
        if self.current_parameters is None:
            self.current_parameters={
              'evaluation_frequency': '1 Frame every 30s',
              'fau_model_id': 'default',
              'mgs_model_id': 'default',
              'output_dir': '',
              'subject_type': 'c57bl/6',
              'video_path': ''
            }
            self.configuration.set('last_parameters_gui',self.current_parameters)

        
        self.sv_videofilename = tk.StringVar()
        self.video = None
        
        input_frame = ttk.Frame(master=self)
        input_frame.grid_rowconfigure(0, weight=1)
        input_frame.grid_columnconfigure(0, weight=1)

        self.button1 = ttk.Button(master=input_frame, text="Browse Files", width=15)
        self.button1.bind("<ButtonRelease-1>", self.buttonHandler)
        self.sv_video_info = tk.StringVar()
        self.lbl_video_info = ttk.Label(master=input_frame, textvariable = self.sv_video_info)
        self.sv_videofilename.set(self.current_parameters['video_path'])
        self.entry_video_filename = tk.Entry(master=input_frame, textvariable=self.sv_videofilename, width=85 )
        self.button1.grid(row=0,column=0, sticky='w')
        self.entry_video_filename.grid(row=0, column=1, sticky='e')

        self.btn_output_dir = ttk.Button(master=input_frame, text="Output Directory", width=15)
        self.btn_output_dir.bind('<ButtonRelease-1>', self.outputDirHandler)
        self.sv_output_dir = tk.StringVar()
        self.sv_output_dir.set(self.current_parameters['output_dir'])
        self.entry_output_dir = ttk.Entry(master=input_frame, textvariable=self.sv_output_dir, width=85)
        self.btn_output_dir.grid(row=1, column=0, sticky='w')
        self.entry_output_dir.grid(row=1, column=1, sticky="e")
        


        self.lbl_interval = ttk.Label(master=input_frame, text="Evaluation Freq")
        self.sv_interval = tk.StringVar()
        self.sv_interval.set(self.current_parameters['evaluation_frequency'])
        self.cmb_interval = ttk.Combobox(master=input_frame, textvariable=self.sv_interval, width=50)
        self.cmb_interval['state']='readonly'
        self.cmb_interval['values'] = ('1 Frame every 1s','1 Frame every 10s','1 Frame every 30s')
        self.lbl_interval.grid(row=2, column=0, sticky='ew')
        self.cmb_interval.grid(row=2, column=1, sticky='ew')

        self.lbl_animal = ttk.Label(master=input_frame, text="Species")
        self.sv_animal = tk.StringVar()
        self.sv_animal.set(self.current_parameters['subject_type'])
        self.cmb_animal = ttk.Combobox(master=input_frame, textvariable=self.sv_animal, width=50)
        self.cmb_animal['state']='readonly'
        self.cmb_animal['values'] = ('general','c57bl/6','crl:cd1(icr)')
        self.lbl_animal.grid(row=3, column=0, sticky='ew')
        self.cmb_animal.grid(row=3, column=1, sticky='ew')

        input_frame.grid(row=0,columnspan=2, sticky="ew")

        self.btn_evaluate = tk.Button(master=self, text="Evaluate Video", width=15,height=2,highlightbackground='green' )
        self.btn_evaluate.bind('<ButtonRelease-1>', self.processVideo)
        
        self.btn_evaluate.grid(row=1, columnspan=2,ipady=10, sticky='nsew')
 
        self.pb_process = ttk.Progressbar(master=self, orient="horizontal", mode="indeterminate")
        
        self.image_viewer = None
        self.tree= None
        self.tree_frame=None
        self.running = False

    def buttonHandler(self,event=None):
        fn = tk.filedialog.askopenfile(mode='r',
                                       title='Select a File',
                                       filetypes=[('Mpeg4 files', '*.mp4')]
                                       )
        if fn:
            self.sv_videofilename.set(Path(fn.name).__str__())
            # info = {
                # 'fps': self.video.fps,
                # 'number_of_frames': self.video.numberOfFrames,
                # 'duration(s)': int(self.video.numberOfFrames / self.video.fps)
            # }
            # self.sv_video_info.set(json.dumps(info,indent=4))
            #self.lbl_video_info.grid(row=5,column=0, columnspan=5)


            
            # if self.image_viewer is not None:
                # self.image_viewer.grid_forget()

    def outputDirHandler(self, event=None):
        fn = tk.filedialog.askdirectory(title='Select a Directory')
        if fn:
            self.sv_output_dir.set(fn)
            if Path(fn).joinpath('visualization').exists():
                #self.add_image_viewer()
                self.add_csv_viewer()

    def processVideo(self, event=None):
        if self.running:
            print("Process is already running ... ")
            return

        self.current_parameters['video_path'] = str(self.sv_videofilename.get())
        self.current_parameters['output_dir'] = str(self.sv_output_dir.get())
        self.current_parameters['evaluation_frequency'] = str(self.sv_interval.get())
        self.current_parameters['subject_type'] = str(self.sv_animal.get())

        print(self.current_parameters)

        self.video = vid.VideoProcessor(self.current_parameters['video_path'])
        self.configuration.set('last_parameters_gui', self.current_parameters)
        if self.tree_frame is not None:
            self.tree_frame.grid_forget()
        th1 = threading.Thread(target=self._thread_process, args=())
        
        th1.start()
    
    def enable(self):
        for child in self.winfo_children():
            try:
                child.configure(state='normal')
            except:
                pass

    def disable(self):
        for child in self.winfo_children():
            try:
                child.configure(state='disable')
            except:
                pass
    
    def _compute_frequency(self, sv_freq):
        fq = sv_freq.get()
        fq = float(fq.split()[-1].replace('s',''))
        interval = fq * self.video.fps
        return int(interval)

    def add_image_viewer(self):
        viz_dir = Path(self.sv_output_dir.get()).joinpath('visualization').__str__()
        self.image_viewer = ImageViewer(master=self, image_dir = viz_dir )
        self.image_viewer.grid(row=5, columnspan=2)

    def add_csv_viewer(self, csv_filename):

        self.tree_frame = ttk.Frame(master=self)
        self.tree_frame.grid(row=4, columnspan=2, sticky='nsew')
                # Configure tree frame grid weights
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(master=self.tree_frame)
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        # Create scrollbars
        v_scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        v_scrollbar.grid(row=0, column=1, sticky="ns")

        h_scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        # Configure treeview scrollbars
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        with open(csv_filename,'r') as f:
            csv_reader = csv.reader(f, delimiter=',')
            headers = next(csv_reader)
            self.tree['columns'] = headers
            self.tree['show'] = 'headings'
            for header in headers:
                self.tree.heading(header, text=header)
                self.tree.column(header, width=120, minwidth=80) 
            for (rn, row) in enumerate(csv_reader, 1):
                self.tree.insert("", "end", values=row)

    def _thread_process(self):
        self.running = True
        self.disable()
        self.pb_process.grid(row=4,column=0, columnspan=100)
        self.pb_process.start(50)
        config_dir = Path.home().joinpath('.painface')
        subject_type = str(self.sv_animal.get())

        subject_type_digest = subject_type.replace('/','').replace(':','').replace('(','').replace(')','')
        fau_model_dir = config_dir.joinpath('models').joinpath(subject_type_digest).joinpath('fau').joinpath('default')
        mgs_model_dir = config_dir.joinpath('models').joinpath(subject_type_digest).joinpath('pain-mgs').joinpath('default')
        payload = {
            'type': 'datasetdir',
            'fau_model_dir': fau_model_dir,
            'mgs_model_dir': mgs_model_dir,
            'output_dir': self.sv_output_dir.get(),
            'data_path': self.sv_videofilename.get(),
            'subject_type': self.sv_animal.get(),
            'study_type': 'pain-mgs',
            'interval': self._compute_frequency(self.sv_interval),
            'gpu': 0,
            'visualize': True,
            'dev': False
        }
        res = e.estimate_video(payload)
        tk.messagebox.showinfo(message="Evaluation Finished")
        self.pb_process.grid_forget()
        if res:
            #self.add_image_viewer()
            logger(yaml.dump(res), color.INFO)
            self.add_csv_viewer(res['filename'])
        self.enable()
        self.running=False


        


