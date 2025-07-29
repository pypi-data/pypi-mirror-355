from ..utils import (
    write_draw_rectangle_style,
    write_text_center
)


def data_inicio(image, context):
    coordinate = {
        'width': 46,
        'height': 7,
        'offset_left': 96,
        'offset_top': 0,
        'left': 0,
        'top': 0,
    }
    style = {
        'fill': '#CEE2C0',
        'outline': '#000',
        'stroke': 1,
    }
    write_draw_rectangle_style(image, coordinate, style)
    due_date_value_text = context['data_inicio']
    due_date_value_text = 'INÍCIO: ' + due_date_value_text
    due_date_value_font = 'MYRIADPRO-BOLD.OTF'
    due_date_value_font_fill = '#000'
    due_date_value_font_size = 10
    write_text_center(image, coordinate, due_date_value_text, due_date_value_font, due_date_value_font_fill, due_date_value_font_size)


def data_conclusao(image, context):
    coordinate = {
        'width': 46,
        'height': 7,
        'offset_left': 96 + 46,
        'offset_top': 0,
        'left': 0,
        'top': 0,
    }
    style = {
        'fill': '#ff8b8b',
        'outline': '#000',
        'stroke': 1,
    }
    write_draw_rectangle_style(image, coordinate, style)
    due_date_value_text = context['data_conclusao']
    due_date_value_text = 'CONCLUSÃO: ' + due_date_value_text
    due_date_value_font = 'MYRIADPRO-BOLD.OTF'
    due_date_value_font_fill = '#000'
    due_date_value_font_size = 10
    write_text_center(image, coordinate, due_date_value_text, due_date_value_font, due_date_value_font_fill, due_date_value_font_size)