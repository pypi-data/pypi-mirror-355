import unittest

from pathlib import Path
from python_orbeon_budget.budget import Budget


BASE_DIR = Path(__file__).resolve().parent.parent


def get_bytes(path):
    bytes = None
    with open(path, 'rb') as f:
        bytes = f.read()
    return bytes


def get_context():
    context = {
        'id': '381',
        'dateline': 'Belo Horizonte, 25 de Janeiro de 2025 às 14:35',
        "customer": {
            "organization": {
                "name": "ALFA COMPANY LTDA SA",
                "id": "07.677.888/0001-77",
                "responsible": "JOÃO LUCAS"
            },
            "person": {
                "name": "EDUARDO SILVA",
                "id": "101.222.333-44",
            }
        },
        "organization": {
            'name': 'BETA COMPANY LTDA - EPP',
            'cnpj': '06.544.076/0001-88',
            'address': "Rua Bacuri, nº 763 - Barro Azul - Belo Horizonte - MG - CEP: 99.950-190",
            'logo': get_bytes(BASE_DIR / 'python_orbeon_budget' / 'contents' / 'logo.png'),
            'stamp': get_bytes(BASE_DIR / 'python_orbeon_budget' / 'contents' / 'stamp.png'),
            'watermark': get_bytes(BASE_DIR / 'python_orbeon_budget' / 'contents' / 'watermark.png')
        },
        'salesperson': {
            'text': 'Vendedor | Telefone/WhatsApp:',
            'value': 'Eduardo Silva | (31) 98343-3488',
            'signature': get_bytes(BASE_DIR / 'python_orbeon_budget' / 'contents' / 'signature.png'),
        },
        'valid': {
            'text': 'Válido por:',
            'value': '7 dias úteis'
        },
        'production_time': {
            'text': 'Prazo de produção:',
            'value': '5 dias úteis'
        },
        "product": {
            "list": [
                {"name": "Teclado Mecânico", "quantity": "2,0000", "unit_price": "R$ 250,00", "subtotal": "R$ 500,00"},
                {"name": "Mouse Gamer", "quantity": "1,0000", "unit_price": "R$ 180,50", "subtotal": "R$ 180,50"},
                {"name": "Monitor 24''", "quantity": "3,0000", "unit_price": "R$ 1200,00", "subtotal": "R$ 3.600,00"},
                {"name": "Headset Bluetooth", "quantity": "1,0000", "unit_price": "R$ 350,00", "subtotal": "R$ 350,00"},
                {"name": "Cadeira Gamer", "quantity": "1,0000", "unit_price": "R$ 1500,00", "subtotal": "R$ 1500,00"},
                {"name": "Mousepad RGB", "quantity": "2,0000", "unit_price": "R$ 120,00", "subtotal": "R$ 240,00"},
            ],
            "total": "R$ 1.500,00"
        },
        "delivery": {
            "title": 'Entrega',
            "text": "Retirada na loja",
        },
        "payment": {
            "title": 'Condições de Pagamento',
            "text": "Pagamento antecipado: pix, dinheiro ou cartão (parcelamos em até 3x sem juros)",
        },
        "condition": {
            "title": "Condições Gerais",
            "conditions": [
                "A data de entrega é válida desde que o prazo para upload seja respeitado e o pagamento esteja aprovado.",
                "O valor total corresponde à soma dos preços dos produtos. Para itens com múltiplas quantidades, todos os valores são somados.",
                "Os valores estão sujeitos a alterações sem aviso prévio.",
                "Este orçamento tem validade de 72 horas."
            ],
        },
        'footer': {
            'row_1': "Scápole Camisetas Personalizadas - scapole.com",
            'row_2': "Contato: (31) 3207-0000 | contato@scapole.com"
        },
    }
    return context


class TestBudget(unittest.TestCase):

    def test_gen(self):
        context = get_context()
        file_save_path = BASE_DIR  / 'generated_files_saved/orcamento.pdf'
        file_save_path.parent.mkdir(parents=True, exist_ok=True)
        budget = Budget('generated_files_saved/orcamento.pdf', context)
        budget.draw()
        # for i in range(1, 4):
        #     budget.new_page()
        budget.save()
        empty = True
        if file_save_path.exists():
            if file_save_path.stat().st_size > 500:
                empty = False
        self.assertFalse(empty)


if __name__ == "__main__":
    unittest.main()
