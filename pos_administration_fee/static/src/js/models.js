/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { PosStore } from "@point_of_sale/app/services/pos_store";

// Mirrors the built-in tip_product_id pattern (pos.config field + a special
// orderline for the same product, found/updated by product identity) but
// driven automatically off the order total instead of a manual tip screen.
//
// Unlike Odoo 17, PosOrder has no self-contained "add a line" method in 19 -
// that lives on the PosStore service (addLineToCurrentOrder), which runs a
// whole configurator/combo/lot/scale pipeline meant for user-picked
// products. The fee line needs none of that, so it's created directly via
// the same low-level ORM factory core itself uses internally
// (this.models["pos.order.line"].create(...)) - which also means this never
// re-enters the patched addLineToCurrentOrder below, so no recursion guard
// is needed there.

patch(PosOrder.prototype, {
    _getAdministrationFeeProduct() {
        const config = this.config;
        if (!config.administration_fee_enabled || !config.administration_fee_product_id) {
            return null;
        }
        return config.administration_fee_product_id;
    },
    _getAdministrationFeeLine(feeProduct) {
        return this.getOrderlines().find((line) => line.getProduct() === feeProduct);
    },
    // Recomputes whether the administration fee line should be present,
    // absent, or updated. Safe to call repeatedly/redundantly - it's a
    // no-op once the order is already in the right state.
    updateAdministrationFee() {
        const feeProduct = this._getAdministrationFeeProduct();
        if (!feeProduct) {
            return;
        }
        const config = this.config;
        const feeLine = this._getAdministrationFeeLine(feeProduct);
        const total = this.getOrderlines().reduce((sum, line) => {
            return line === feeLine ? sum : sum + line.priceIncl;
        }, 0);
        const shouldHaveFee = total > 0 && total < config.administration_fee_threshold;
        if (shouldHaveFee && !feeLine) {
            this.models["pos.order.line"].create({
                order_id: this,
                product_id: feeProduct,
                product_tmpl_id: feeProduct.product_tmpl_id,
                qty: 1,
                price_unit: config.administration_fee_amount,
                price_type: "manual",
                tax_ids: feeProduct.product_tmpl_id.taxes_id.map((tax) => ["link", tax]),
            });
        } else if (!shouldHaveFee && feeLine) {
            this.removeOrderline(feeLine);
        } else if (shouldHaveFee && feeLine && feeLine.price_unit !== config.administration_fee_amount) {
            feeLine.setUnitPrice(config.administration_fee_amount);
        }
    },
    removeOrderline(line) {
        const feeProduct = this._getAdministrationFeeProduct();
        const result = super.removeOrderline(...arguments);
        if (!feeProduct || line.getProduct() !== feeProduct) {
            this.updateAdministrationFee();
        }
        return result;
    },
});

patch(PosOrderline.prototype, {
    // Shared by setQuantity/setUnitPrice/setDiscount below. Skips
    // recomputing when the line being touched IS the fee line itself, to
    // avoid a feedback loop when updateAdministrationFee sets the fee
    // line's own price.
    _maybeUpdateAdministrationFee() {
        const order = this.order_id;
        if (!order) {
            return;
        }
        const feeProduct = order._getAdministrationFeeProduct();
        if (this.getProduct() !== feeProduct) {
            order.updateAdministrationFee();
        }
    },
    setQuantity(quantity, keep_price) {
        const result = super.setQuantity(...arguments);
        this._maybeUpdateAdministrationFee();
        return result;
    },
    setUnitPrice(price) {
        const result = super.setUnitPrice(...arguments);
        this._maybeUpdateAdministrationFee();
        return result;
    },
    setDiscount(discount) {
        const result = super.setDiscount(...arguments);
        this._maybeUpdateAdministrationFee();
        return result;
    },
});

patch(PosStore.prototype, {
    async addLineToCurrentOrder(vals, opts, configure = true) {
        const result = await super.addLineToCurrentOrder(...arguments);
        this.getOrder()?.updateAdministrationFee();
        return result;
    },
});
