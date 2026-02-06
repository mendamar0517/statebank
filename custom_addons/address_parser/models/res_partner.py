# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = "res.partner"

    address_raw = fields.Text(string="Raw Address")

    sumname = fields.Char(string="SUMNAME")
    horooid = fields.Integer(string="HOROOID")
    bair = fields.Integer(string="BAIR")
    korpus = fields.Char(string="KORPUS")
    xaalga = fields.Integer(string="XAALGA")

    address_confidence = fields.Float(string="Confidence", default=0.0)
    address_pattern = fields.Char(string="Matched pattern")
    address_is_trusted = fields.Boolean(string="Trusted", default=False)

    # -------------------------
    # UI onchange
    # -------------------------
    @api.onchange("address_raw")
    def _onchange_address_raw(self):
        for rec in self:
            rec._parse_address_safe()

    # -------------------------
    # Create / Write hooks (production-safe)
    # -------------------------
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # create дээр parse (avoid recursion with context flag)
        records.with_context(skip_address_parse=False)._parse_address_safe()
        return records

    def write(self, vals):
        res = super().write(vals)
        # зөвхөн address_raw өөрчлөгдвөл parse хийе
        if "address_raw" in vals and not self.env.context.get("skip_address_parse"):
            self._parse_address_safe()
        return res

    # -------------------------
    # Core logic
    # -------------------------
    def _clear_address(self):
        for rec in self:
            rec.sumname = False
            rec.horooid = 0
            rec.bair = 0
            rec.korpus = "0"
            rec.xaalga = 0
            rec.address_confidence = 0.0
            rec.address_pattern = False
            rec.address_is_trusted = False

    def _parse_address_safe(self):
        """
        Exception гарсан ч UI-г унагаахгүй.
        Log дээр алдааг гаргана.
        """
        for rec in self:
            raw = (rec.address_raw or "").strip()
            if not raw:
                rec._clear_address()
                continue

            try:
                from .address_rules import normalize_address, parse_with_rules
                norm = normalize_address(raw)
                r = parse_with_rules(norm)

                rec.sumname = r.get("SUMNAME_PRED") or False
                rec.horooid = int(r.get("HOROOID_PRED") or 0)
                rec.bair = int(r.get("BAIR_PRED") or 0)
                rec.korpus = str(r.get("KORPUS_PRED") or "0")
                rec.xaalga = int(r.get("XAALGA_PRED") or 0)

                rec.address_confidence = float(r.get("CONFIDENCE") or 0.0)
                rec.address_pattern = r.get("MATCHED_PATTERN") or False

                is_partial = (rec.address_pattern == "xaalga only")
                rec.address_is_trusted = (not is_partial) and (rec.address_confidence >= 0.95) and (rec.horooid > 0) and (rec.bair > 0) and (rec.xaalga > 0)

                _logger.info(
                    "[address_parser] raw=%s | norm=%s | parsed=%s",
                    raw, norm, r
                )

            except Exception as e:
                _logger.exception("[address_parser] parse failed for raw=%s. error=%s", raw, e)
                # parse алдаа гарвал цэвэрлээд үлдээнэ
                rec._clear_address()
