from io import BytesIO

from pathlib import Path
from datetime import datetime
BASE_DIR = Path(__file__).resolve().parent.parent


def get_example_data():
  data = {
    'sales_order_id': '150',
    'layout_id': '15/20',
    'financeiro': 'LIBERADO',
    'data_inicio': datetime.now().strftime('%d/%m/%y %H:%M'),
    'data_conclusao': datetime.now().strftime('%d/%m/%y %H:%M'),
    'cliente_nome': 'JOÃO PEDRO DA SILVA COSTA QUENTE DO SUL E DO NORTE DO AMAZONAS',
    'cliente_contato': "(31) 9-8888-7777",
    'responsavel_nome': 'PEDRO LUCAS DA SILVA COSTA QUENTE DO SUL E DO NORTE DO PARÁ',
    'responsavel_contato': "(31) 9-8844-6644",
    'shipping': get_shipping(),
    'logo_bytesio': encapsulate_image_path_in_bytesio(BASE_DIR / 'data' / '500x500.png'),
    'body_bytesio': encapsulate_image_path_in_bytesio(BASE_DIR / 'data' / '1200x800.png'),
  }
  return data


def get_shipping():
  method = 'RETIRADA NA LOJA'
  public_place = 'Rua de Ouro'
  number = '456'
  complement = 'GALPAO A'
  neighborhood = 'Ouro Azul'
  city = 'Rio Preto'
  state_code = 'MG'
  postal_code = '30190110'
  location_reference = 'Prox. Club do Cruzeiro'
  note = 'Sucesso tem técnica'
  shipping = {
    'method': method,
    'public_place': public_place,
    'number': number,
    'complement': complement,
    'neighborhood': neighborhood,
    'city': city,
    'state_code': state_code,
    'postal_code': postal_code,
    'location_reference': location_reference,
    'notes': note,
  }
  return shipping


def encapsulate_image_path_in_bytesio(image_path) -> BytesIO:
  image_bytes = None
  with open(image_path, "rb") as image_file:
    image_bytes = BytesIO(image_file.read())
  return image_bytes
