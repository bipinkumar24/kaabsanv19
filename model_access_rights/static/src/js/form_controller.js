/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";

import { onWillStart, useState } from "@odoo/owl";

patch(FormController.prototype, {
    setup() {
        super.setup();
        this.modelAccessRights = useState({
            is_delete: false,
            is_export: false,
            is_create_or_update: false,
            is_archive: false,
        });
        onWillStart(async () => {
            const restrictions = await this.orm.call(
                "access.right",
                "get_user_view_access",
                [this.props.resModel]
            );
            Object.assign(this.modelAccessRights, restrictions);
            if (this.modelAccessRights.is_create_or_update) {
                this.canCreate = false;
                this.canEdit = false;
                this.archInfo.activeActions.create = false;
                this.archInfo.activeActions.edit = false;
            }
            if (this.modelAccessRights.is_delete) {
                this.archInfo.activeActions.delete = false;
            }
        });
    },

    getStaticActionMenuItems() {
        const items = super.getStaticActionMenuItems();
        if (this.modelAccessRights.is_archive) {
            items.archive.isAvailable = () => false;
            items.unarchive.isAvailable = () => false;
        }
        return items;
    },
});
