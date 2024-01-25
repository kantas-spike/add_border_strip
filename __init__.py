if "bpy" in locals():
    import imp

    imp.reload(ops)
    imp.reload(border_strip_utils)
else:
    from . import ops
    from . import border_strip_utils

import bpy

bl_info = {
    "name": "add border",
    "description": "VSE内に枠線用のイメージストリップを追加する",
    "author": "kanta",
    "version": (0, 0),
    "blender": (4, 0, 1),
    "location": "VSE > Sidebar",
    "category": "Sequencer",
}


def layout_props(layout: bpy.types.UILayout, prop_obj, prop_name, label, factor=0.3):
    sep = layout.split(factor=factor)
    sep.alignment = "RIGHT"
    sep.label(text=label)
    sep.prop(prop_obj, property=prop_name, text="")


class AddBorderBase:
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Add Border"

    @classmethod
    def poll(cls, context):
        return context.space_data.view_type == "SEQUENCER"


class AddBorderOutputPanel(AddBorderBase, bpy.types.Panel):
    bl_label = "Output"
    bl_idname = "ADDBORDER_PT_OutputPanel"

    def draw(self, context):
        props = context.scene.border_props

        layout = self.layout
        layout.label(text="Border Image Directory")
        layout.prop(props, "image_dir", text="")


class AddBorderPlaceholderPanel(AddBorderBase, bpy.types.Panel):
    bl_label = "Placeholder"
    bl_idname = "ADDBORDER_PT_PlaceholderPanel"

    def draw(self, context):
        pass


class AddBorderPlaceholderSettingsPanel(AddBorderBase, bpy.types.Panel):
    bl_label = "Settings"
    bl_idname = "ADDBORDER_PT_PlaceholderSettingsPanel"
    bl_parent_id = "ADDBORDER_PT_PlaceholderPanel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        props = context.scene.border_props

        layout = self.layout
        layout.label(text="Color & Size")
        layout_props(layout, props, "placeholder_color", "Color")
        layout.separator()
        layout_props(layout, props, "placeholder_scale_x", "Scale X")
        layout_props(layout, props, "placeholder_scale_y", "Scale Y")
        layout.separator()
        layout.label(text="Strip")
        layout_props(layout, props, "placeholder_duration", "Duration")
        layout_props(layout, props, "placeholder_channel", "Channel")


class AddBorderPlaceholderButtonsPanel(AddBorderBase, bpy.types.Panel):
    bl_label = "Placeholder"
    bl_idname = "ADDBORDER_PT_PlaceholderButtonsPanel"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = "ADDBORDER_PT_PlaceholderPanel"

    def draw(self, context):
        pass
        layout = self.layout
        layout.operator(
            ops.AddPlaceholderStripOpertaion.bl_idname,
            text="Add Strip for Placeholder",
        )


class AddBorderBorderPanel(AddBorderBase, bpy.types.Panel):
    bl_label = "Border"
    bl_idname = "ADDBORDER_PT_BorderPanel"

    def draw(self, context):
        props = context.scene.border_props

        layout = self.layout
        layout_props(layout, props, "border_color", "Color")
        layout.separator()
        layout_props(layout, props, "border_size", "Size(px)")

        layout.separator()
        row = layout.row(align=True)
        row.operator(
            ops.AddBorderMainOperation.bl_idname,
            text="Replace Placehlder to Border Image",
        )
        strip = context.scene.sequence_editor.active_strip
        if (
            strip is not None
            and strip.get("generated_by") == "add_border_strip"
            and strip.get("strip_type") == "placeholder"
        ):
            row.enabled = True
        else:
            row.enabled = False


class AddBorderProperties(bpy.types.PropertyGroup):
    image_dir: bpy.props.StringProperty(subtype="DIR_PATH", default="//border_imgs")
    border_color: bpy.props.FloatVectorProperty(
        subtype="COLOR_GAMMA", min=0, max=1.0, size=4, default=(1.0, 0, 0, 1)
    )
    border_size: bpy.props.IntProperty(default=10, min=0, max=100)
    placeholder_color: bpy.props.FloatVectorProperty(
        subtype="COLOR_GAMMA", min=0, max=1.0, size=4, default=(0.0, 0.5, 0.1, 0.3)
    )
    placeholder_scale_x: bpy.props.FloatProperty(min=0, max=1.0, default=0.5)
    placeholder_scale_y: bpy.props.FloatProperty(min=0, max=1.0, default=0.5)
    placeholder_duration: bpy.props.IntProperty(min=0, default=60)
    placeholder_channel: bpy.props.IntProperty(min=1, default=2)


classList = ops.class_list + [
    AddBorderPlaceholderPanel,
    AddBorderPlaceholderSettingsPanel,
    AddBorderPlaceholderButtonsPanel,
    AddBorderOutputPanel,
    AddBorderBorderPanel,
    AddBorderProperties,
]


def setup_props():
    bpy.types.Scene.border_props = bpy.props.PointerProperty(type=AddBorderProperties)


def clear_props():
    del bpy.types.Scene.border_props


def register():
    for c in classList:
        bpy.utils.register_class(c)
    setup_props()
    print("add_border_strip: registered")


def unregister():
    clear_props()
    for c in classList:
        bpy.utils.unregister_class(c)
    print("add_border_strip: unregistered")


if __name__ == "__main__":
    register()
