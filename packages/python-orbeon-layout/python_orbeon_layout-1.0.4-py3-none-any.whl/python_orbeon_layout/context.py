import textwrap


def get_context_clean(context_raw):
  context = {
    'sales_order_id':       context_raw['sales_order_id'],
    'layout_id':            context_raw['layout_id'],
    'data_inicio':          context_raw['data_inicio'],
    'data_conclusao':       context_raw['data_conclusao'],
    'customer_name':        get_cliente_nome(context_raw),
    'customer_contact':     get_cliente_contato(context_raw),
    'responsible_name':     get_responsavel_nome(context_raw),
    'responsible_contact':  get_responsavel_contato(context_raw),
    'body_bytesio':         context_raw['body_bytesio'],
    'logo_bytesio':         context_raw['logo_bytesio'],
    'financial':            context_raw['financeiro'].upper().strip(),
    'shipping':             context_raw['shipping'],
  }
  return context


def get_cliente_nome(context_raw):
  cliente_nome = context_raw['cliente_nome']
  customer_name = 'CLIENTE: {}'.format(cliente_nome).upper()
  customer_name = truncatechars(customer_name, 60)
  return customer_name.strip()


def get_cliente_contato(context_raw):
  cliente_contato = context_raw['cliente_contato']
  customer_contact = 'CONTATO: {}'.format(cliente_contato)
  return customer_contact.strip()


def get_responsavel_nome(context_raw):
  responsavel_nome = context_raw['responsavel_nome']
  responsavel_nome = truncatechars(responsavel_nome, 44)
  return responsavel_nome.strip()


def get_responsavel_contato(context_raw):
  responsavel_contato = context_raw['responsavel_contato']
  responsavel_contato = 'CONTATO: {}'.format(responsavel_contato).upper()
  return responsavel_contato.strip()


def truncatechars(string, width=10):
  return textwrap.shorten(string, width=width, placeholder="...")
