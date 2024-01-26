import bpy
import datetime
import secrets
import os


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
    _draw_rect(output_path, src_rect.width, src_rect.height, border_size, border_color)
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
    img_strip.transform.offset_x = src_rect.x - img_rect.x - border_size
    img_strip.transform.offset_y = src_rect.y - img_rect.y - border_size
    img_strip.color_tag = "COLOR_01"
    return img_strip


def _make_unique_name(prefix="___"):
    return "{0}{1}_{2}".format(
        prefix, secrets.token_urlsafe(6), datetime.datetime.now().timestamp()
    )


def _draw_rect(output_path, width, height, border_size=5, border_color=[1, 0, 0, 1]):
    # print(">>>_draw_rect")
    rect_width = width + border_size * 2
    rect_height = height + border_size * 2
    img_name = _make_unique_name()

    img = bpy.data.images.new(
        img_name, width=rect_width, height=rect_height, alpha=True
    )
    img.file_format = "PNG"
    img.alpha_mode = "STRAIGHT"
    img.filepath = output_path

    default_pixel = [0, 0, 0, 0]
    len_of_pxs = rect_width * rect_height
    # img.pixels = default_pixel * len_of_pxs
    wk_pixels = default_pixel * len_of_pxs
    _draw_straight_line(
        wk_pixels,
        rect_width,
        rect_height,
        (0, 0),
        (0, rect_height - 1),
        border_size,
        border_color,
    )
    _draw_straight_line(
        wk_pixels,
        rect_width,
        rect_height,
        (rect_width - border_size, 0),
        (rect_width - border_size, rect_height - 1),
        border_size,
        border_color,
    )
    _draw_straight_line(
        wk_pixels,
        rect_width,
        rect_height,
        (0, 0),
        (rect_width - 1, 0),
        border_size,
        border_color,
    )
    _draw_straight_line(
        wk_pixels,
        rect_width,
        rect_height,
        (0, rect_height - border_size - 1),
        (rect_width - 1, rect_height - border_size - 1),
        border_size,
        border_color,
    )
    img.pixels = wk_pixels
    img.save()
    bpy.data.images.remove(img)


def _draw_straight_line(pixels, width, height, p1, p2, border_size, border_color):
    if p1[0] == p2[0]:
        _draw_vertical_line(pixels, width, height, p1, p2, border_size, border_color)
    elif p1[1] == p2[1]:
        _draw_horizontal_line(pixels, width, height, p1, p2, border_size, border_color)
    else:
        raise NotImplementedError("直線以外は未実装")


def _draw_vertical_line(pixels, width, height, p1, p2, border_size, border_color):
    color = border_color[:]
    depth = len(color)
    dh = p2[1] - p1[1]
    for hidx in range(dh):
        start_idx = (p1[0] * depth) + (width * depth * (p1[1] + hidx))
        end_idx = start_idx + depth * border_size
        pixels[start_idx:end_idx] = color * border_size


def _draw_horizontal_line(pixels, width, height, p1, p2, border_size, border_color):
    color = border_color[:]
    depth = len(color)
    for bsidx in range(border_size):
        start_idx = (p1[0] * depth) + (width * depth * (p1[1] + bsidx))
        end_idx = start_idx + depth * (p2[0] - p1[0] + 1)
        pixels[start_idx:end_idx] = color * (p2[0] - p1[0] + 1)
