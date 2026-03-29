from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)


class StockCardReportController(http.Controller):

  @http.route("/stock/stock_card_report/<string:output_format>", type="http", auth="user")
  def report(self, output_format, report_name=False, **kw):
    try:
      # Get active_id from query parameters or POST data
      active_id = kw.get("active_id")
      if not active_id and request.httprequest.method == "POST":
        # Try to get from POST data
        try:
          post_data = json.loads(request.httprequest.data.decode("utf-8"))
          if isinstance(post_data, dict) and "data" in post_data:
            # If data is a JSON string, parse it
            if isinstance(post_data["data"], str):
              data_content = json.loads(post_data["data"])
              # Try to extract active_id from the data
              if isinstance(data_content, dict) and "active_id" in data_content:
                active_id = data_content["active_id"]
            elif isinstance(post_data["data"], dict) and "active_id" in post_data["data"]:
              active_id = post_data["data"]["active_id"]
        except (json.JSONDecodeError, AttributeError, KeyError):
          pass

      # If still not found, try to get from request params
      if not active_id:
        active_id = request.params.get("active_id")

      if not active_id:
        return request.make_response(
            "Missing active_id parameter",
            headers=[("Content-Type", "text/plain")],
            status=400,
        )

      try:
        active_id = int(active_id)
      except (ValueError, TypeError):
        return request.make_response(
            "Invalid active_id parameter",
            headers=[("Content-Type", "text/plain")],
            status=400,
        )

      # Verify the report record exists
      report_model = request.env["report.stock.card.report"]
      report_record = report_model.browse(active_id)
      if not report_record.exists():
        return request.make_response(
            "Report record not found",
            headers=[("Content-Type", "text/plain")],
            status=404,
        )

      # Ensure computed fields are computed
      report_record._compute_results()

      # Both methods in Odoo 19 require report_ref as first argument (class methods)
      IrActionsReport = request.env["ir.actions.report"]

      if output_format == "pdf":
        report_ref = request.env.ref("stock_card_report.action_stock_card_report_pdf")
        # In Odoo 19, _render_qweb_pdf requires report_ref as first argument
        pdf_content = IrActionsReport._render_qweb_pdf(
            report_ref,
            res_ids=[active_id],
            data={"report_type": "pdf"},
        )
        # Handle both tuple and single value returns
        if isinstance(pdf_content, tuple):
          pdf_content = pdf_content[0]
        return request.make_response(
            pdf_content,
            headers=[
                ("Content-Type", "application/pdf"),
                (
                    "Content-Disposition",
                    "attachment; filename=Stock_Card_Report.pdf",
                ),
            ],
        )
      else:
        report_ref = request.env.ref("stock_card_report.action_stock_card_report_xlsx")
        # In Odoo 19, _render_xlsx requires report_ref as first argument
        xlsx_content = IrActionsReport._render_xlsx(
            report_ref,
            docids=[active_id],
            data={"report_type": "xlsx"},
        )
        # Handle both tuple and single value returns
        if isinstance(xlsx_content, tuple):
          xlsx_content = xlsx_content[0]
        return request.make_response(
            xlsx_content,
            headers=[
                (
                    "Content-Type",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ),
                (
                    "Content-Disposition",
                    "attachment; filename=Stock_Card_Report.xlsx",
                ),
            ],
        )
    except Exception as e:
      _logger.error("Error generating stock card report: %s", str(e), exc_info=True)
      return request.make_response(
          f"Error generating report: {str(e)}",
          headers=[("Content-Type", "text/plain")],
          status=500,
      )
