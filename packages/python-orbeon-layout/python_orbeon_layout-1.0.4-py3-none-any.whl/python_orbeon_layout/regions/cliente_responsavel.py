from ..utils import (
    write_draw_rectangle_style,
    write_text_left
)


def cliente(image, context):
    coordinate = {
        'width': 92,
        'height': 9,
        'offset_left': 96,
        'offset_top': 9,
        'left': 0,
        'top': 0,
    }
    style = {
        'fill': '#fff',
        'outline': '#000',
        'stroke': 1,
    }
    write_draw_rectangle_style(image, coordinate, style)
    customer_name = context['customer_name']
    value_text = customer_name[:55] + '\n' + context['customer_contact']
    value_font = 'MYRIADPRO-REGULAR.OTF'
    value_font_fill = '#000'
    value_font_size = 10
    coordinate['offset_left'] = coordinate['offset_left'] + 2
    write_text_left(image, coordinate, value_text, value_font, value_font_fill, value_font_size)


def responsavel(image, context):
    coordinate = {
        'width': 92,
        'height': 9,
        'offset_left': 96,
        'offset_top': 20,
        'left': 0,
        'top': 0,
    }
    style = {
        'fill': '#fff',
        'outline': '#000',
        'stroke': 1,
    }
    write_draw_rectangle_style(image, coordinate, style)
    value_text = 'RESPONSÁVEL: ' + context['responsible_name'] + '\n' + context['responsible_contact']
    value_font = 'MYRIADPRO-REGULAR.OTF'
    value_font_fill = '#000'
    value_font_size = 10
    coordinate['offset_left'] = coordinate['offset_left'] + 2
    write_text_left(image, coordinate, value_text, value_font, value_font_fill, value_font_size)