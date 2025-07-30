from textual import on, events, work
from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll, Horizontal, Vertical, Center
from textual.widgets import (Input,
                            DirectoryTree,
                            Button, 
                            Header, 
                            Footer, 
                            Static, 
                            RichLog, 
                            DataTable,
                            Select)
from textual_fspicker import FileOpen, SelectDirectory, Filters

import yaml
import csv
import asyncio
import time
import traceback
from pathlib import Path
import painfacelib.common as common
import painfacelib.common.utils as utils

class Application(App):
    """ Painface TUI App """
    CSS_PATH="tui.tcss"
    BINDINGS = [
        ("q", "quit", "Quit")
    ]
    
    def __init__(self, *args,config={}, **kwargs):
        super().__init__(*args,**kwargs)
        self.config = config
        
        self.current_parameters = self.config.get('last_parameters')
    
        if self.current_parameters is None:
            self.current_parameters = {
                'video_path': '',
                'output_dir': '',
                'evaluation_frequency': 900,
                'subject_type': 'c57bl/6',
            }
            self.config.set('last_parameters', self.current_parameters)


    def compose(self) -> ComposeResult:
        """ Composing UI Here """
        self.inputfile =  Input(placeholder="File Path", 
                                id="inp_filepath", 
                                value=self.current_parameters['video_path'], 
                                classes="disable-on-compute")
        self.button_openfile = Button(label="Select Video", 
                                    id="fileopen",
                                    classes="filedialog disable-on-compute" , 
                                    variant="primary")
        self.output_dir = Input(placeholder="Output Dir", 
                                id="output_dir", 
                                value=self.current_parameters['output_dir'], 
                                classes="disable-on-compute")
        self.button_selectdir = Button(label="Output Dir", 
                                        id="select_dir",
                                        classes="filedialog disable-on-compute",  
                                        variant="primary")
        
        self.current_parameters.setdefault('subject_type', 'c57bl/6')
        self.select_animal = Select( value = self.current_parameters['subject_type'],
                                        prompt="Subject Type",
                                        options = [
                                        ('General','general'),
                                        ('c57bl/6','c57bl/6'),
                                        ('crl:cd1(icr)', 'crl:cd1(icr)'),
                                        # ('129/SvEv', '129/SvEv'),
                                        # ('Rat', 'rat'),
                                        # ('Horse', 'horse'),
                                        ],
                                        id="select_animal",
                                        classes="disable-on-compute")
        self.current_parameters.setdefault('evaluation_frequency', 900)
        self.select_frequency = Select( value = self.current_parameters['evaluation_frequency'],
                                        prompt="Evaluation Frequency",
                                        options = [('1 Frame every 1s',30),
                                        ('1 Frame every 10s', 300),
                                        ('1 Frame every 30s', 900)
                                        ],
                                        id="select_frequency",
                                        classes="disable-on-compute")
        
        self.current_parameters.setdefault('fau_model_id','default')
        self.select_model_id_fau = Select( value = self.current_parameters['fau_model_id'],
                                        prompt="Face Model ID",
                                        options = [('Default','default'),
                                        ],
                                        id="select_model_id_fau",
                                        classes="disable-on-compute")

        self.current_parameters.setdefault('mgs_model_id','default')
        self.select_model_id_mgs = Select( value = self.current_parameters['mgs_model_id'],
                                        prompt="Grimace Model ID",
                                        options = [('Default','default'),
                                        ],
                                        id="select_model_id_mgs",
                                        classes="disable-on-compute")

        self.button_compute = Button(label="Compute", 
                                    id="btn_compute", 
                                    classes="buttons disable-on-compute", 
                                    variant="success")
        self.process_log = RichLog(id="process_log")

        self.datatable = DataTable(id="datatable")

        self.inputfile.value = self.current_parameters['video_path']
        self.output_dir.value = self.current_parameters['output_dir']

        with Container(id="grid-container"):
            yield Static("PainFace", classes="custom-header")
            with Horizontal(id="row1"):
                yield self.button_openfile
                yield self.inputfile
            # yield DirectoryTree("/")
            with Horizontal(id="row2"):
                yield self.button_selectdir
                yield self.output_dir

            with Horizontal(id="row3"):
                yield Button(label="Animal",id="lbl_animal", disabled=True)
                yield self.select_animal
                yield Button(label="Eval.Frequency",id="lbl_frequency", disabled=True)
                yield self.select_frequency

            with Horizontal(id="rowr4"):
                yield Button(label="FAU Model",id="lbl_fau_model", disabled=True)
                yield self.select_model_id_fau
                yield Button(label="MGS Model",id="lbl_mgs_model", disabled=True)
                yield self.select_model_id_mgs

            with Center(id="center-container"): 
                yield self.button_compute
            
            yield self.datatable

            with Vertical():
                yield self.process_log

            yield Footer()
            yield Static("2025 Zylka Lab, all rights reserved.", classes="custom-footer")
    
    def on_mount(self) -> None:
        self.process = None

    @on(Select.Changed, '#select_animal')
    def select_animal_changed(self, event: Select.Changed)-> None:
        self.current_parameters['subject_type'] = event.value
        model_root_dir = self.config.get('model_dir')
        subject = self.select_animal.value
        fau_options =  [ (x.name,x.name) for x in utils.get_model_list(model_root_dir, subject, 'fau' ) ]
        mgs_options = [ (x.name,x.name) for x in utils.get_model_list(model_root_dir, subject, 'pain-mgs' ) ]
        self.select_model_id_fau.set_options(fau_options)
        self.select_model_id_mgs.set_options(mgs_options)

        if len(fau_options)>0:
            if ('default','default') in fau_options:
                def_value_fau = 'default'
            else:
                def_value_fau = fau_options[0][1]
            self.select_model_id_fau.value = def_value_fau
            
        if len(fau_options)>0:
            if ('default','default') in mgs_options:
                def_value_mgs = 'default'
            else:
                def_value_fau = mgs_options[0][1]
            self.select_model_id_mgs.value = def_value_mgs


        #self.process_log.write(str(self.select_model_id_mgs.options))

    @on(Select.Changed, '#select_frequency')
    def select_freq_changed(self, event: Select.Changed)-> None:
        self.current_parameters['evaluation_frequency'] = event.value

    @on(Input.Changed, '#inp_filepath')
    def input_file_changed(self, event: Input.Changed)-> None:
        self.current_parameters['video_path'] = event.value

    @on(Input.Changed, '#output_dir')
    def input_dir_changed(self, event: Input.Changed)-> None:
        self.current_parameters['output_dir'] = event.value

    @on(Button.Pressed, "#btn_compute")
    async def compute_button_pressed(self, event: Button.Pressed) -> None: 
        if self.process and not self.process.returncode:
            self.process_log.write('Already in processing')
            return
        
        for wg in self.query('.disable-on-compute'):
            wg.disabled= True

        if self.config.get('model_dir') is None:
            self.config.set('model_dir', Path(self.config.get('config_dir')).joinpath('models').__str__() )

        fau_model_dir = utils.get_model_directory(self.config.get('model_dir'), self.select_animal.value, 'fau', self.select_model_id_fau.value)
        mgs_model_dir = utils.get_model_directory(self.config.get('model_dir'), self.select_animal.value, 'pain-mgs', self.select_model_id_mgs.value)
        
        self.current_parameters['fau_model_dir'] = fau_model_dir
        self.current_parameters['mgs_model_dir'] = mgs_model_dir

        self.process_log.write( yaml.dump(self.current_parameters) )
        self.config.set('last_parameters', self.current_parameters)
        self.datatable.clear()
        executable = Path('painface')

        

       
        cmd = [ 
               executable.__str__(),
               'run',
               self.inputfile.value,
               '--output-dir', self.output_dir.value,
               '--fau-model-dir', fau_model_dir,
               '--mgs-model-dir', mgs_model_dir,
               '-i', str(self.current_parameters['evaluation_frequency']),
               '-g', '0',
               '--visualize',
               '--subject-type', self.select_animal.value,
               '--study-type', 'pain-mgs'
              ]
        self.process = await asyncio.create_subprocess_exec(*cmd,
                                                            cwd= executable.parent,
                                                            stdout= asyncio.subprocess.PIPE,
                                                            stderr= asyncio.subprocess.STDOUT,
                                                           )
        
        self.process_log.write(f"Process begins : {' '.join(cmd)}")
        
        while True:
            line = await self.process.stdout.readline()
            if not line:
                break
            self.process_log.write(line.strip())

        await self.process.wait()
        self.process_log.write(f"Process finished with code : {self.process.returncode}")
        self.process = None
        for wg in self.query('.disable-on-compute'):
            wg.disabled= False 
    
        ## read result csv
        try:
            csv_path = Path(self.output_dir.value).joinpath('result/result.csv')
            with open(csv_path,'r') as f:
                csv_reader = csv.reader(f)
                headers = next(csv_reader)
                for header in headers:
                    self.datatable.add_column(header)

                for row in csv_reader:
                    self.datatable.add_row(*row)
        except Exception as e:
            self.process_log.write(str(e)) 


    @on(Button.Pressed, "#fileopen")
    @work
    async def file_button_pressed(self, event: Button.Pressed) -> None:
        """ When button is pressed for the file open"""
        out  = await self.push_screen_wait(FileOpen(    location=Path(self.inputfile.value).parent,
                                                                            filters=Filters(
                                                                                ("MP4", lambda p: p.suffix.lower() == '.mp4'),
                                                                            )
                                                                       )
                                                                )
        if out is not None:
            self.inputfile.value = str(out)
            self.current_parameters['video_path'] = self.inputfile.value
            self.config.set('last_parameters', self.current_parameters)

    @on(Button.Pressed, "#select_dir")
    @work
    async def dir_button_pressed(self, event: Button.Pressed) -> None:
        """ When button is pressed for the file open"""
        out =  await self.push_screen_wait(SelectDirectory(location=Path(self.output_dir.value).parent))
        if out is not None:
            self.output_dir.value = str(out)
            self.current_parameters['output_dir'] = self.output_dir.value
            self.config.set('last_parameters', self.current_parameters)

async def main(options={}):
    Application().run()

if __name__=='__main__':
    asyncio.run(main())
