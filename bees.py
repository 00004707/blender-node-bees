import bpy
import random

# License: GPL 
# https://www.gnu.org/licenses/gpl-3.0.en.html
# This addon comes with absolutely NO WARRANTY


bl_info = {
    "name": "Node Bees",
    "author": "00004707",
    "version": (1, 1),
    "blender": (3, 5, 0),
    "location": "Node Editor Menu Bar",
    "description": "Add bees to your Node Groups",
    "warning": "Annoying",
    "doc_url": "",
    "category": "Interface",
}


class RemoveBeesOperator(bpy.types.Operator):
    """
    Operator that simply removes the bees (reroutes with drivers) from the node tree
    """
    
    bl_idname = "bees.remove"
    bl_label = "Remove Bees"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        self.remove_bees(context)
        return {'FINISHED'}
    
    @classmethod
    def poll(self, context):
        return context.space_data.type == "NODE_EDITOR" and context.space_data.node_tree
    
    def remove_bees(self, context):
        nodes = context.space_data.node_tree.nodes
        
        # Get selected nodes or all if none selected
        selected = context.selected_nodes
        if len(selected) == 0:
            selected = nodes

        # Remove bees
        rem_count = 0
        for node in selected:
            if "annoying0bee" in node.name:
                nodes.remove(node)
                rem_count += 1
        self.report({'INFO'}, f"Removed {rem_count} bees")
        return {"FINISHED"}

class GenerateBeesOperator(bpy.types.Operator):
    """
    Operator that creates reroutes with drivers to create the "bees"
    """
    bl_idname = "bees.generate"
    bl_label = "Add Bees"
    bl_options = {'REGISTER', 'UNDO'}

    density: bpy.props.FloatProperty(name="Spacing", default=50.0, min=10.0, max=1000.0)
    amplitude: bpy.props.FloatProperty(name="Amplitude", default=500.0, min = 0.0, max = 1000)
    speed: bpy.props.FloatProperty(name="Speed", default=10.0, min = 1.0, max = 100)
    label: bpy.props.StringProperty(name="Text", default="\_(bee)_/")
    count_limit: bpy.props.IntProperty(name="Max Spawned Bees", default=2000, min=1)
    nodetype: bpy.props.EnumProperty(
        name="Bee Color",
        description="Select an option",
        items=[
            ('COLLECTION', "White", "Create white bees"),
            ('VALUE', "Gray", "Create gray bees"),
            ('OBJECT', "Orange", "Create orange bees"),
            ('RGBA', "Yellow", "Create yellow bees"),
            ('SHADER', "Green", "Create green bees"),
            ('INT', "Dark Green", "Create dark green bees"),
            ('GEOMETRY', "Teal", "Create teal bees"),
            ('STRING', "Sky Blue", "Create sky blue bees"),
            ('VECTOR', "Lavender", "Create lavender colored bees"),
            ('TEXTURE', "Purple", "Create purple bees"),
            ('IMAGE', "Dark Purple", "Create dark purple bees"),
            ('BOOLEAN', "Pink", "Create pink bees"),
            ('RANDOM', "Random", "Create random colored bees")
        ],
        default="RGBA"
    )
    
    # For randomize color
    reroute_color_vals = ['VALUE','INT','BOOLEAN','VECTOR','STRING','RGBA','SHADER','OBJECT','IMAGE','GEOMETRY','COLLECTION','TEXTURE','MATERIAL']
    min_x = 0
    min_y = 0
    
    def execute(self, context):
        return self.create_bees(context)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    @classmethod
    def poll(self, context):
        return context.space_data.type == "NODE_EDITOR" and context.space_data.node_tree
    
    
    def create_node(self, context, x,y):
        """
        Create node at X Y matrix index
        """
        
        nodes = context.space_data.node_tree.nodes     
        speed = 100/self.speed
        
        r = nodes.new("NodeReroute")
        r.inputs['Input'].type = self.nodetype if self.nodetype != "RANDOM" else random.choice(self.reroute_color_vals)
        r.location = ((self.min_x + (x * self.density), self.min_y + (y * self.density)))
        r.label = self.label
        r.name = "annoying0bee"
        

        # add a driver to make them fly
        drivers = []
        drivers.append(r.driver_add("location", 0).driver)
        drivers.append(r.driver_add("location", 1).driver)
        
        for i, driver in enumerate(drivers):
            driver.type = 'SCRIPTED'
            driver.expression = f"{float(r.location[i])} + sin(frame/{speed}+{random.uniform(-10, 10)}) * ({self.amplitude + random.uniform(0, self.amplitude/10)})"
        
        
    def create_bees(self, context):
        """
        Calculate deltas and create x amount of bees in area
        """
        # enable playback in node editors
        for screen in bpy.data.screens:
            screen.use_play_node_editors = True

        nodes = context.space_data.node_tree.nodes

        self.min_x = 9999999.0
        self.min_y = 9999999.0
        self.max_x = -9999999.0
        self.max_y = -9999999.0
        
        # case: graph with nodes
        # find the min&max pos vector
        if len(nodes) > 0:
        
            selected = context.selected_nodes

            if len(selected) == 0:
                selected = nodes
            print(f"Selected nodes count: {len(selected)}")

            for node in selected:
                self.min_x = (node.location[0]) if (node.location[0]) < self.min_x else self.min_x
                self.min_y = (node.location[1]-node.height) if(node.location[1]-node.height) < self.min_y else self.min_y
                self.max_x = (node.location[0]+node.width) if (node.location[0]+node.width) > self.max_x else self.max_x
                self.max_y = (node.location[1]) if (node.location[1]) > self.max_y else self.max_y
          
        # case: graph without nodes
        else:
            self.min_x = -400
            self.min_y = -400
            self.max_x = 400
            self.max_y = 400

        # get density
        delta_x = self.max_x - self.min_x
        delta_y = self.max_y - self.min_y
        density_x = int(delta_x / (self.density))
        density_y = int(delta_y / (self.density))
        bee_count = density_x * density_y 

        # create bees with hard limit to avoid too long unresponsive time
        print(f"About to create {density_x*density_y} bees with a hard limit of {self.count_limit}")
        limiter = False
        for x in range(0, density_x):
            for y in range(0, density_y):
                if (x*density_y+y+1) > self.count_limit: 
                    print(f"{(x*density_y+y+1)} > self.count_limit")
                    limiter = True
                    break
                self.create_node(context, x,y)
            
            if limiter:
                break

            print(f"Bee #{(x+1)*density_y} created")

        self.report({'INFO'}, f"Created {min(bee_count, self.count_limit)} bees")
        return {"FINISHED"}

def append_menu(self, context):
    """
    Add the opeartor buttons
    """
    self.layout.operator("bees.generate")
    self.layout.operator("bees.remove")


classes = [GenerateBeesOperator, RemoveBeesOperator]

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.NODE_MT_editor_menus.append(append_menu)
    
def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    bpy.types.NODE_MT_editor_menus.remove(append_menu)
    
        
if __name__ == "__main__":
    register()
