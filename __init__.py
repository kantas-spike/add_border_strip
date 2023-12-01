import bpy
from bpy.types import Context

bl_info = {
    "name": "add border strip",
    "description": "VSE内で選択されたストリップをボーダーで囲むためのイメージストリップを作成・追加する",
    "author": "kanta",
    "version": (0, 0),
    "blender": (4, 0, 1),
    "location": "VSE > Sidebar",
    "category": "Sequencer",
}


class AddBorderPanel(bpy.types.Panel):
    bl_label = "Add border strip"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Add Border Strip"
    bl_idname = "ADDBORDER_PT_MainPanel"

    @classmethod
    def poll(cls, context):
        return context.space_data.view_type == "SEQUENCER"

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon="PLUGIN")

    def draw(self, context: Context):
        props = bpy.context.scene.border_props
        layout = self.layout
        layout.label(text="画像出力先ディレクトリ")
        layout.prop(props, "image_dir", text="")
        layout.separator()
        layout.label(text="ボーダー色")
        layout.prop(props, "border_color", text="")
        layout.separator()
        layout.label(text="ボーダー色のアルファ値")
        layout.prop(props, "border_alpha", text="")
        layout.separator()
        layout.label(text="ボーダーのサイズ(px)")
        layout.prop(props, "border_size", text="")


class AddBorderProperties(bpy.types.PropertyGroup):
    image_dir: bpy.props.StringProperty(subtype="DIR_PATH", default="//border_imgs")
    border_color: bpy.props.FloatVectorProperty(subtype="COLOR", default=(1.0, 0, 0))
    border_alpha: bpy.props.FloatProperty(default=1.0, min=0, max=1.0)
    border_size: bpy.props.IntProperty(default=10, min=0, max=100)


classList = [AddBorderPanel, AddBorderProperties]


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
