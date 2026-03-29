/** @odoo-module **/

import {Component, onWillStart, onMounted, onPatched, useState, useRef} from "@odoo/owl";
import {download} from "@web/core/network/download";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

export class report_backend extends Component {
    static template = "report_stock_card_html";

    setup() {
        this.orm = useService("orm");
        this.state = useState({lines: null});
        this.reportContentRef = useRef("reportContent");

        const {active_id, active_model, context, ttype, url} =
            this.props.action.context;
        this.controllerUrl = url;

        this.context = context || {};
        Object.assign(this.context, {
            active_id: active_id || this.props.action.params.active_id,
            model: active_model || false,
            ttype: ttype || false,
        });

        onWillStart(async () => {
            this.state.lines = await this.orm.call("report.stock.card.report", "get_html", [
                this.context,
            ]);
        });

        onMounted(() => {
            this.updateReportContent();
        });

        onPatched(() => {
            this.updateReportContent();
        });
    }

    updateReportContent() {
        if (this.reportContentRef.el && this.state.lines && this.state.lines.html) {
            this.reportContentRef.el.innerHTML = this.state.lines.html;
        }
    }

    onClickPrint() {
        let url = this.controllerUrl
            .replace(":active_id", this.context.active_id)
            .replace("output_format", "pdf");
        // Ensure URL starts with /
        if (!url.startsWith("/")) {
            url = "/" + url;
        }
        download({
            url,
            data: {},
        });
    }

    onClickExport() {
        let url = this.controllerUrl
            .replace(":active_id", this.context.active_id)
            .replace("output_format", "xlsx");
        // Ensure URL starts with /
        if (!url.startsWith("/")) {
            url = "/" + url;
        }
        download({
            url,
            data: {},
        });
    }
}

registry.category("actions").add("stock_card_report_backend", report_backend);
