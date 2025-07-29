from .context import get_context_clean
from .regions.financial import financial
from .regions.logo import logo
from .regions.body import body
from .regions.shipping import shipping
from .regions.cliente_responsavel import cliente, responsavel
from .regions.data_inicio_conclusao import data_inicio, data_conclusao
from .regions.sales_order_id_and_layout_id import sales_order_id, layout_id
from .utils import (
	add_margin,
	save_file as save_file_,
	get_final_result,
	a4 as a4i
)


def layout_draw(context_raw, save_file=False):
	context = get_context_clean(context_raw)
	a4 = a4i()
	sales_order_id(a4, context)
	layout_id(a4, context)
	financial(a4, context)
	logo(a4, context)
	data_inicio(a4, context)
	data_conclusao(a4, context)
	cliente(a4, context)
	responsavel(a4, context)    
	shipping(a4, context)
	body(a4, context)
	a4 = add_margin(a4)
	result = get_final_result(a4)
	save_file_(result, save_file)
	return result
