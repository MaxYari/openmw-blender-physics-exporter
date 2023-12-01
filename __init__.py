bl_info = {
	"name": "Bullet json format",
	"author": "xionglong.xu",
	"version": (0, 0, 1),
	"blender": (2, 80, 0),
	"location": "File > Import-Export",
	"category": "Import-Export"
}

if "bpy" in locals():
    import importlib
    if "import_bullet" in locals():
        importlib.reload(import_bullet)
    if "export_bullet" in locals():
        importlib.reload(export_bullet)

import bpy
from bpy.props import (
		StringProperty,
		)
from bpy_extras.io_utils import (
		ImportHelper,
		ExportHelper,
		path_reference_mode,
		)



class ExportBullet(bpy.types.Operator, ExportHelper):
	bl_idname = "openmw_physics.json"
	bl_label = "Export OpenMW Physics"
	bl_options = {'PRESET', 'UNDO'}

	filename_ext = ".json"
	filter_glob = StringProperty(
		default="*.json",
		options={'HIDDEN'}
		)

	def execute(self, context):
		from . import export_bullet
		export_bullet.save(context, self.properties.filepath)
		return {'FINISHED'}		

def menu_func_export(self, context):
    self.layout.operator(ExportBullet.bl_idname, text="OpenMW Physics (.json)")

def register():	
	bpy.utils.register_class(ExportBullet)	
	bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():	
	bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)	
	bpy.utils.unregister_class(ExportBullet)
	
if __name__ == "__main__":
    register() 