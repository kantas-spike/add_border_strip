import bpy
import datetime
import secrets
import os
import gpu
import numpy as np

from mathutils import Matrix
from gpu_extras.batch import batch_for_shader


class StripRect:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.width = w
        self.height = h

    def __str__(self) -> str:
        return f"<StripRect, ({self.x}, {self.y}), {self.width} x {self.height}>"

    def central_point(self):
        return [self.x + self.width / 2, self.y + self.height / 2]

    @classmethod
    def fromEffectSequenceStrip(cls, strip: bpy.types.Sequence):
        scrn_rect = cls.fromScreen()
        trans = strip.transform
        strip_size = []
        # print(strip, f"has elements?: {hasattr(strip, 'elements')}")
        if hasattr(strip, "elements"):
            element = strip.elements[0]
            strip_size[:] = [element.orig_width, element.orig_height]
        else:
            strip_size[:] = [
                scrn_rect.width * trans.scale_x,
                scrn_rect.height * trans.scale_y,
            ]
        # print(f"strip_size: {strip_size}")
        strip_w = strip_size[0]
        strip_h = strip_size[1]
        global_origin = [
            scrn_rect.width * trans.origin[0],
            scrn_rect.height * trans.origin[1],
        ]
        local_origin = [strip_w * trans.origin[0], strip_h * trans.origin[1]]
        strip_blp = [
            global_origin[0] - local_origin[0] + trans.offset_x,
            global_origin[1] - local_origin[1] + trans.offset_y,
        ]

        return cls(
            round(strip_blp[0]), round(strip_blp[1]), round(strip_w), round(strip_h)
        )

    @classmethod
    def fromScreen(cls):
        render = bpy.data.scenes["Scene"].render
        width = render.resolution_x * (render.resolution_percentage / 100)
        height = render.resolution_y * (render.resolution_percentage / 100)
        return cls(0, 0, round(width), round(height))


def normalize_image_dir(image_dir):
    clean_image_dir = bpy.path.abspath(image_dir)
    if os.path.isabs(clean_image_dir):
        return clean_image_dir
    elif len(bpy.data.filepath) > 0:
        base_dir = os.path.dirname(bpy.data.filepath)
        return os.path.normpath(os.path.join(base_dir, clean_image_dir))
    else:
        return None


def create_border_strip(
    src_strip: bpy.types.Sequence, image_dir, border_size, border_color
):
    # print(">>>create_border_strip")
    # print(src_strip)
    abs_image_dir = os.path.abspath(image_dir)
    # print(abs_image_dir)

    if not os.path.exists(abs_image_dir):
        os.makedirs(abs_image_dir)

    file_name = f"{src_strip.get('placeholder_id')}.png"
    output_path = os.path.join(abs_image_dir, file_name)
    # print(output_path)

    # target_stripの座標情報を取得
    src_rect = StripRect.fromEffectSequenceStrip(src_strip)

    # 座標情報から画像を生成
    # print(f"border_color: {border_color[:]}")
    image_padding = 10
    create_rect_border_image(
        output_path,
        border_size,
        [src_rect.width, src_rect.height],
        border_color,
        image_padding,
    )
    # _draw_rect(output_path, src_rect.width, src_rect.height, border_size, border_color)
    print(f"ボーダー画像を生成: {output_path}")
    # 生成画像と座標情報からimageストリップを追加
    rel_image_path = (
        bpy.path.relpath(output_path) if len(bpy.data.filepath) > 0 else output_path
    )
    # print(f"rel_image_path: {rel_image_path}")
    se = bpy.context.scene.sequence_editor
    img_strip = se.sequences.new_image(
        bpy.path.basename(rel_image_path),
        rel_image_path,
        src_strip.channel + 1,
        src_strip.frame_final_start,
    )
    img_strip.frame_final_end = src_strip.frame_final_end
    img_rect = StripRect.fromEffectSequenceStrip(img_strip)
    # print(src_rect, img_rect)
    img_strip.transform.offset_x = src_rect.x - img_rect.x - border_size - image_padding
    img_strip.transform.offset_y = src_rect.y - img_rect.y - border_size - image_padding
    img_strip.color_tag = "COLOR_01"
    return img_strip


def _make_unique_name(prefix="___"):
    return "{0}{1}_{2}".format(
        prefix, secrets.token_urlsafe(6), datetime.datetime.now().timestamp()
    )


def get_rect_vertices(rect_size, canvs_size):
    rect_w, rect_h = rect_size
    canvas_w, canvas_h = canvs_size
    w_rate = rect_w / canvas_w
    h_rate = rect_h / canvas_h
    return np.array(
        [
            [-1 * w_rate, -1 * h_rate],
            [-1 * w_rate, h_rate],
            [w_rate, -1 * h_rate],
            [w_rate, h_rate],
        ]
    )


def create_rect_border_image(
    output_path,
    line_width,
    inner_rect_size,
    line_color,
    padding=10,
):
    inner_w = inner_rect_size[0]
    inner_h = inner_rect_size[1]
    outer_w = inner_w + (line_width * 2)
    outer_h = inner_h + (line_width * 2)
    canvas_w = outer_w + (padding * 2)
    canvas_h = outer_h + (padding * 2)
    outer_vtxs = get_rect_vertices([outer_w, outer_h], [canvas_w, canvas_h])
    inner_vtxs = get_rect_vertices([inner_w, inner_h], [canvas_w, canvas_h])

    image_name = _make_unique_name()

    offscreen = gpu.types.GPUOffScreen(canvas_w, canvas_h)

    with offscreen.bind():
        fb = gpu.state.active_framebuffer_get()
        fb.clear(color=(0.0, 0.0, 0.0, 0.0))
        with gpu.matrix.push_pop():
            # reset matrices -> use normalized device coordinates [-1, 1]
            gpu.matrix.load_matrix(Matrix.Identity(4))
            gpu.matrix.load_projection_matrix(Matrix.OrthoProjection("XY", 4))
            # gpu.matrix.translate((0, 0))
            # gpu.matrix.scale_uniform(1.0)

            shader = gpu.shader.from_builtin("UNIFORM_COLOR")
            shader.uniform_float("color", line_color)
            print("outer: ", outer_vtxs)
            batch = batch_for_shader(shader, "TRI_STRIP", {"pos": outer_vtxs.tolist()})
            batch.draw(shader)

            shader.uniform_float("color", (0, 0, 0, 0))

            batch = batch_for_shader(
                shader,
                "TRI_STRIP",
                {"pos": inner_vtxs.tolist()},
            )
            batch.draw(shader)

        buffer = fb.read_color(0, 0, canvas_w, canvas_h, 4, 0, "UBYTE")

    offscreen.free()
    if image_name in bpy.data.images:
        img = bpy.data.images[image_name]
        bpy.data.images.remove(img)

    img = bpy.data.images.new(image_name, width=canvas_w, height=canvas_h, alpha=True)
    img.file_format = "PNG"
    img.alpha_mode = "STRAIGHT"
    img.filepath = output_path
    buffer.dimensions = canvas_w * canvas_h * 4
    img.pixels = [v / 255 for v in buffer]
    img.save()
    bpy.data.images.remove(img)
