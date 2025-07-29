from textual.app import App
from textual.widgets import (Header,
                             Footer,
                             ListItem,
                             ListView,
                             TextArea,
                             Button,
                             DataTable,
                             Input,
                             DirectoryTree,
                             Static,
                             Collapsible,
                             Select,
                             MarkdownViewer,
                              TabbedContent,
                             Label)
import bioplumber
from bioplumber import config
from textual.screen import Screen
from textual.containers import Container,Horizontal,Vertical
from bioplumber import (configs,
                        bining,
                        files,
                        qc,
                        assemble,
                        slurm,
                        abundance,
                        taxonomy,
                        alignment,
                        dereplication)
from textual import on, work
from textual.binding import Binding
from textual.validation import Number
import pandas as pd
import time
import pathlib
import datetime

class DirectoryReference(Container):
    def compose(self):
        yield Vertical(
        Container(
                Vertical(
                    Input(placeholder="Base Directory",id="base_dir_input"),
                    DirectoryTree("/",id="folder_tree"),
                    TextArea(id="selected_dir")
                        )
                ))


    def on_input_changed(self, event: Input.Changed):
        try:
            self.query_one("#folder_tree").path=event.value
        except Exception as e:
            pass
    
    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected):
        self.query_one("#selected_dir").text=str(event.path)
        
class Manager(Container):
    def compose(self):
            yield Vertical(Horizontal(TextArea.code_editor(text="",
                                             language="python",
                                             id="io_code_editor",
                                             show_line_numbers=True),
                                             DirectoryReference(id="dir_ref")),
             Horizontal(
                  Input(placeholder="Variable Name",id="variable_input_render")
                  ,Button("Render Variable",id="render_button"),
                
                  id="render_variable"
             ),
             DataTable(id="output_text"),
             Horizontal(
                  Input(placeholder="Save Directory",id="variable_input_save"),
                  Button("Save",id="save_button"),
                  Button("Save Script",id="save_script_button"),
                  id="save_variable"
             ))
        
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "render_button":
            try:
            
                code = self.query_one("#io_code_editor").text
                variable=self.query_one("#variable_input_render").value
                sc={}
                exec(code,locals=sc)
                data=sc[variable]
                if isinstance(data, pd.DataFrame):
                    temp_data = data.to_dict(orient="list")
                    table = self.query_one("#output_text")
                    table.remove_children()
                    table.clear(columns=True)
                    table.add_columns(*[str(i) for i in temp_data.keys()])
                    table.add_rows(list(zip(*temp_data.values())))

                else:
                    table=self.query_one("#output_text")
                    table.remove_children()
                    table.clear(columns=True) 
                    table.add_columns("Variable Name","Value")
                    table.add_rows([(variable,data)])
                    
                    
            except Exception as e:
                self.query_one("#output_text").mount(TextArea(text=f"Error rendering variable\n{e}"))
                
        if event.button.id == "save_button":
            try:
                code = self.query_one("#io_code_editor").text
                variable=self.query_one("#variable_input_render").value
                sc={}
                exec(code,locals=sc)
                data=sc[variable]
                if isinstance(data, pd.DataFrame):
                    data.to_csv(self.query_one("#variable_input_save").value,index=False)
                else:
                    with open(self.query_one("#variable_input_save").value,"w") as f:
                        f.write(str(data))
                self.query_one("#output_text").mount(TextArea(text=f"Variable {variable} saved successfully"))
            except Exception as e:
                self.query_one("#output_text").mount(TextArea(text=f"Error saving variable\n{e}"))
        if event.button.id == "save_script_button":
            try:
                code = self.query_one("#io_code_editor").text
                with open((pathlib.Path(bioplumber.get_config()["base_directory"])/"scripts")/f"{datetime.datetime.now()}.txt","w") as f:
                    f.write(code)
                self.mount(Label("[green]Script saved successfully",id="script_save_label"))
                self.set_timer(3, lambda: self.query_one("#script_save_label").remove())
            except Exception as e:
                self.query_one("#output_text").mount(Label(f"[red]Error saving script\n{e}",id="script_save_failed_label"))
                self.set_timer(3, lambda: self.query_one("#script_save_failed_label").remove())

        
class History(Container):
    def compose(self):
        yield Vertical(
            ListView(*[ListItem(Static(f"{i}")) for i in sorted(get_history_files(bioplumber.get_config()["base_directory"]),reverse=True)],id="history_list_view"),
            TextArea.code_editor(text="",
                                             language="python",
                                             id="history_text_area",
                                             show_line_numbers=True),
                                             
        )

    def on_list_view_selected(self, event: ListView.Selected):
        file_name = event.item.children[0].renderable
        file_path = pathlib.Path(bioplumber.get_config()["base_directory"]) / "scripts" / file_name
        if file_path.exists():
            with open(file_path, "r") as f:
                content = f.read()
            self.query_one("#history_text_area").text = content
        else:
            self.query_one("#history_text_area").text = f"File {file_name} does not exist."

    

class MGRScreen(Screen):
    def __init__(self):
        super().__init__()
        self.manager = Manager(id="manager_container")
        self.history = History(id="history_container")
    
    def compose(self):

        yield Header(show_clock=True)
        with TabbedContent("Manager","History",id="tabs"):
                yield self.manager
                yield self.history
                
        yield Footer()
    
    @on(TabbedContent.TabActivated)
    async def refresh_history(self):
        self.history.query_one("#history_list_view").remove_children()
        self.history.query_one("#history_list_view").mount(
            *[ListItem(Static(f"{i}")) for i in sorted(get_history_files(bioplumber.get_config()["base_directory"]),reverse=True)]
        )

    


                
class SetBaseDir(Screen):
    def compose(self):
        yield Vertical(
            Header(show_clock=True),
            Static("Please set a base directory to continue"),
            Input(placeholder="Base Directory",id="base_dir_input"),
            Button("Set Base Directory",id="set_base_dir_button"),
            Footer()
        )
    
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "set_base_dir_button":
            base_dir = self.query_one("#base_dir_input").value
            try:
                pathlib.Path(base_dir).mkdir(parents=True, exist_ok=True)
                if not (pathlib.Path(base_dir)/"scripts").exists():
                    (pathlib.Path(base_dir)/"scripts").mkdir()
                bioplumber.set_base_directory(base_dir)
                self.dismiss()
            except Exception as e:
                self.mount(Label(f"[Red]Error setting base directory: {e}"))
        

class FileManager(App):
    CSS_PATH = "tui_css.tcss"
    @work(exclusive=True)
    async def on_mount(self):
        self.theme="gruvbox"
        print("Bioplumber File Manager")
        if config["base_directory"]=="":
            await self.push_screen(SetBaseDir(),"base-dir-conf",wait_for_dismiss=True)
            
        self.push_screen(MGRScreen(),"mgr-screen" )

def get_history_files(base_dir):
    history_dir = pathlib.Path(base_dir) / "scripts"
    if not history_dir.exists():
        return []
    return [f.name for f in history_dir.glob("*.txt") if f.is_file()]

def main():
    mgr=FileManager()
    mgr.run()
    
if __name__ == '__main__':
    main()


