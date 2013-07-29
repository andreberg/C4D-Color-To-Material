# -*- coding: utf-8  -*-
# 
#  Color To Material
#  CINEMA 4D Python Plugins
#  
#  Created by André Berg on 2011-03-22.
#  Copyright 2011 Berg Media. All rights reserved.
#  
#  Version 1.0
#  Updated: 2013-07-29
#
#  (license details see end of file)
#
#  Summary: Convert an object's layer or object color to 
#  a newly assigned material with that same color.
# 
#  Modus Operandi
#
#  First, loop through all the objects that are selected
#  in the object manager and get the layer the object belongs to.
#  Then, create a new material and set the material's color channel to
#  the same RGB color as the color of the layer.
#  Create a new texture tag on the object and assign the corresponding
#  material.
#  Do not create a new material if a material with name "RGB x,y,z"
#  already exists. Use existing material instead.
#  
#  Tip: If you want all the new materials that will be created added to
#  an existing material layer, in the Material Manager switch to that layer
#  before running the script. Any materials created will be assigned to this 
#  layer automatically. 
#
#  TODO: in the future the material layer new materials are assigned to 
#  should be choosable in the interface).
#
#

import re
import os
import math
import time
import c4d
from c4d import plugins, bitmaps, gui, documents

# from c4d.utils import *
#from c4d import *

DEBUG = True

if DEBUG:
    import pprint
    pp = pprint.PrettyPrinter(width=200)
    PP = pp.pprint
    PF = pp.pformat

CR_YEAR = time.strftime("%Y")

# -------------------------------------------
#               PLUGING IDS 
# -------------------------------------------

# unique ID
ID_COLORTOMATERIAL = 1026870


# Element IDs
IDD_DIALOG_SETTINGS    = 10001
IDC_GROUP_WRAPPER      = 10002
IDC_GROUP_SETTINGS     = 10003
IDC_STATIC_CHANNEL     = 10004
IDC_COMBO_CHANNEL      = 10005
IDC_STATIC_SOURCE      = 10006
IDC_COMBO_SOURCE       = 10007
IDC_CHECK_CLEARPREV    = 10008
IDC_GROUP_BUTTONS      = 10009
IDC_BUTTON_CANCEL      = 10010
IDC_BUTTON_DOIT        = 10011
IDC_CHECK_CHILDREN     = 10012
IDC_GROUP_SETTINGS2    = 10013
IDC_MENU_ABOUT         = 30001




# String IDs
IDS_PLUGIN_VERSION = 1.0
IDS_PLUGIN_NAME = "Color To Material"
IDS_HELP_STRING = "Create and assign a material with the same color as an object's layer or viewport color"

IDS_DIALOG_TITLE   = "Color To Material"
IDS_BUTTON_CANCEL  = "Cancel"
IDS_BUTTON_DOIT    = "Do It!"
IDS_STATIC_CHANNEL = "Material Channel"
IDS_STATIC_SOURCE  = "Color Source"
IDS_GROUP_SETTINGS = "Settings"
IDS_CHECK_CLEARPREV= "Clear previous tags"

IDS_MENU_INFO      = "Info"
IDS_MENU_ABOUT     = "About..."

IDS_ABOUT   = """(C) %s Andre Berg (Berg Media)
All rights reserved.

Version %s

Color To Material is a Python plugin that allows 
for making the Display > Layer Color viewport,
as well as the Basic > Use Color object settings 
renderable by assigning materials with the target
material channel set to the object or layer color.
 
Use at your own risk! 

It is recommended to try out the plugin 
on a spare copy of your data first.
""" % (CR_YEAR, IDS_PLUGIN_VERSION)

# --------------------------------------------------------
#                      Defaults 
# --------------------------------------------------------

RGB_8BIT_MULT = 255

# no idea why these symbols are there in console and otherwise in scripts 
# but for plugins the c4d module doesn't have attributes called MATERIAL_COLOR_COLOR etc. 
# so I need to hardcode the values :(
MATERIAL_COLOR_COLOR = 2100
MATERIAL_LUMINANCE_COLOR = 2300

TARGET_CHANNEL =  MATERIAL_COLOR_COLOR       
COLOR_SOURCE = 0 # 0 = LAYER, 1 = OBJECT

# "Enum"
COLOR_SOURCE_LAYER = 1
COLOR_SOURCE_OBJECT = 2

TARGET_CHANNEL_COLOR = 1
TARGET_CHANNEL_LUMINANCE = 2

# ----------------------------------------------------------------
#                      Helper Functions 
# ----------------------------------------------------------------

