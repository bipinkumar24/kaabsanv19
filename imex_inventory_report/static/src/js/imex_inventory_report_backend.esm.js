/** @odoo-module **/
import { Component, onWillStart, onMounted, useRef, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class ImexInventoryReportBackend extends Component {
    static template = xml`
        <div class="o_imex_inventory_backend h-100 overflow-auto p-2">
            <div class="o_report_header mb-2">
                <button class="btn btn-sm btn-primary" t-on-click="onPrint">
                    <i class="fa fa-print me-1"/> Print
                </button>
            </div>
            <div class="o_report_content" t-ref="contentRef"/>
        </div>
    `;

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.contentRef = useRef("contentRef");
        this.rawHtml = "";

        const ctx = this.props.action.context;
        this.givenContext = Object.assign({}, ctx.context || {});
        this.givenContext.active_id =
            ctx.active_id || (this.props.action.params || {}).active_id;
        this.givenContext.model = ctx.active_model || false;
        this.odooCtx = ctx;

        onWillStart(async () => {
            const result = await this.orm.call(
                this.givenContext.model,
                "get_html",
                [this.givenContext],
                { context: this.odooCtx }
            );
            this.rawHtml = (result && result.html) || "";
        });

        onMounted(() => {
            if (this.contentRef.el) {
                this.contentRef.el.innerHTML = this.rawHtml;
            }
        });
    }

    async onPrint() {
        const result = await this.orm.call(
            this.givenContext.model,
            "print_report",
            [this.givenContext.active_id],
            { context: this.odooCtx }
        );
        await this.actionService.doAction(result);
    }
}

registry.category("actions").add(
    "imex_inventory_report_backend",
    ImexInventoryReportBackend
);
