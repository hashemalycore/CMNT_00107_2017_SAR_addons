# -*- coding: utf-8 -*-
from odoo import models, api

# ------------------------- CMNT PATCH ---------------------------------------
# Este es el arch que debe leeerse de base de datos, pero cuando va con lang
# en contexto, al hacer el read de la factura electronica de inditex, te
# sustituye la etiqueta de apertura:
# <v1:InditexInvoiceExtension xmlns:v1="http://www.inditex.com/documents/
# einvoicing/Facturae/InditexInvoiceExtension/v1.0">
# Cambiando el v1 por ns0, y en la etiqueta de cierre pone el valor dado al v1
# entre llaves quedando </{http://www.indi...}InditexInvoiceExtension/>
# Hacemos pues que solo para este informe el READ devuelva el xml tal cual
# está en el infomre. Ya que sino al hacerle un etree.fromString falla.
ARCH_FIXED = u'<t t-name="facturae_inditex.template_facturae_inditex">\n        <t t-call="l10n_es_facturae.facturae_header">\n            <t t-set="invoice" t-value="docs[0]"/>\n            <t t-set="company" t-value="invoice.company_id"/>\n            <t t-set="company_partner" t-value="company.partner_id"/>\n            <t t-set="invoice_partner" t-value="invoice.partner_id"/>\n            <FileHeader>\n                <SchemaVersion t-esc="\'3.2\'"/>\n                <Modality t-esc="\'I\'"/>\n                <InvoiceIssuerType t-esc="\'EM\'"/>\n                <Batch>\n                    <BatchIdentifier t-esc="company_partner.vat + invoice.number.replace(\'/\',\'\')"/>\n                    <InvoicesCount t-esc="\'1\'"/>\n                    <TotalInvoicesAmount>\n                        <TotalAmount t-esc="\'%.2f\' % invoice.amount_total"/>\n                    </TotalInvoicesAmount>\n                    <TotalOutstandingAmount>\n                        <TotalAmount t-esc="\'%.2f\' % invoice.amount_total"/>\n                    </TotalOutstandingAmount>\n                    <TotalExecutableAmount>\n                        <TotalAmount t-esc="\'%.2f\' % invoice.amount_total"/>\n                    </TotalExecutableAmount>\n                    <InvoiceCurrencyCode t-esc="invoice.currency_id.name"/>\n                </Batch>\n            </FileHeader>\n            <Parties>\n                <SellerParty>\n                    <t t-set="seller_type" t-value="\'F\' if company_partner.vat and company_partner.vat[2:3].isdigit() else \'J\'"/>\n                    <TaxIdentification>\n                        <PersonTypeCode t-esc="seller_type"/>\n                        <ResidenceTypeCode t-esc="\'R\'"/>\n                        <TaxIdentificationNumber t-esc="company_partner.vat"/>\n                    </TaxIdentification>\n                    <PartyIdentification t-esc="invoice_partner.seller_party_id"/>\n                    <Individual t-if="seller_type == \'F\'">\n                        <Name t-esc="company_partner.name"/>\n                        <FirstSurname t-esc="\'\'"/>\n                        <SecondSurname t-esc="\'\'"/>\n                        <t t-call="l10n_es_facturae.address_contact">\n                            <t t-set="partner" t-value="company_partner"/>\n                        </t>\n                    </Individual>\n                    <LegalEntity t-if="seller_type == \'J\'">\n                        <CorporateName t-esc="company_partner.name"/>\n                        <TradeName t-esc="company_partner.name"/>\n                        <t t-call="l10n_es_facturae.address_contact">\n                            <t t-set="partner" t-value="company_partner"/>\n                        </t>\n                    </LegalEntity>\n                </SellerParty>\n                <BuyerParty>\n                    <t t-set="buyer_type" t-value="\'F\' if company_partner.vat and invoice_partner.vat[2:3].isdigit() else \'J\'"/>\n                    <TaxIdentification>\n                        <PersonTypeCode t-esc="buyer_type"/>\n                        <ResidenceTypeCode t-esc="\'R\'"/>\n                        <TaxIdentificationNumber t-esc="invoice_partner.vat"/>\n                    </TaxIdentification>\n                    <PartyIdentification t-esc="invoice_partner.buyer_party_id"/>\n                    <Individual t-if="buyer_type == \'F\'">\n                        <Name t-esc="invoice_partner.name"/>\n                        <FirstSurname t-esc="\'\'"/>\n                        <SecondSurname t-esc="\'\'"/>\n                        <t t-call="l10n_es_facturae.address_contact">\n                            <t t-set="partner" t-value="invoice_partner"/>\n                        </t>\n                    </Individual>\n                    <LegalEntity t-if="buyer_type == \'J\'">\n                        <CorporateName t-esc="invoice_partner.name"/>\n                        <TradeName t-esc="invoice_partner.name"/>\n                        <t t-call="l10n_es_facturae.address_contact">\n                            <t t-set="partner" t-value="invoice_partner"/>\n                        </t>\n                    </LegalEntity>\n                </BuyerParty>\n            </Parties>\n            <Invoices>\n                <Invoice>\n                    <InvoiceHeader>\n                        <InvoiceNumber t-esc="invoice.number.replace(\'/\',\'\')"/>\n                        <InvoiceSeriesCode t-esc="\'\'"/>\n                        <InvoiceDocumentType t-esc="\'FC\'"/>\n                        <InvoiceClass t-esc="\'OO\'"/>\n                    </InvoiceHeader>\n                    <InvoiceIssueData>\n                        <IssueDate t-esc="invoice.date_invoice"/>\n                        <!-- TODO: la documentacion de Inditex lo pone como obligatorio, en los ejemplos no aparece\n                        <OperationDate></OperationDate>\n                        -->\n                        <InvoiceCurrencyCode t-esc="invoice.currency_id.name"/>\n                        <TaxCurrencyCode t-esc="invoice.currency_id.name"/>\n                        <LanguageName t-esc="\'es\'"/>\n                    </InvoiceIssueData>\n                    <TaxesOutputs>\n                        <Tax t-foreach="invoice.tax_line_ids" t-as="tax_line">\n                            <TaxTypeCode t-esc="\'01\'"/>\n                            <TaxRate t-esc="\'%.2f\' % tax_line.tax_id.amount"/>\n                            <TaxableBase>\n                                <TotalAmount t-esc="\'%.2f\' % tax_line.base"/>\n                            </TaxableBase>\n                            <TaxAmount>\n                                <TotalAmount t-esc="\'%.2f\' % tax_line.amount"/>\n                            </TaxAmount>\n                        </Tax>\n                    </TaxesOutputs>\n                    <InvoiceTotals>\n                        <TotalGrossAmount t-esc="\'%.2f\' % sum(invoice.mapped(\'invoice_line_ids.price_subtotal\'))"/>\n                        <TotalGrossAmountBeforeTaxes t-esc="\'%.2f\' % sum(invoice.mapped(\'invoice_line_ids.price_subtotal\'))"/>\n                        <TotalTaxOutputs t-esc="\'%.2f\' % invoice.amount_tax"/>\n                        <TotalTaxesWithheld t-esc="\'0.00\'"/>\n                        <InvoiceTotal t-esc="\'%.2f\' % invoice.amount_total"/>\n                        <TotalOutstandingAmount t-esc="\'%.2f\' % invoice.residual"/>\n                        <TotalExecutableAmount t-esc="\'%.2f\' % invoice.residual"/>\n                    </InvoiceTotals>\n                    <Items>\n                        <InvoiceLine t-foreach="invoice.invoice_line_ids" t-as="line">\n                            <IssuerTransactionReference t-esc="invoice.customer_order_ref"/>\n                            <!--TODO: No aparece como obligatorio en la documentaci&#243;n, pero siempre sale en los ejemplos-->\n                            <IssuerTransactionDate t-esc="invoice.delivery_date"/>\n                            <ReceiverTransactionReference t-esc="invoice.customer_delivery_ref"/>\n                            <ReceiverTransactionDate t-esc="invoice.delivery_date"/>\n                            <DeliveryNotesReferences>\n                                <DeliveryNote>\n                                    <DeliveryNoteNumber t-esc="invoice.ple_number"/>\n                                </DeliveryNote>\n                            </DeliveryNotesReferences>\n                            <!-- CMNT Comentado porque falla -->\n                         <!--    <ItemDescription>\n                                <![CDATA[<![CDATA[]]><t t-esc="\'%s     %s]]\' % (line.product_id.product_customer_codes.product_code , line.product_id.product_customer_codes.product_name)"/><![CDATA[>]]>\n                            </ItemDescription> -->\n                            <ItemDescription>\n                                &lt;![CDATA[<t t-esc="\'%s     %s]]\' % (line.product_id.default_code , line.product_id.display_name)"/>&gt;\n                            </ItemDescription>\n                            <Quantity t-esc="line.quantity"/>\n                            <UnitPriceWithoutTax t-esc="\'%.6f\' % line.price_unit"/>\n                            <TotalCost t-esc="\'%.6f\' % (line.quantity * line.price_unit)"/>\n                            <DiscountsAndRebates>\n                                <Discount>\n                                    <DiscountReason t-esc="\'Descuento\'"/>\n                                    <DiscountRate t-esc="\'%.4f\' % line.discount"/>\n                                    <DiscountAmount t-esc="\'%.6f\' % (line.price_unit * line.quantity - line.price_subtotal)"/>\n                                </Discount>\n                            </DiscountsAndRebates>\n                            <GrossAmount t-esc="\'%.6f\' % line.price_subtotal"/>\n                            <t t-set="tax_exempt" t-value="True"/>\n                            <TaxesOutputs>\n                                <Tax t-foreach="line.invoice_line_tax_ids" t-as="line_tax">\n                                    <TaxTypeCode t-esc="\'01\'"/>\n                                     <t t-if="line_tax.amount &gt; 0">\n                                        <t t-set="tax_exempt" t-value="False"/>\n                                    </t>\n                                    <TaxRate t-esc="\'%.2f\' % line_tax.amount"/>\n                                    <TaxableBase>\n                                        <TotalAmount t-esc="\'%.2f\' % line.price_subtotal"/>\n                                    </TaxableBase>\n                                </Tax>\n                            </TaxesOutputs>\n                            <SpecialTaxableEvent t-if="tax_exempt">\n                                <SpecialTaxableEventCode t-esc="\'02\'"/>\n                                <SpecialTaxableEventReason t-esc="\'Mercanc&#237;a a nacionalizar por el cliente\'"/>\n                            </SpecialTaxableEvent>\n                            <!-- CMNT COMENTADO, NO HAY MODULO CON CAMPO product_customer_codes -->\n                            <!-- <ArticleCode t-esc="line.product_id.product_customer_codes.product_code"/> -->\n                            <ArticleCode t-esc="line.product_id.default_code"/>\n                        </InvoiceLine>\n                    </Items>\n                    <!-- TODO: Inditex recomienda no rellenar esta parte\n                    <PaymentDetails t-if="invoice.payment_mode_id">\n                        <Installment t-foreach="invoice.move_id.line_ids" t-as="move" t-if="move.account_id == invoice.account_id">\n                            <InstallmentDueDate t-esc="move.date_maturity or invoice.date_invoice"/>\n                            <InstallmentAmount t-esc="\'%.2f\' % (move.debit if move.debit > move.credit else -move.credit)"/>\n                            <PaymentMeans t-esc="invoice.payment_mode_id.facturae_code"/>\n                            <AccountToBeDebited t-if="invoice.payment_mode_id.facturae_code == \'02\'">\n                                <IBAN t-esc="invoice.partner_bank_id.acc_number"/>\n                            </AccountToBeDebited>\n                            <AccountToBeCredited t-if="invoice.payment_mode_id.facturae_code != \'02\'">\n                                <IBAN t-esc="invoice.partner_bank_id.acc_number"/>\n                            </AccountToBeCredited>\n                        </Installment>\n                    </PaymentDetails> -->\n                    <!-- CMNT COMENTADO PORQUE FALLA -->\n                    <AdditionalData>\n                        <InvoiceAdditionalInformation t-esc="invoice.comment"/>\n                        <Extensions>\n                            <v1:InditexInvoiceExtension xmlns:v1="http://www.inditex.com/documents/einvoicing/Facturae/InditexInvoiceExtension/v1.0">\n                                    <Version t-esc="\'1.0\'"/>\n                                    <InvoiceFamily t-esc="\'PRODUCT_INVOICE\'"/>\n                                  <Campaign t-esc="invoice.campaign"/>\n                                 <LogisticExtension>\n                                    <TransportCode t-esc="invoice.transport_mode_id.id"/>\n                                    <IncotermCode t-esc="invoice.incoterms_id.code"/>\n                                    <TotalNetWeight t-esc="invoice.net_weight"/>\n                                    <TotalVolume t-esc="invoice.volume"/>\n                                    <NumberOfCartons t-esc="invoice.number_of_cartons"/>\n                                 </LogisticExtension>\n                            </v1:InditexInvoiceExtension>\n                        </Extensions>\n                    </AdditionalData>\n                </Invoice>\n            </Invoices>\n        </t>\n    </t>'


class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        res = super(IrUiView, self).read(fields=None, load='_classic_read')
        for iuw in self:
            if iuw.name == u'template_facturae_inditex':
                res[0]['arch'] = ARCH_FIXED
        return res