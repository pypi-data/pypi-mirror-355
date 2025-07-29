import os
class colorize:
    def __init__(self):
        self.black=30
        self.red=31
        self.green=32
        self.yellow=33
        self.blue=34
        self.magenta=35
        self.cyan=36
        self.white=37
    
    def colorize(self, color:int):
        return f"\033[{color}m"
    def reset(self):
        return "\033[0m"

class ExtraContents:
    def __init__(self, optionals: dict, modName: str):
        self.optionals=optionals
        self.modName=modName
        self.Maps_py=f"""from StardewValley.Data.SVModels.Maps import Maps as MapsModel
from StardewValley import Helper, EditMap, ToArea, MapTiles, EditData, WarpPosition

from StardewValley.Data.XNA import Position

class Maps(MapsModel):
    def __init__(self, mod: Helper):
        super().__init__(mod)
        self.mod.assetsFileIgnore=[]
    
    def contents(self):
        super().contents()

"""
        self.set_contents()
    
    def write_file(self, path, content):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def set_contents(self):
        self.map_imports="from Maps.Maps import Maps" if self.optionals["Maps"] else ""
        self.npcs_imports="""import NPCS as NPCs_List
from StardewValley.Data.SVModels.NPCs import NPCs
""" if self.optionals["NPCs"] else ""
        self.dialogues_imports="""import Dialogues as Dialogues_List
from StardewValley.Data.SVModels.Dialogues import Dialogues
""" if self.optionals["Dialogues"] else ""
        self.schedules_imports="""import Schedules as Schedules_List
from StardewValley.Data.SVModels.Schedules import Schedules
""" if self.optionals["Schedules"] else ""
        self.events_imports="""import Events as Events_list
from StardewValley.Data.SVModels.Events import Events
""" if self.optionals["Events"] else ""
        
        self.map_contents="Maps(self)" if self.optionals["Maps"] else ""
        self.npcs_contents="NPCs(mod=self, NPCs_List=[])" if self.optionals["NPCs"] else ""
        self.dialogues_contents="Dialogues(mod=self, Dialogues_List=[])" if self.optionals["Dialogues"] else ""
        self.schedules_contents="Schedules(mod=self, Schedules_List=[])" if self.optionals["Schedules"] else ""
        self.events_contents="Events(mod=self, Events_list=[])" if self.optionals["Events"] else ""
        self.contents()
    def contents(self):
        if self.optionals["Dialogues"]:
            os.makedirs(os.path.join(self.modName, "Dialogues"))
            self.write_file(os.path.join(self.modName, "Dialogues", "__init__.py"), "")
        if self.optionals["Events"]:
            os.makedirs(os.path.join(self.modName, "Events"))
            self.write_file(os.path.join(self.modName, "Events", "__init__.py"), "")
        if self.optionals["Maps"]:
            os.makedirs(os.path.join(self.modName, "Maps"))
            self.write_file(os.path.join(self.modName, "Maps", "Maps.py"), self.Maps_py)
        if self.optionals["NPCs"]:
            os.makedirs(os.path.join(self.modName, "NPCS"))
            self.write_file(os.path.join(self.modName, "NPCS", "__init__.py"), "")
        if self.optionals["Schedules"]:
            os.makedirs(os.path.join(self.modName, "Schedules"))
            self.write_file(os.path.join(self.modName, "Schedules", "__init__.py"), "")
