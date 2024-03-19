if "bpy" in locals():
    import imp

    imp.reload(ops)
    imp.reload(border_strip_utils)
else:
    from . import ops
    from . import border_strip_utils

import bpy

bl_info = {
    "name": "Add Border",
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
    bl_options = {"DEFAULT_CLOSED"}

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
        layout = self.layout
        layout.operator(
            ops.AddPlaceholderStripOpertaion.bl_idname,
            text="Add Placeholder",
        )


class AddBorderBorderPanel(AddBorderBase, bpy.types.Panel):
    bl_label = "Border"
    bl_idname = "ADDBORDER_PT_BorderPanel"

    def draw(self, context):
        props = context.scene.border_props

        layout = self.layout
        layout_props(layout, props, "shape_type", "Shape")
        layout_props(layout, props, "border_color", "Color")
        layout_props(layout, props, "border_size", "Size(px)")

        layout.separator()
        row = layout.row(align=True)
        row.operator(
            ops.AddBorderReplaceCurrentPlaceholderOperation.bl_idname,
            text="Placehlder → Border",
        )
        strip = context.scene.sequence_editor.active_strip
        if strip is not None and ops.is_placeholder(strip):
            row.enabled = True
        else:
            row.enabled = False

        row = layout.row(align=True)
        row.operator(
            ops.AddBorderReplaceAllPlaceholdersOperation.bl_idname,
            text="All Placehlders → Borders",
        )


class AddBorderEffectPanel(AddBorderBase, bpy.types.Panel):
    bl_label = "Effect"
    bl_idname = "ADDBORDER_PT_EffectPanel"

    def draw(self, context):
        pass


class AddBorderEffectSettingsPanel(AddBorderBase, bpy.types.Panel):
    bl_label = "Settings"
    bl_idname = "ADDBORDER_PT_EffectSettingsPanel"
    bl_parent_id = "ADDBORDER_PT_EffectPanel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        props = context.scene.border_props.effect_settings

        layout = self.layout
        layout_props(layout, props, "sec_of_one_cycle", "1周期の秒数")
        layout_props(layout, props, "max_scale", "最大拡大率")
        layout_props(layout, props, "min_scale", "最小拡大率")
        layout_props(layout, props, "effect_times", "繰り返し回数")
        row = layout.row()
        row.label(text="キーフレームの時間配分")
        layout_props(layout, props, "keyframes_ratio", "")


class AddBorderEffectButtonsPanel(AddBorderBase, bpy.types.Panel):
    bl_label = "Buttons"
    bl_idname = "ADDBORDER_PT_EffectButtonsPanel"
    bl_parent_id = "ADDBORDER_PT_EffectPanel"
    bl_options = {"HIDE_HEADER"}

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        op = row.operator(
            ops.AddBorderApplyEffectOperation.bl_idname,
            text="Apply Effect",
        )
        props = context.scene.border_props.effect_settings
        op.sec_of_one_cycle = props.sec_of_one_cycle
        op.max_scale = props.max_scale
        op.min_scale = props.min_scale
        op.effect_times = props.effect_times
        op.keyframes_ratio = props.keyframes_ratio

        row = layout.row()
        row.operator(
            ops.AddBorderClearEffectOperation.bl_idname,
            text="Clear Effect",
        )


class AddBorderEffectProperties(bpy.types.PropertyGroup):
    sec_of_one_cycle: bpy.props.FloatProperty(min=0.5, max=10, default=0.5)
    max_scale: bpy.props.FloatProperty(min=1.0, max=2.0, default=1.05)
    min_scale: bpy.props.FloatProperty(min=0.1, max=1.0, default=0.9)
    effect_times: bpy.props.IntProperty(min=1, max=5, default=2)
    keyframes_ratio: bpy.props.FloatVectorProperty(
        min=0, max=1.0, size=4, default=(0.0, 0.3, 0.7, 1.0)
    )


class AddBorderProperties(bpy.types.PropertyGroup):
    image_dir: bpy.props.StringProperty(subtype="DIR_PATH", default="//border_imgs")
    shape_type: bpy.props.EnumProperty(
        name="Shape",
        description="シェイプの種類",
        items=[
            ("rectangle", "Rectangle", "四角形"),
            ("circle", "Circle", "円形"),
        ],
        default="rectangle",
    )
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
    effect_settings: bpy.props.PointerProperty(type=AddBorderEffectProperties)


classList = ops.class_list + [
    AddBorderPlaceholderPanel,
    AddBorderPlaceholderSettingsPanel,
    AddBorderPlaceholderButtonsPanel,
    AddBorderOutputPanel,
    AddBorderBorderPanel,
    AddBorderEffectPanel,
    AddBorderEffectSettingsPanel,
    AddBorderEffectButtonsPanel,
    AddBorderEffectProperties,
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
    for c in reversed(classList):
        bpy.utils.unregister_class(c)
    print("add_border_strip: unregistered")


if __name__ == "__main__":
    register()
