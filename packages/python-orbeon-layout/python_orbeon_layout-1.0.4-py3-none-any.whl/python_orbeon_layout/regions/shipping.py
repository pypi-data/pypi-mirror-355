from ..utils import (
    write_draw_rectangle,
    write_text_left_top,
    write_text_center,
    write_draw_rectangle_style
)


def shipping(a4, context):
    shipping_title(a4, context)
    shipping_body(a4, context)


def shipping_title(image, context):
    coordinate = {
        'width': 106,
        'height': 7,
        'offset_left': 190,
        'offset_top': 0,
        'left': 0,
        'top': 0,
    }
    style = {
        'fill': '#fa985f',
        'outline': '#000',
        'stroke': 1,
    }
    write_draw_rectangle_style(image, coordinate, style)
    value_font = 'MYRIADPRO-BOLD.OTF'
    value_font_fill = '#000'
    value_font_size = 11
    text = context['shipping']['method'] 
    write_text_center(image, coordinate, text, value_font, value_font_fill, value_font_size)


def shipping_body(image, context):
    context_shipping = context['shipping'] 
    context_method = context_shipping['method'].upper()
    coordinate = {
        'width': 106,
        'height': 20,
        'offset_left': 190,
        'offset_top': 7,
        'left': 0,
        'top': 2,
    }
    write_draw_rectangle(image, coordinate)

    retirada = False
    if 'RETIRADA' in context_method:
        retirada = True
    shipping_send(image, retirada)
    shipping_address(image, context_shipping)


def shipping_send(image, retirada=False):
    coordinate = {
        'width': 106,
        'height': 20,
        'offset_left': 190,
        'offset_top': 7,
        'left': 2,
        'top': 4,
    }
    if retirada:
        value_text = 'ENDEREÇO PARA "RETIRADA" DA MERCADORIA:'
    else:
        value_text = 'ENDEREÇO DE "ENVIO" DA MERCADORIA:'
    value_font = 'MYRIADPRO-BOLD.OTF'
    value_font_fill = '#bf1515'
    value_font_size = 9
    write_text_left_top(image, coordinate, value_text, value_font, value_font_fill, value_font_size)


def shipping_address(image, context):
    offset_left_default = 190
    value_font_fill = '#000'
    value_font_size = 8
    font_bold = 'MYRIADPRO-BOLD.OTF'
    font_regular = 'MYRIADPRO-REGULAR.OTF'
    coordinate = {
        'width': 106,
        'height': 20,
        'offset_left': offset_left_default,
        'offset_top': 7,
        'left': 2,
        'top': 8,
    }

    public_place = context['public_place']
    number = context['number']
    complement = context['complement']
    neighborhood = context['neighborhood']
    city = context['city']
    state_code = context['state_code']
    postal_code = '30190110'
    location_reference = context['location_reference']
    notes = context['notes']

    write_text_left_top(image, coordinate, 'ENDEREÇO: ', font_bold, value_font_fill, value_font_size)

    value_text = f"{public_place}, NÚMERO: {number}"
    if complement:
        value_text = f'{value_text} | {complement}'.upper()
    coordinate['offset_left'] = coordinate['offset_left'] + 16
    write_text_left_top(image, coordinate, value_text, font_regular, value_font_fill, value_font_size)

    coordinate['offset_left'] = offset_left_default
    coordinate['offset_top'] = coordinate['offset_top'] + 3
    write_text_left_top(image, coordinate, 'BAIRRO | CIDADE:', font_bold, value_font_fill, value_font_size)

    coordinate['offset_left'] = coordinate['offset_left'] + 23
    text = f"{neighborhood} | {city}"
    write_text_left_top(image, coordinate, text.upper(), font_regular, value_font_fill, value_font_size)

    coordinate['offset_top'] = coordinate['offset_top'] + 3
    coordinate['offset_left'] = offset_left_default
    write_text_left_top(image, coordinate, 'UF - CEP:', font_bold, value_font_fill, value_font_size)
    
    coordinate['offset_left'] = coordinate['offset_left'] + 11
    text = f"{state_code} - {postal_code}".upper()
    write_text_left_top(image, coordinate, text, font_regular, value_font_fill, value_font_size)

    coordinate['offset_top'] = coordinate['offset_top'] + 3
    coordinate['offset_left'] = offset_left_default
    write_text_left_top(image, coordinate, 'REF. | OBS.:', font_bold, value_font_fill, value_font_size)

    text = f"{location_reference} | {notes}"
    text = text.upper()
    coordinate['offset_left'] = coordinate['offset_left'] + 14
    write_text_left_top(image, coordinate, text, font_regular, value_font_fill, value_font_size)
