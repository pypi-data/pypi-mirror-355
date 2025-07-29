from ..utils import (
    write_draw_rectangle,
    write_text_center,
    write_draw_rectangle_style
)


def financial(image, context):
    height = 8
    financial_title(image, 28, height)
    financial_body(image, 29, height, context)


def financial_title(image, width, height):
    coordinate = {
        'width': width,
        'height': height,
        'offset_left': 0,
        'offset_top': 21,
        'left': 0,
        'top': 0,
    }
    write_draw_rectangle(image, coordinate)
    pid_title_text = 'FINANCEIRO'
    pid_title_font = 'MYRIADPRO-BOLD.OTF'
    pid_title_font_fill = '#000'
    pid_title_font_size = 12
    write_text_center(image, coordinate, pid_title_text, pid_title_font, pid_title_font_fill, pid_title_font_size)


def financial_body(image, width, height, context):
    financeiro_status = context['financial'].upper()
    financeiro_fill = 'yellow'
    pid_title_font_fill = '#000'
    if financeiro_status == 'LIBERADO':
        financeiro_fill = 'green'
        pid_title_font_fill = '#fff'
    coordinate = {
        'width': width,
        'height': height,
        'offset_left': width - 1,
        'offset_top': 21,
        'left': 0,
        'top': 0,
    }
    style = {
        'fill': financeiro_fill,
        'outline': '#000',
        'stroke': 1,
    }
    write_draw_rectangle_style(image, coordinate, style)
    pid_title_text = financeiro_status
    pid_title_font = 'MYRIADPRO-BOLD.OTF'
    pid_title_font_size = 12
    write_text_center(image, coordinate, pid_title_text, pid_title_font, pid_title_font_fill, pid_title_font_size)