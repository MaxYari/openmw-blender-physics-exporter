

bl_info = {
    "name": "Bullet JSON Exporter",
    "author": "xionglong.xu and Thrax",
    "version": (1, 0),
    "blender": (3, 3, 1),
    "location": "File > Export > Bullet JSON (.json)",
    "description": "Exports scenes to Bullet JSON format",
    "category": "Import-Export",
}


import os
import json
import mathutils
import bpy
from bpy_extras.io_utils import ExportHelper
import pprint

def getOffsetFromAToB(a, b):
    ta, ra, sa = a.matrix_world.decompose()
    tb, rb, sb = b.matrix_world.decompose()
    MtaInv = mathutils.Matrix.Translation(-ta)
    MraInv = ra.to_matrix().inverted().to_4x4()
    Mtb = mathutils.Matrix.Translation(tb)
    Mrb = rb.to_matrix().to_4x4()
    Moffset = MraInv @ MtaInv @ Mtb @ Mrb
    tOffset, rOffset, sOffset = Moffset.decompose()
    #tOffset.x = tOffset.x / sa.x
    #tOffset.y = tOffset.y / sa.y
    #tOffset.z = tOffset.z / sa.z
    return tOffset, rOffset

def save(context, path):
    jsonObject = {}

    scene = context.scene
    jsonObject["gravity"] = scene.gravity[:]
    jsonObject["rigid_bodys"] = []
    jsonObject["constraints"] = []
    jsonObject["bone_constraints"] = []
    def show_error(message):
        def draw_func(self, context):
            self.layout.label(text=message)
            
        bpy.context.window_manager.popup_menu(draw_func, title="An error occurred", icon='ERROR')

    print("----------BULLET EXPORT V2 Parsing scene----------")
    for obj in scene.objects:
        if obj.type == 'ARMATURE':
            print(f"Checking armature: {obj.name}")
            
            # Loop through its pose bones
            for pose_bone in obj.pose.bones:
                
                # Check each constraint for the pose bone
                for constraint in pose_bone.constraints:
                    
                    # If the constraint is a 'CHILD_OF' type, log its details
                    if constraint.type == 'CHILD_OF':
                        print(f"  Bone: {pose_bone.name}")
                        print(f"    Constraint: {constraint.name}")
                        print(f"      Type: {constraint.type}")
                        print(f"      Target: {constraint.target}")
                        print(f"      Subtarget: {constraint.subtarget}")
                        print(f"      Inverse Matrix: {constraint.inverse_matrix}")
                        print(f"      Influence: {constraint.influence}")
                        boneConstraint = {}
                        boneConstraint["bone"] = pose_bone.name
                        if constraint.target != None:
                            boneConstraint["parent"] = constraint.target.name
                        else:
                            print(f">-------------------------------- ERROR: {pose_bone.name}")
                            show_error(f"Bone parent undefined! {pose_bone.name}")
                        boneConstraint["inverse_matrix"] = [element for row in constraint.inverse_matrix for element in row]
                        boneConstraint["influence"] = constraint.influence
                        jsonObject["bone_constraints"].append(boneConstraint)

        if obj.rigid_body is not None:
            transform = obj.matrix_world
            location, quaternion, scale = transform.decompose()
            rigidBodyObject = {}
            rigidBodyObject["name"] = obj.name
            rigidBodyObject["location"] = location[0:3]
            rigidBodyObject["quaternion"] = quaternion[0:4]
            rigidBodyObject["static"] = obj.rigid_body.type == 'PASSIVE'
            rigidBodyObject["enabled"] = obj.rigid_body.enabled
            rigidBodyObject["kinematic"] = obj.rigid_body.kinematic
            rigidBodyObject["mass"] = 0 if obj.rigid_body.type == 'PASSIVE' else obj.rigid_body.mass
            rigidBodyObject["friction"] = obj.rigid_body.friction
            rigidBodyObject["restitution"] = obj.rigid_body.restitution
            rigidBodyObject["collision_shape"] = obj.rigid_body.collision_shape
            rigidBodyObject["collision_collections"] = [int(x) for x in obj.rigid_body.collision_collections]
            
            rigidBodyObject["use_margin"] = obj.rigid_body.use_margin
            rigidBodyObject["collision_margin"] = obj.rigid_body.collision_margin
            rigidBodyObject["angular_damping"] = obj.rigid_body.angular_damping
            rigidBodyObject["linear_damping"] = obj.rigid_body.collision_margin
            rigidBodyObject["deactivate_angular_velocity"] = obj.rigid_body.deactivate_angular_velocity
            rigidBodyObject["deactivate_linear_velocity"] = obj.rigid_body.deactivate_linear_velocity
            rigidBodyObject["use_deactivation"] = obj.rigid_body.use_deactivation
            rigidBodyObject["use_start_deactivated"] = obj.rigid_body.use_start_deactivated
            print("----------",obj.name)
            print(dir(obj.rigid_body))
            group = 0
            for i in range(0, len(obj.rigid_body.collision_collections)):
                if obj.rigid_body.collision_collections[i]:
                    group = group | (1 << i)
            rigidBodyObject["group"] = group
            rigidBodyObject["mask"] = group
            jsonObject["rigid_bodys"].append(rigidBodyObject)


        if obj.rigid_body_constraint is not None:
            rigidBodyConstraintObject = {}
            constraintType = obj.rigid_body_constraint.type
            rigidBodyConstraintObject["type"] = constraintType
            rigidBodyConstraintObject["enabled"] = obj.rigid_body_constraint.enabled
            rigidBodyConstraintObject["disable_collisions"] = obj.rigid_body_constraint.disable_collisions
            rigidBodyConstraintObject["breaking_threshold"] = obj.rigid_body_constraint.breaking_threshold
            rigidBodyConstraintObject["use_breaking"] = obj.rigid_body_constraint.use_breaking #todo: replace by breaking thredhold value?
            rigidBodyConstraintObject["use_override_solver_iterations"] = obj.rigid_body_constraint.use_override_solver_iterations
            rigidBodyConstraintObject["solver_iterations"] = obj.rigid_body_constraint.solver_iterations

            object1 = obj.rigid_body_constraint.object1
            if object1 is not None:
                rigidBodyConstraintObject["object1"] = object1.name
                tOffset, rOffset = getOffsetFromAToB(object1, obj)
                rigidBodyConstraintObject["translation_offset_a"] = tOffset[0:3]
                rigidBodyConstraintObject["rotation_offset_a"] = rOffset[0:4]

            object2 = obj.rigid_body_constraint.object2
            if object2 is not None:
                rigidBodyConstraintObject["object2"] = object2.name
                tOffset, rOffset = getOffsetFromAToB(object2, obj)
                rigidBodyConstraintObject["translation_offset_b"] = tOffset[0:3]
                rigidBodyConstraintObject["rotation_offset_b"] = rOffset[0:4]
            
            
            print(obj.rigid_body_constraint)
            
            pprint.pprint(obj.rigid_body_constraint , width= 30)
            for attr in dir(obj.rigid_body_constraint):
                print(f"{attr}: {getattr(obj.rigid_body_constraint, attr)}")
            
            if constraintType == 'HINGE' or constraintType == 'MOTOR':
                rigidBodyConstraintObject["use_limit_ang_z"] = obj.rigid_body_constraint.use_limit_ang_z
                rigidBodyConstraintObject["limit_ang_z_lower"] = obj.rigid_body_constraint.limit_ang_z_lower
                rigidBodyConstraintObject["limit_ang_z_upper"] = obj.rigid_body_constraint.limit_ang_z_upper
                if constraintType == 'MOTOR':
                    rigidBodyConstraintObject["motor_ang_max_impulse"] = obj.rigid_body_constraint.motor_ang_max_impulse
                    rigidBodyConstraintObject["motor_lin_max_impulse"] = obj.rigid_body_constraint.motor_lin_max_impulse
                    rigidBodyConstraintObject["motor_ang_target_velocity"] = obj.rigid_body_constraint.motor_ang_target_velocity
                    rigidBodyConstraintObject["motor_lin_target_velocity"] = obj.rigid_body_constraint.motor_lin_target_velocity
                    rigidBodyConstraintObject["use_motor_ang"] = obj.rigid_body_constraint.use_motor_ang
                    rigidBodyConstraintObject["use_motor_lin"] = obj.rigid_body_constraint.use_motor_lin
            elif constraintType == 'SLIDER':
                rigidBodyConstraintObject["use_limit_lin_x"] = obj.rigid_body_constraint.use_limit_lin_x
                rigidBodyConstraintObject["limit_lin_x_lower"] = obj.rigid_body_constraint.limit_lin_x_lower
                rigidBodyConstraintObject["limit_lin_x_upper"] = obj.rigid_body_constraint.limit_lin_x_upper
            elif constraintType == 'PISTON':
                rigidBodyConstraintObject["use_limit_lin_x"] = obj.rigid_body_constraint.use_limit_lin_x
                rigidBodyConstraintObject["limit_lin_x_lower"] = obj.rigid_body_constraint.limit_lin_x_lower
                rigidBodyConstraintObject["limit_lin_x_upper"] = obj.rigid_body_constraint.limit_lin_x_upper
                rigidBodyConstraintObject["use_limit_ang_x"] = obj.rigid_body_constraint.use_limit_ang_x
                rigidBodyConstraintObject["limit_ang_x_lower"] = obj.rigid_body_constraint.limit_ang_x_lower
                rigidBodyConstraintObject["limit_ang_x_upper"] = obj.rigid_body_constraint.limit_ang_x_upper
            elif constraintType == 'GENERIC' or constraintType == 'GENERIC_SPRING':
                rigidBodyConstraintObject["use_limit_lin_x"] = obj.rigid_body_constraint.use_limit_lin_x
                rigidBodyConstraintObject["limit_lin_x_lower"] = obj.rigid_body_constraint.limit_lin_x_lower
                rigidBodyConstraintObject["limit_lin_x_upper"] = obj.rigid_body_constraint.limit_lin_x_upper
                rigidBodyConstraintObject["use_limit_lin_y"] = obj.rigid_body_constraint.use_limit_lin_y
                rigidBodyConstraintObject["limit_lin_y_lower"] = obj.rigid_body_constraint.limit_lin_y_lower
                rigidBodyConstraintObject["limit_lin_y_upper"] = obj.rigid_body_constraint.limit_lin_y_upper
                rigidBodyConstraintObject["use_limit_lin_z"] = obj.rigid_body_constraint.use_limit_lin_z
                rigidBodyConstraintObject["limit_lin_z_lower"] = obj.rigid_body_constraint.limit_lin_z_lower
                rigidBodyConstraintObject["limit_lin_z_upper"] = obj.rigid_body_constraint.limit_lin_z_upper
                rigidBodyConstraintObject["use_limit_ang_x"] = obj.rigid_body_constraint.use_limit_ang_x
                rigidBodyConstraintObject["limit_ang_x_lower"] = obj.rigid_body_constraint.limit_ang_x_lower
                rigidBodyConstraintObject["limit_ang_x_upper"] = obj.rigid_body_constraint.limit_ang_x_upper
                rigidBodyConstraintObject["use_limit_ang_y"] = obj.rigid_body_constraint.use_limit_ang_y
                rigidBodyConstraintObject["limit_ang_y_lower"] = obj.rigid_body_constraint.limit_ang_y_lower
                rigidBodyConstraintObject["limit_ang_y_upper"] = obj.rigid_body_constraint.limit_ang_y_upper
                rigidBodyConstraintObject["use_limit_ang_z"] = obj.rigid_body_constraint.use_limit_ang_z
                rigidBodyConstraintObject["limit_ang_z_lower"] = obj.rigid_body_constraint.limit_ang_z_lower
                rigidBodyConstraintObject["limit_ang_z_upper"] = obj.rigid_body_constraint.limit_ang_z_upper
                if constraintType == 'GENERIC_SPRING':
                    rigidBodyConstraintObject["use_spring_x"] = obj.rigid_body_constraint.use_spring_x
                    rigidBodyConstraintObject["spring_stiffness_x"] = obj.rigid_body_constraint.spring_stiffness_x
                    rigidBodyConstraintObject["spring_damping_x"] = obj.rigid_body_constraint.spring_damping_x
                    rigidBodyConstraintObject["use_spring_y"] = obj.rigid_body_constraint.use_spring_y
                    rigidBodyConstraintObject["spring_stiffness_y"] = obj.rigid_body_constraint.spring_stiffness_y
                    rigidBodyConstraintObject["spring_damping_y"] = obj.rigid_body_constraint.spring_damping_y
                    rigidBodyConstraintObject["use_spring_z"] = obj.rigid_body_constraint.use_spring_z
                    rigidBodyConstraintObject["spring_stiffness_z"] = obj.rigid_body_constraint.spring_stiffness_z
                    rigidBodyConstraintObject["spring_damping_z"] = obj.rigid_body_constraint.spring_damping_z
                    rigidBodyConstraintObject["use_spring_ang_x"] = obj.rigid_body_constraint.use_spring_ang_x
                    rigidBodyConstraintObject["spring_stiffness_ang_x"] = obj.rigid_body_constraint.spring_stiffness_ang_x
                    rigidBodyConstraintObject["spring_damping_ang_x"] = obj.rigid_body_constraint.spring_damping_ang_x
                    rigidBodyConstraintObject["use_spring_ang_y"] = obj.rigid_body_constraint.use_spring_ang_y
                    rigidBodyConstraintObject["spring_stiffness_ang_y"] = obj.rigid_body_constraint.spring_stiffness_ang_y
                    rigidBodyConstraintObject["spring_damping_ang_y"] = obj.rigid_body_constraint.spring_damping_ang_y
                    rigidBodyConstraintObject["use_spring_ang_z"] = obj.rigid_body_constraint.use_spring_ang_z
                    rigidBodyConstraintObject["spring_stiffness_ang_z"] = obj.rigid_body_constraint.spring_stiffness_ang_z
                    rigidBodyConstraintObject["spring_damping_ang_z"] = obj.rigid_body_constraint.spring_damping_ang_z
                    
            jsonObject["constraints"].append(rigidBodyConstraintObject)

    jsonText = json.dumps(jsonObject)
    bpy.context.scene['physics_scene'] = jsonText
    f = open(path, 'w')
    f.write(jsonText)
    f.close()



class ExportBulletJSON(bpy.types.Operator, ExportHelper):
    bl_idname = "export_bullet.json"
    bl_label = "Export Bullet JSON"
    
    filename_ext = ".json"

    def execute(self, context):
        save(context, self.filepath)  # Call your existing save function
        return {'FINISHED'}

def menu_func_export(self, context):
    self.layout.operator(ExportBulletJSON.bl_idname, text="Bullet JSON (.json)")

def register():
    bpy.utils.register_class(ExportBulletJSON)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(ExportBulletJSON)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()