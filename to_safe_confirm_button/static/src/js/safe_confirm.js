/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ViewButton } from "@web/views/view_button/view_button";
import { BUTTON_CLICK_PARAMS } from "@web/views/utils";

if (!BUTTON_CLICK_PARAMS.includes("safe-confirm")) {
    BUTTON_CLICK_PARAMS.push("safe-confirm");
}
if (!BUTTON_CLICK_PARAMS.includes("safe-confirm-title")) {
    BUTTON_CLICK_PARAMS.push("safe-confirm-title");
}
if (!BUTTON_CLICK_PARAMS.includes("safe-confirm-label")) {
    BUTTON_CLICK_PARAMS.push("safe-confirm-label");
}
if (!BUTTON_CLICK_PARAMS.includes("safe-cancel-label")) {
    BUTTON_CLICK_PARAMS.push("safe-cancel-label");
}

patch(ViewButton.prototype, {
    get clickParams() {
        const clickParams = { ...super.clickParams };
        if (clickParams["safe-confirm"] && !clickParams.confirm) {
            clickParams.confirm = clickParams["safe-confirm"];
            if (clickParams["safe-confirm-title"] && !clickParams["confirm-title"]) {
                clickParams["confirm-title"] = clickParams["safe-confirm-title"];
            }
            if (clickParams["safe-confirm-label"] && !clickParams["confirm-label"]) {
                clickParams["confirm-label"] = clickParams["safe-confirm-label"];
            }
            if (clickParams["safe-cancel-label"] && !clickParams["cancel-label"]) {
                clickParams["cancel-label"] = clickParams["safe-cancel-label"];
            }
        }
        return clickParams;
    },
});
