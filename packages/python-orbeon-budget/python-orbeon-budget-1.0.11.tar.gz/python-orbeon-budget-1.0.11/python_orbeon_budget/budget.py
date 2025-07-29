from io import BytesIO
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.utils import ImageReader


class Budget(canvas.Canvas):

    def __init__(self, filename, context):
        super().__init__(filename, pagesize=A4)
        self.width, self.height = A4
        self.num_page = 1
        self.context = context
        self.current_height = 0
        # extra
        self.h1 = "Orçamento"
        self.main_stroke_color = '#c9c9c9'
        self.main_font = 'Helvetica'
        self.main_font_bold = 'Helvetica-Bold'
        self.small_font_size = 9
        self.main_font_size = 12
        self.h1_font_size = 23
        self.h2_font_size = 18
        self.h3_font_size = 13
        self.h2_font_primary = '#000000'
        self.h2_font_secondary = '#444544'

    def draw(self):
        self.setStrokeColor(colors.HexColor(self.main_stroke_color))
        self.watermark()
        self.header()
        self.title()
        self.subtitle()
        self.customer()
        self.salesperson()
        self.valid()
        self.production_time()
        self.product()
        self.delivery()
        self.payment()
        self.condition_title()
        self.condition_list()
        self.footer()
        self.stamp_and_salesperson_signature()
        self.metadata()

    def watermark(self):
        watermark = self.context['organization']['watermark']
        if not watermark:
            return
        img = Image.open(BytesIO(watermark))
        img_width, img_height = img.size
        watermark_width = self.width - 100
        watermark_height = (img_height / img_width) * watermark_width  # Mantém proporção
        x_position = (self.width - watermark_width) / 2
        y_position = (self.height - watermark_height) / 2
        image_reader = ImageReader(BytesIO(watermark))
        self.drawImage(image_reader, x_position, y_position, width=watermark_width, height=watermark_height, mask='auto')

    def header(self):
        logo = self.context['organization']['logo']
        img = Image.open(BytesIO(logo))
        img_width, img_height = img.size
        height_target = 40
        width_target = (img_width / img_height) * height_target
        x_logo = 50
        y_logo = (self.height - 70) + (70 - height_target) / 2
        self.drawImage(ImageReader(BytesIO(logo)), x_logo, y_logo, width=width_target, height=height_target, mask='auto')
        y_linha = self.height - 70
        self.line(50, y_linha, self.width - 50, y_linha)
        self.current_height = 70
        self.header_organization()

    def header_organization(self):
        header_height = self.current_height
        center_header = header_height / 2
        self.setFont(self.main_font_bold, self.small_font_size)
        text_spacing = 3
        organization_name_height = self.height - (center_header - text_spacing)
        organization_cnpj_height = self.height - (center_header + self.small_font_size)
        self.drawRightString(self.width - 50, organization_name_height, self.context['organization']['name'])
        self.drawRightString(self.width - 50, organization_cnpj_height, f"CNPJ: {self.context['organization']['cnpj']}")

    def title(self):
        self.current_height = self.height - self.current_height - 30
        self.setFont(self.main_font, self.h1_font_size)
        self.drawString(50, self.current_height, self.h1)

    def subtitle(self):
        self.current_height -= 25
        self.setFont(self.main_font, self.h3_font_size)
        self.drawString(50, self.current_height, f"{self.context['dateline']},")
        self.current_height -= 20
        self.setFont(self.main_font, self.main_font_size)
        budget_id = f"{int(self.context['id']):06d}".replace(",", ".")
        self.drawString(50, self.current_height, f"Número do orçamento: {budget_id}")
        self.current_height -= 10

    def customer(self):
        customer = self.context.get('customer')
        if customer:
            organization = customer.get('organization', None)
            if organization:
                self.customer_organization(organization)
                return
            person = customer.get('person', None)
            if person:
                self.customer_person(person)

    def customer_organization(self, company):
        max_length = 45
        self.current_height = self.current_height - 20
        self.setFillColor(colors.HexColor(self.h2_font_secondary))
        self.setFont(self.main_font, self.main_font_size)
        title = 'Cliente (empresa):'
        value = company['name']
        company_id = company.get('id', None)
        if company_id:
            value = f"{value} ({company_id})"
        diff = len(value) - max_length
        if diff >= 1:
            value = value[:len(value) - diff]
        self.drawString(50, self.current_height, title)
        self.drawRightString(self.width - 50, self.current_height, value)
        self.current_height = self.current_height - 10
        self.line(50, self.current_height, self.width - 50, self.current_height)
        responsible = company.get('responsible', None)
        self.customer_organization_responsible(responsible)

    def customer_organization_responsible(self, responsible):
        if responsible:
            max_length = 45
            self.current_height = self.current_height - 20
            self.drawString(50, self.current_height, 'Cliente (responsável):')
            diff = len(responsible) - max_length
            if diff >= 1:
                responsible = responsible[:len(responsible) - diff]
            self.drawRightString(self.width - 50, self.current_height, responsible)
            self.current_height = self.current_height - 10
            self.line(50, self.current_height, self.width - 50, self.current_height)

    def customer_person(self, person):
        max_length = 45
        self.current_height = self.current_height - 20
        self.setFillColor(colors.HexColor(self.h2_font_secondary))
        self.setFont(self.main_font, self.main_font_size)
        title = 'Cliente:'
        value = person['name']
        person_id = person.get('id', None)
        if person_id:
            value = f"{value} ({person_id})"
        diff = len(value) - max_length
        if diff >= 1:
            value = value[:len(value) - diff]
        self.drawString(50, self.current_height, title)
        self.drawRightString(self.width - 50, self.current_height, value)

    def salesperson(self):
        self.current_height = self.current_height - 20
        self.setFillColor(colors.HexColor(self.h2_font_secondary))
        self.setFont(self.main_font, self.main_font_size)
        title = self.context['salesperson']['text']
        value = self.context['salesperson']['value']
        self.drawString(50, self.current_height, title)
        self.drawRightString(self.width - 50, self.current_height, value)
        self.current_height = self.current_height - 10
        self.line(50, self.current_height, self.width - 50, self.current_height)

    def valid(self):
        self.current_height = self.current_height - 20
        self.setFillColor(colors.HexColor(self.h2_font_secondary))
        self.setFont(self.main_font, self.main_font_size)
        title = self.context['valid']['text']
        value = self.context['valid']['value']
        self.drawString(50, self.current_height, title)
        self.drawRightString(self.width - 50, self.current_height, value)
        self.current_height = self.current_height - 10
        self.line(50, self.current_height, self.width - 50, self.current_height)

    def production_time(self):
        self.current_height = self.current_height - 20
        self.setFillColor(colors.HexColor(self.h2_font_secondary))
        self.setFont(self.main_font, self.main_font_size)
        title = self.context['production_time']['text']
        value = self.context['production_time']['value']
        self.drawString(50, self.current_height, title)
        self.drawRightString(self.width - 50, self.current_height, value)
        self.current_height = self.current_height - 10
        self.line(50, self.current_height, self.width - 50, self.current_height)

    def product(self):
        self.product_title()
        self.product_table()
        self.product_total()

    def product_title(self):
        self.current_height -= 25
        self.setFillColor(colors.HexColor('#000000'))
        self.setFont(self.main_font, self.h3_font_size)
        self.drawString(50, self.current_height, "Produto(s)")

    def product_table(self):
        self.current_height -= 10
        product_list = self.context['product']['list']
        self.setFont(self.main_font, self.main_font_size)
        table_width = self.width - 100
        colWidths = [table_width * 0.45, table_width * 0.15, table_width * 0.20, table_width * 0.20]
        styles = getSampleStyleSheet()
        header_style = styles["Normal"]
        header_style.alignment = 1
        body_style = styles["BodyText"]
        body_style.wordWrap = 'CJK'
        data = [[
            Paragraph("Produto", header_style), 
            Paragraph("Quantidade", header_style), 
            Paragraph("Valor Unitário (R$)", header_style), 
            Paragraph("Subtotal (R$)", header_style)
        ]]
        row_heights = [30]
        for product in product_list:
            product_style = getSampleStyleSheet()["BodyText"]
            product_style.wordWrap = 'CJK'
            product_style.alignment = 0
            product_paragraph = Paragraph(product["name"], product_style)
            td_style = getSampleStyleSheet()["BodyText"]
            td_style.alignment = 1
            quantity_paragraph = Paragraph(product["quantity"], td_style)
            unit_price_paragraph = Paragraph(product["unit_price"], td_style)
            subtotal_paragraph = Paragraph(product["subtotal"], td_style)
            _, product_height = product_paragraph.wrap(colWidths[0], 0)
            _, quantity_height = quantity_paragraph.wrap(colWidths[1], 0)
            _, unit_price_height = unit_price_paragraph.wrap(colWidths[2], 0)
            _, subtotal_height = subtotal_paragraph.wrap(colWidths[3], 0)
            row_height = max(product_height, quantity_height, unit_price_height, subtotal_height)
            row_heights.append(row_height + 5)
            data.append([product_paragraph, quantity_paragraph, unit_price_paragraph, subtotal_paragraph])
        table = Table(data, colWidths=colWidths, rowHeights=row_heights)
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), self.main_font_bold),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
        table.setStyle(style)
        total_table_height = sum(row_heights)
        self.current_height -= total_table_height
        table.wrapOn(self, 50, self.current_height)
        table.drawOn(self, 50, self.current_height)

    def product_total(self):
        self.current_height -= 25
        total = self.context['product']['total']
        self.setFont(self.main_font, self.h3_font_size)
        self.setFillColor(colors.HexColor(self.h2_font_primary))
        self.drawString(50, self.current_height, "Total")
        self.drawRightString(self.width - 50, self.current_height, total)
        self.current_height = self.current_height - 10
        self.line(50, self.current_height, self.width - 50, self.current_height)

    def delivery(self):
        title = self.context.get("delivery", {}).get("title", None)
        self.large_title(title, 25)
        text = self.context.get("payment", {}).get("text", None)
        if not text:
            return
        self.current_height -= 10
        text = self.context.get("delivery", {}).get("text", None)
        if not text:
            return
        bullet_style = getSampleStyleSheet()["BodyText"]
        bullet_style.alignment = TA_LEFT
        bullet_style.leading = 14
        max_width = self.width - 110
        for condition in [text]:
            self.list_item(condition, max_width, bullet_style)

    def payment(self):
        self.payment_title()
        self.payment_list()

    def payment_title(self):
        self.current_height -= 18
        self.setFont(self.main_font, self.h3_font_size)
        title = self.context.get("payment", {}).get("title", None)
        if not title:
            return
        self.drawString(50, self.current_height, title)

    def payment_list(self):
        self.current_height -= 10
        text = self.context.get("payment", {}).get("text", None)
        if not text:
            return
        payment_conditions = [text]
        bullet_style = getSampleStyleSheet()["BodyText"]
        bullet_style.alignment = TA_LEFT
        bullet_style.leading = 14
        max_width = self.width - 110
        for payment_condition in payment_conditions:
            self.list_item(payment_condition, max_width, bullet_style)

    def condition_title(self):
        self.current_height -= 18
        self.setFont(self.main_font, self.h3_font_size)
        title = self.context.get("condition", {}).get("title", None)
        if not title:
            return
        self.drawString(50, self.current_height, title)

    def condition_list(self):
        self.current_height -= 10
        conditions = self.context.get("condition", {}).get("conditions", None)
        if not conditions:
            return
        bullet_style = getSampleStyleSheet()["BodyText"]
        bullet_style.alignment = TA_LEFT
        bullet_style.leading = 14
        max_width = self.width - 110
        for condition in conditions:
            self.list_item(condition, max_width, bullet_style)

    def list_item(self, condition, max_width, bullet_style):
        bullet_text = "• " + condition
        paragraph = Paragraph(bullet_text, bullet_style)
        _, h = paragraph.wrap(max_width, self.current_height)
        self.current_height -= h 
        paragraph.drawOn(self, 60, self.current_height)
        self.current_height -= 4 

    def large_title(self, title, margin_top):
        self.current_height -= margin_top
        self.setFont(self.main_font, self.h3_font_size)
        if not title:
            return
        self.drawString(50, self.current_height, title)

    def footer(self):
        self.setFillColor(colors.HexColor(self.h2_font_secondary))
        linha_y = 70
        self.line(50, linha_y, self.width - 50, linha_y)
        self.setFont(self.main_font, self.small_font_size)
        row_1 = self.context['footer']['row_1']
        row_2 = self.context['footer']['row_2']
        address = f"{self.context['organization']['address']}"
        self.drawString(50, linha_y - 15, row_1)
        self.drawString(50, linha_y - 30, row_2)
        self.drawString(50, linha_y - 45, address)
        self.drawString(self.width - 80, linha_y - 15, f"Página {self.num_page}")
        self.num_page += 1

    def stamp_and_salesperson_signature(self):
        stamp = self.context['organization']['stamp']
        signature = self.context['salesperson']['signature']
        y_position = 80
        target_height = None
        if not stamp and not signature:
            return
        if stamp:
            img_reader, target_width, target_height = self.rotated_img(stamp, 180, 5)
            x_position = self.width - (target_width + 50)
            self.drawImage(img_reader, x_position, y_position, width=target_width, height=target_height, mask='auto')
        if signature:
            if target_height is None:
                target_height = 0
            self.salesperson_signature(signature, y_position, target_height)

    def salesperson_signature(self, signature, stamp_y_position, stamp_height):
        if not signature:
            return
        img_reader, target_width, target_height = self.rotated_img(signature, 150, 10)
        x_position = self.width - (target_width + 50)
        y_position = stamp_y_position + stamp_height - int(round(stamp_height / 100 * 30, 0))
        self.drawImage(img_reader, x_position, y_position, width=target_width, height=target_height, mask='auto')

    def rotated_img(self, img_bytes, target_width, angle):
        if not img_bytes:
            return
        img = Image.open(BytesIO(img_bytes))
        img = img.convert("RGBA")
        img = img.rotate(angle, expand=True)
        rotated_width, rotated_height = img.size
        target_width = target_width
        scale_factor = target_width / rotated_width
        target_height = int(rotated_height * scale_factor)
        img = img.resize((target_width, target_height), Image.LANCZOS)
        img_buffer = BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        img_reader = ImageReader(img_buffer)
        return img_reader, target_width, target_height

    def metadata(self):
        budget_id = self.context.get('id')
        title = 'Orçamento'
        if budget_id:
            title = f"{title} {budget_id}"
        self.setTitle(title)

    def new_page(self):
        self.showPage()
        self.draw()
