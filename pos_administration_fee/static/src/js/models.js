/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Order, Orderline } from "@point_of_sale/app/store/models";

// Mirrors the built-in tip_product_id pattern (pos.config field + a special
// orderline for the same product, found/updated by product identity) but
// driven automatically off the order total instead of a manual tip screen.

patch(Order.prototype, {
    _getAdministrationFeeProduct() {
        const config = this.pos.config;
        if (!config.administration_fee_enabled || !config.administration_fee_product_id) {
            return null;
        }
        return this.pos.db.get_product_by_id(config.administration_fee_product_id[0]) || null;
    },
    _getAdministrationFeeLine(feeProduct) {
        return this.get_orderlines().find((line) => line.get_product() === feeProduct);
    },
    // Recomputes whether the administration fee line should be present,
    // absent, or updated. Safe to call repeatedly/redundantly - it's a
    // no-op once the order is already in the right state.
    updateAdministrationFee() {
        const feeProduct = this._getAdministrationFeeProduct();
        if (!feeProduct) {
            return;
        }
        const config = this.pos.config;
        const feeLine = this._getAdministrationFeeLine(feeProduct);
        const total = this.get_orderlines().reduce((sum, line) => {
            return line === feeLine ? sum : sum + line.get_price_with_tax();
        }, 0);
        const shouldHaveFee = total > 0 && total < config.administration_fee_threshold;
        if (shouldHaveFee && !feeLine) {
            this.add_product(feeProduct, {
                quantity: 1,
                price: config.administration_fee_amount,
                lst_price: config.administration_fee_amount,
                merge: false,
                extras: { price_type: "automatic" },
            });
        } else if (!shouldHaveFee && feeLine) {
            this.removeOrderline(feeLine);
        } else if (shouldHaveFee && feeLine && feeLine.get_unit_price() !== config.administration_fee_amount) {
            feeLine.set_unit_price(config.administration_fee_amount);
            feeLine.set_lst_price(config.administration_fee_amount);
        }
    },
    async add_product(product, options) {
        const result = await super.add_product(...arguments);
        if (product !== this._getAdministrationFeeProduct()) {
            this.updateAdministrationFee();
        }
        return result;
    },
    removeOrderline(line) {
        const feeProduct = this._getAdministrationFeeProduct();
        const result = super.removeOrderline(...arguments);
        if (!feeProduct || line.get_product() !== feeProduct) {
            this.updateAdministrationFee();
        }
        return result;
    },
});

patch(Orderline.prototype, {
    // Shared by set_quantity/set_unit_price/set_discount below. Skips
    // recomputing when the line being touched IS the fee line itself -
    // both to avoid feedback loops (updateAdministrationFee sets the fee
    // line's own price) and because the fee line's construction runs
    // through these same setters before it's linked into order.orderlines.
    _maybeUpdateAdministrationFee() {
        const order = this.order;
        if (!order) {
            return;
        }
        const feeProduct = order._getAdministrationFeeProduct();
        if (this.product !== feeProduct) {
            order.updateAdministrationFee();
        }
    },
    set_quantity(quantity, keep_price) {
        const result = super.set_quantity(...arguments);
        this._maybeUpdateAdministrationFee();
        return result;
    },
    set_unit_price(price) {
        const result = super.set_unit_price(...arguments);
        this._maybeUpdateAdministrationFee();
        return result;
    },
    set_discount(discount) {
        const result = super.set_discount(...arguments);
        this._maybeUpdateAdministrationFee();
        return result;
    },
});
