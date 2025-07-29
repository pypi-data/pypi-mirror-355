from PIL import Image


from ..utils import (
    SCALE,
    write_draw_rectangle,
    get_center_middle_image_box
)


def body(image, context):
    coordinate = {
        'width': 296,
        'height': 166 + 12,
        'offset_left': 0,
        'offset_top': 41 - 12,
        'left': 0,
        'top': 2,
    }
    write_draw_rectangle(image, coordinate)
    body_image_insert(image, coordinate, context)


def body_image_insert(image, coordinate, context):
    width_ = coordinate['width'] - 2
    height_ = coordinate['height'] - 2
    body_bytesio = context['body_bytesio']
    body_image = get_body_image(body_bytesio, width_, height_)
    box = get_center_middle_image_box(body_image, coordinate)
    image.paste(body_image, box)


def get_body_image(body_bytesio, width, height):
    if body_bytesio:
        body_image = Image.open(body_bytesio)
    else:
        raise Exception('Não é possível gerar o layout, pois não há uma imagem para o corpo do layout.')
    body_image_adjusted = body_image_adjust(body_image, width, height)
    return body_image_adjusted


def body_image_adjust(body_image, width, height):
    body_image_width, body_image_height = body_image.size
    body_image_ratio = body_image_width / body_image_height
    if body_image_ratio >= 1:
        body_image_width_new = width * SCALE
        body_image_height_new = round(body_image_width_new * (1 / body_image_ratio))
        body_image_height_new_real_size = body_image_height_new / SCALE 
        if body_image_height_new_real_size > height:
            taxa_de_reducao = height/body_image_height_new_real_size-1
            body_image_width_new = round(body_image_width_new * (1 + taxa_de_reducao))
            body_image_height_new = round(body_image_height_new * (1 + taxa_de_reducao))
    else:
        body_image_height_new = height * SCALE
        body_image_width_new = round(body_image_height_new * body_image_ratio)
    size = (body_image_width_new, body_image_height_new)
    return body_image.resize(size, Image.LANCZOS)