def ColorToString(col):
    return "RGB " \
    + str(int(math.floor(col.x * RGB_8BIT_MULT))) + "," \
    + str(int(math.floor(col.y * RGB_8BIT_MULT))) + "," \
    + str(int(math.floor(col.z * RGB_8BIT_MULT)))

def FindLastTag(op):
    ttag = op.GetFirstTag()
    ttag1 = None
    while(ttag):
        ttag1 = ttag;
        ttag = ttag.GetNext()
    if ttag1 is not None:
        return ttag1
    else:
        return None

def OpHasTextureTagWithMaterialName(op, str, isregex=False):
    ttag = op.GetFirstTag()
    while (ttag):
        if isinstance(ttag, c4d.TextureTag):
            mname = ttag.GetMaterial().GetName()
            if isregex:
                match = re.match(str, mname)
                if match: return True
            else:
                if mname == str: return True
        ttag = ttag.GetNext()
        if ttag is None: 
            break
    return False

def FindMaterial(str, isregex=False, doc=None):
    if doc is None: 
        doc = c4d.documents.GetActiveDocument()
    mats = doc.GetMaterials()
    if mats:
        if isregex:
            for mat in mats:
                mname = mat.GetName()
                match = re.match(str, mname)
                if match: return mat
        else:      
            for mat in mats:
                if mat.GetName() == str:
                    return mat
    return None



# ------------------------------------------------------
#                   User Interface 
# ------------------------------------------------------

# Snippets

# self.AddStaticText(ID, c4d.BFH_CENTER | c4d.BFV_CENTER, name=IDS) # id, flags[, initw=0][, inith=0][, name=""][, borderstyle=0]

class ColorToMaterialDialog(gui.GeDialog):
        
    def CreateLayout(self):
        plugins.GeResource().Init(os.path.dirname(os.path.abspath(__file__)))
        self.LoadDialogResource(IDD_DIALOG_SETTINGS, flags=c4d.BFH_SCALEFIT)
        
        # Menu
        self.MenuFlushAll()
        self.MenuSubBegin(IDS_MENU_INFO)
        self.MenuAddString(IDC_MENU_ABOUT, IDS_MENU_ABOUT)
        self.MenuSubEnd()
        
        self.MenuFinished()
        return True
    
    def InitValues(self):
        self.SetLong(IDC_COMBO_CHANNEL, 1)
        self.SetLong(IDC_COMBO_SOURCE, 1)
        self.SetLong(IDC_CHECK_CLEARPREV, 1)
        self.SetLong(IDC_CHECK_CHILDREN, 1)
        return True
    
    def Command(self, id, msg):
        if id == IDC_BUTTON_DOIT:
            cursrc = self.GetLong(IDC_COMBO_SOURCE)
            curchan = self.GetLong(IDC_COMBO_CHANNEL)
            clear = self.GetLong(IDC_CHECK_CLEARPREV)
            children = self.GetLong(IDC_CHECK_CHILDREN)
            scriptvars = {
                'source': cursrc,
                'channel': curchan,
                'clearprev': clear,
                'children': children
            }
            script = ColorToMaterialScript(scriptvars)
            if DEBUG:
                print "do it: %r" % msg
                print "script = %r" % script
                print "scriptvars = %r" % scriptvars
            return script.run()
        elif id == IDC_BUTTON_CANCEL:
            if DEBUG:
                print "cancel: %r" % msg
            self.Close()
        elif id == IDC_MENU_ABOUT:
            c4d.gui.MessageDialog(IDS_ABOUT)
        else:
            if DEBUG:
                print "id = %s" % id
        
        return True
    


