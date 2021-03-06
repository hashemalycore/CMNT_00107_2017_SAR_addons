# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError
WASH_SELEC = (('q', 'q'), ('w', 'w'), ('e', 'e'), ('r', 'r'), ('t', 't'),
              ('u', 'u'), ('o', 'o'), ('p', 'p'), ('a', 'a'), ('f', 'f'),
              ('g', 'g'), ('h', 'h'), ('j', 'j'), ('k', 'k'), ('l', 'l'),
              ('x', 'x'), ('c', 'c'), ('v', 'v'), ('b', 'b'), ('m', 'm'),
              ('Q', 'Q'), ('E', 'E'), ('R', 'R'), ('T', 'T'), ('I', 'I'),
              ('O', 'O'), ('P', 'P'), ('A', 'A'), ('S', 'S'), ('D', 'D'),
              ('F', 'F'), ('G', 'G'), ('H', 'H'), ('J', 'J'), ('K', 'K'),
              ('L', 'L'), ('C', 'C'), ('B', 'B'), ('N', 'N'), ('M', 'M'))
CLEANING_SELEC = ((',', ','), ('.', '.'), ('-', '-'), ('W', 'W'), ('Y', 'Y'),
                  ('Z', 'Z'), ('X', 'X'), ('V', 'V'), (';', ';'), (':', ':'),
                  ('$', '$'), ('%', '%'), ('&', '&'), ('(', '('), (')', ')'),
                  ('?', '?'), ('U', 'U'), (',', ','))
IRONING_SELEC = (('i', 'i'), ('s', 's'), ('d', 'd'), ('n', 'n'),
                 ('+', '+'), ('*', '*'), ('!', '!'), ('/', '/'))
DRYING_SELEC = (('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'),
                ('6', '6'), ('7', '7'), ('0', '0'))
BLEACHED_SELEC = (('8', '8'), ('9', '9'))


