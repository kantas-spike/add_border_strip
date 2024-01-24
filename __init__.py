if "bpy" in locals():
    import imp

    imp.reload(ops)
else:
    from . import ops

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
        layout.label(text="画像出力先ディレクトリ")
        layout.prop(props, "image_dir", text="")


class AddBorderMarkerPanel(AddBorderBase, bpy.types.Panel):
    bl_label = "Marker"
    bl_idname = "ADDBORDER_PT_MarkerPanel"

    def draw(self, context):
        layout = self.layout
        layout.operator(ops.AddMarkerStripOpertaion.bl_idname, text="位置決め用Stripを挿入")


class AddBorderBorderPanel(AddBorderBase, bpy.types.Panel):
    bl_label = "Border"
    bl_idname = "ADDBORDER_PT_BorderPanel"

    def draw(self, context):
        props = context.scene.border_props

        layout = self.layout
        layout.label(text="ボーダー色")
        layout.prop(props, "border_color", text="")
        layout.separator()
        layout.label(text="ボーダーのサイズ(px)")
        layout.prop(props, "border_size", text="")
        layout.separator()
        row = layout.row(align=True)
        label = "ボーダーストリップを追加"
        row.operator(ops.AddBorderMainOperation.bl_idname, text=label)
        strip = context.scene.sequence_editor.active_strip
        if (
            strip is not None
            and strip.get("generated_by") == "add_border_strip"
            and strip.get("strip_type") == "marker"
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


classList = ops.class_list + [
    AddBorderOutputPanel,
    AddBorderMarkerPanel,
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
