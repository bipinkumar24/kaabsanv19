/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";

import { onWillStart, useState } from "@odoo/owl";

patch(ListController.prototype, {
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
                this.activeActions.create = false;
                this.activeActions.edit = false;
            }
            if (this.modelAccessRights.is_delete) {
                this.activeActions.delete = false;
            }
            if (this.modelAccessRights.is_export) {
                this.isExportEnable = false;
            }
            if (this.modelAccessRights.is_archive) {
                this.archiveEnabled = false;
            }
        });
    },
});