class TextileModel(models.Model):

    _name = 'textile.model'
    _inherit = ["base_multi_image.owner"]

    reference = fields.Char(required=True)
    name = fields.Char(required=True)
    customer = fields.Many2one('res.partner')
    analytic_tag = fields.Many2one('account.analytic.tag', 'Season',
                                   domain=[('type', '=', 'season')])
    image = fields.Binary()
    version = fields.Integer(default=1)
    active = fields.Boolean(default=True)
    article_type = fields.Many2one('product.category', required=True)
    color = fields.Many2one('product.attribute.value',
                            domain=[('is_color', '=', True)])
    blanqueado = fields.Selection(BLEACHED_SELEC)
    lavado = fields.Selection(WASH_SELEC)
    limpieza = fields.Selection(CLEANING_SELEC)
    planchado = fields.Selection(IRONING_SELEC)
    secado = fields.Selection(DRYING_SELEC)
    measurement_image = fields.Binary()
    base_version = fields.Many2one('textile.model', 'Base version', copy=False)
    versions = fields.One2many('textile.model', compute='_compute_versions')
    premodel_variant = fields.Many2one('product.product', 'Premodel product')
    state = fields.Selection((('draft', 'Draft'), ('approved', 'Approved')),
                             default='draft')
    model_type = fields.Selection(
        (('premodel', 'Pre-model'), ('model', 'Model')))
    bom_lines = fields.One2many('mrp.bom.line', 'model_id', copy=True)

    size_type = fields.Many2one('product.attribute',
                                domain=[('is_size', '=', True)])
    sizes = fields.Many2many('product.attribute.value')
    colors = fields.Many2many(
        'product.attribute.value', 'model_colors_rel_2',
        domain=[('is_color', '=', True)])
    model_template = fields.Many2one('product.template')
    all_attributes = fields.Many2many('product.attribute.value',
                                      compute='_compute_all_values')
    premodel_id = fields.Many2one('textile.model', 'Premodel', readonly=True)
    composition_name = fields.Char(compute='_get_composition_name',
                                   string='Composition name')
    composition_id = fields.Many2one("product.composition",
                                     string="Composition")
    bom_cost = fields.Float(compute='_get_bom_cost', string='Bom Cost')
    pvp = fields.Float('PVP')
    bom_weight = fields.Float(compute='_get_bom_weight', string='BOM Weigth')
    bom_cost = fields.Float(compute='_get_bom_cost', string='BOM Cost')
    model_margin = fields.Float(compute='_get_model_margin', string='Margin')
    model_margin_per = fields.Float(compute='_get_model_margin',
                                    string='Margin %')
    color_attribute_id = fields.Many2one('product.attribute',
                                         string="Color Type",
                                         compute='_get_color_attribute')

    @api.multi
    def _get_color_attribute(self):
        domain = [('name', '=', 'Color')]
        att_obj = self.env['product.attribute'].search(domain, limit=1)
        if att_obj:
            for model in self:
                model.color_attribute_id = att_obj.id

    @api.multi
    @api.depends('bom_lines.product_id', 'bom_lines.product_qty')
    def _get_composition_name(self):
        for model in self:
            name_lst = []
            for line in model.bom_lines:
                if line.weight_per >= 30:
                    name = str(round(line.weight_per, 2)) + ' % ' + \
                        line.product_id.name
                    name_lst.append(name)
            model.composition_name = ', '.join(name_lst)

    @api.multi
    @api.depends('bom_lines.product_id', 'bom_lines.product_qty')
    def _get_bom_weight(self):
        for model in self:
            sum_weight = 0.0
            for line in model.bom_lines:
                sum_weight += line.product_id.weight * line.product_qty
            model.bom_weight = sum_weight

    @api.multi
    @api.depends('bom_lines.product_id', 'bom_lines.product_qty')
    def _get_bom_cost(self):
        for model in self:
            sum_cost = 0.0  # # for lines without variants
            var_cost = 0.0  # for lines with variants
            n_variants = 0.0

            # Get variants number
            if model.sizes or model.colors:
                # Both of them
                if model.sizes and model.colors:
                    n_variants = len(model.sizes) * len(model.colors)
                # Some of them
                else:
                    n_variants = len(model.sizes) + len(model.colors)

            for line in model.bom_lines:
                if not line.attribute_value_ids:
                    sum_cost += line.product_id.standard_price * \
                        line.product_qty
                else:
                    var_cost += line.product_id.standard_price * \
                        line.product_qty
                if n_variants:
                    var_cost /= n_variants
            model.bom_cost = sum_cost + var_cost

    @api.multi
    def create_composition(self):
        self.ensure_one()
        t_composition = self.env['product.composition']
        if self.composition_id:
            raise UserError(_('Composition is already setted.'))
        if not self.composition_name:
            raise UserError(_('No composition to create.'))

        objs = t_composition.search([('name', '=', self.composition_name)])
        if objs:
            raise UserError(_('Composition %s already exists' %
                            self.composition_name))
        vals = {
            'name': self.composition_name,
            'description': self.composition_name
        }
        comp = t_composition.create(vals)
        self.composition_id = comp.id

    @api.multi
    @api.depends('pvp', 'bom_cost')
    def _get_model_margin(self):
        for model in self:
            model.model_margin = model.pvp - model.bom_cost
            model.model_margin_per = 0.0
            if model.bom_cost:
                model.model_margin_per = (model.model_margin / model.bom_cost) * \
                    100

    @api.depends('sizes', 'colors')
    def _compute_all_values(self):
        for model in self:
            model.all_attributes = model.sizes + model.colors

    @api.multi
    def action_to_model(self):
        self.ensure_one()
        model = self.copy({'model_type': 'model', 'state': 'draft',
                           'premodel_id': self.id})
        model.bom_lines.write({'bom_id': False})
        action = self.env.ref('textile_base.textile_model_action')
        if not action:
            return
        action = action.read()[0]
        res = self.env.ref('textile_base.textile_model_view_form')
        action['views'] = [(res.id, 'form')]
        action['res_id'] = model.id
        action['context'] = False
        return action

    @api.multi
    def action_approve(self):
        self.ensure_one()
        self.state = 'approved'
        attributes = []
        if self.model_type == 'premodel':
            attributes = [
                (0, 0,
                 {'attribute_id':
                     self.env.ref('textile_base.color_attribute').id,
                  'value_ids': [(4, self.color.id)]})]
        else:
            attributes = [
                (0, 0,
                 {'attribute_id':
                     self.env.ref('textile_base.color_attribute').id,
                  'value_ids': [(4, x.id) for x in self.colors]}),
                (0, 0,
                 {'attribute_id': self.size_type.id,
                  'value_ids': [(4, x.id) for x in self.sizes]})]
        model_product = self.env['product.template'].create(
            {'name': self.name, 'image': self.image,
             'article_type': self.model_type,
             'composition_id': self.composition_id.id,
             'default_code': self.reference, 'categ_id': self.article_type.id,
             'attribute_line_ids': attributes, 'type': 'product'})

        bom = self.env['mrp.bom'].create(
            {'product_tmpl_id': model_product.id})
        self.bom_lines.write({'bom_id': bom.id})
        if self.model_type == 'premodel':
            self.premodel_variant = model_product.product_variant_id
            action = self.env.ref('product.product_normal_action')
            if not action:
                return
            action = action.read()[0]
            res = self.env.ref('product.product_normal_form_view')
            action['views'] = [(res.id, 'form')]
            action['res_id'] = self.premodel_variant.id
            action['context'] = False
        else:
            self.model_template = model_product
            action = self.env.ref('product.product_template_action')
            if not action:
                return
            action = action.read()[0]
            res = self.env.ref('product.product_template_only_form_view')
            action['views'] = [(res.id, 'form')]
            action['res_id'] = self.model_template.id
            action['context'] = False
        return action

    @api.multi
    @api.depends('base_version')
    def _compute_versions(self):
        for model in self:
            if not model.base_version:
                model.versions = False
                continue
            model.versions = self.search(
                [('base_version', '=', model.base_version.id),
                 ('id', '!=', model.id), '|', ('active', '=', True),
                 ('active', '=', False)])

    @api.multi
    def create_new_version(self):
        max_version = max([x.version for x in self.versions + self])
        args = {'version': max_version + 1,
                'base_version': self.base_version.id,
                'active': True}
        new_version = self.copy(args)
        self.write({'active': False})
        action = self.env.ref('textile_base.textile_premodel_action')
        if not action:
            return
        action = action.read()[0]
        res = self.env.ref('textile_base.textile_model_view_form')
        action['views'] = [(res.id, 'form')]
        action['res_id'] = new_version.id
        action['context'] = False
        return action

    @api.model
    def create(self, vals):
        res = super(TextileModel, self).create(vals)
        if not res.base_version:
            res.base_version = res.id
        return res