# ------------------------------------------------------
#                   Command Script 
# ------------------------------------------------------
class ColorToMaterialScript(object):
    """Run when the user clicks the DoIt! button."""
    def __init__(self, scriptvars=None):
        super(ColorToMaterialScript, self).__init__()
        self.data = scriptvars
    
    def run(self):
        doc = documents.GetActiveDocument()
        doc.StartUndo()
        
        chan = self.data['channel']
        src = self.data['source']
        clr = self.data['clearprev'] == 1
        chld = self.data['children'] == 1
        
        if chan == TARGET_CHANNEL_COLOR:
            TARGET_CHANNEL = MATERIAL_COLOR_COLOR
        elif chan == TARGET_CHANNEL_LUMINANCE:
            TARGET_CHANNEL = MATERIAL_LUMINANCE_COLOR
        if src == COLOR_SOURCE_LAYER:
            COLOR_SOURCE = 0
        elif src == COLOR_SOURCE_OBJECT:
            COLOR_SOURCE = 1
        
        if chld: 
            c4d.CallCommand(100004768) # Select Children
        
        sel = doc.GetSelection()
        if sel is None: return False
        
        for op in sel:
            lay = op[c4d.ID_LAYER_LINK]
            opusescolor = op[c4d.ID_BASEOBJECT_USECOLOR]
            col = None
            layname = None
            if COLOR_SOURCE == 1 and (opusescolor > 0 and opusescolor < 3):  # 0 = off, 1 = auto, 2 = always, 3 = layer
                # use the object's color as color source
                col = op[c4d.ID_BASEOBJECT_COLOR]
            elif COLOR_SOURCE == 0 or opusescolor == 3:
                # use the layer the object belongs to as color source
                if lay is None: continue # if the object has no layer get the next selected object
                col = lay[c4d.ID_LAYER_COLOR]
                layname = lay.GetName()
            else:
                # continue with next object
                continue
            
            colstr = ColorToString(col)
            if col:
                # see if a material with name "RGB x,y,z" already exists
                mat = FindMaterial(colstr, False, doc)
                if mat is None:
                    # if not create a new material
                    c4d.StopAllThreads()
                    c4d.CallCommand(13015) # New Material
                    mat = doc.GetFirstMaterial()
                    if mat is None: return False
                    doc.AddUndo(c4d.UNDO_NEW, mat)
                else:
                    if DEBUG: print "material %s already exists" % mat.GetName()
                                
                # set material name to "RGB x,y,z"
                mat.SetName(colstr)
                
                # set the color channel to the RGB values of the layer
                mat[TARGET_CHANNEL] = col
                
                # determine channel to switch off (everything other than chosen)
                if TARGET_CHANNEL == MATERIAL_COLOR_COLOR:
                    onchan = c4d.MATERIAL_USE_COLOR
                    offchans = [c4d.MATERIAL_USE_LUMINANCE]
                elif TARGET_CHANNEL == MATERIAL_LUMINANCE_COLOR:
                    onchan = c4d.MATERIAL_USE_LUMINANCE
                    offchans = [c4d.MATERIAL_USE_COLOR]
                
                # enable material channel, disable other(s)
                mat[onchan] = True
                for offchan in offchans:
                    mat[offchan] = False
                
                # find out if the object already has a tag which references the proper layer material
                if not OpHasTextureTagWithMaterialName(op, colstr):
                    if DEBUG: print "colstr = %s" % colstr
                    c4d.StopAllThreads()
                    if clr:
                        for tag in op.GetTags():
                            if tag.GetType() == c4d.Ttexture:
                                n = tag.GetMaterial().GetName()
                                if n != colstr and re.match(r'RGB \d+,\d+,\d+', n):
                                    if DEBUG:
                                        print "removing previous tag with name %s" % n
                                    tag.Remove()
                                    c4d.EventAdd()
                    textag = c4d.TextureTag() # was: op.MakeTag(c4d.Ttexture)
                    if textag is None: return False
                    lasttag = FindLastTag(op)
                    if lasttag is not None:
                        if DEBUG: print "lasttag = %s" % lasttag.GetName()
                    doc.AddUndo(c4d.UNDO_TAG_NEW, textag);
                    doc.AddUndo(c4d.UNDO_TAG_DATA, textag);
                    textag.SetMaterial(mat)
                    if lasttag is not None:
                        op.InsertTag(textag, lasttag)
                    else:
                        op.InsertTag(textag)
                    #textag[TEXTURETAG_PROJECTION] = 6 # Set projection to UVW
                
        c4d.EventAdd()
        doc.EndUndo()
        
        return True
        


# ----------------------------------------------------
#                      Main 
# ----------------------------------------------------
class ColorToMaterialMain(plugins.CommandData):
    dialog = None
    def Execute(self, doc):
        # create the dialog
        if self.dialog is None:
            self.dialog = ColorToMaterialDialog()
        return self.dialog.Open(c4d.DLG_TYPE_ASYNC, pluginid=ID_COLORTOMATERIAL)
    
    def RestoreLayout(self, secref):
        # manage nonmodal dialog
        if self.dialog is None:
            self.dialog = ColorToMaterialDialog()
        return self.dialog.Restore(pluginid=ID_COLORTOMATERIAL, secret=secref)
    


if __name__ == "__main__":
    thispath = os.path.dirname(os.path.abspath(__file__))
    icon = bitmaps.BaseBitmap()
    icon.InitWith(os.path.join(thispath, "res/", "icon.tif"))
    plugins.RegisterCommandPlugin(
        ID_COLORTOMATERIAL, 
        IDS_PLUGIN_NAME, 
        0, 
        icon, 
        IDS_HELP_STRING, 
        ColorToMaterialMain()
    )

    print "%s v%.1f loaded. (C) %s Andre Berg" % (IDS_PLUGIN_NAME, IDS_PLUGIN_VERSION, CR_YEAR)
    

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
