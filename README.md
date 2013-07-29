Color To Material
=================

Color To Material is a Python plugin that allows  
for making the Display > Layer Color viewport,  
as well as the Basic > Use Color object settings  
renderable by assigning materials with the target  
material channel set to the object or layer color.


Requirements
------------

CINEMA 4D R12 or later


Modus Operandi
--------------

First, loop through all the objects that are selected in  
the object manager and get the layer the object belongs to. 

Then, create a new material and set the material's color  
channel to the same RGB color as the color of the layer.  

Create a new texture tag on the object and assign the  
corresponding material.  

Do not create a new material if a material with name `RGB x,y,z`  
already exists. Use existing material instead.

Tip: If you want all the new materials that will be created  
added to an existing material layer, in the Material Manager  
switch to that layer before running the script.   

Any materials created will be assigned to this layer automatically.  


License
-------

    Created by André Berg on 2011-03-22.
    Copyright Berg Media 2013. All rights reserved.
    
    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at
    
      http://www.apache.org/licenses/LICENSE-2.0
    
    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

