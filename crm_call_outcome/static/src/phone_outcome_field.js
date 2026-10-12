/** @odoo-module **/

/*
 * Option B (disabled by default): a dedicated phone icon on the Phone field
 * that opens the Call Outcome wizard. Enable by uncommenting the "assets"
 * block in __manifest__.py, then set widget="phone_outcome" on the phone
 * field (see README.md).
 */

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { PhoneField, phoneField } from "@web/views/fields/phone/phone_field";

export class PhoneOutcomeField extends PhoneField {
    static template = "crm_call_outcome.PhoneOutcomeField";

    setup() {
        super.setup();
        this.action = useService("action");
    }

    onLogCall() {
        if (!this.props.record.resId) {
            return; // record not saved yet
        }
        this.action.doAction("crm_call_outcome.action_crm_call_outcome_wizard", {
            additionalContext: { default_lead_id: this.props.record.resId },
            onClose: () => this.props.record.model.load(),
        });
    }
}

export const phoneOutcomeField = {
    ...phoneField,
    component: PhoneOutcomeField,
};

registry.category("fields").add("phone_outcome", phoneOutcomeField);
