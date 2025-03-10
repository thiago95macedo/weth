odoo.define('web.ReportActionManager', function (require) {
"use strict";

/**
 * The purpose of this file is to add the support of WETH actions of type
 * 'ir.actions.report' to the ActionManager.
 */

var ActionManager = require('web.ActionManager');
var core = require('web.core');
var framework = require('web.framework');
var session = require('web.session');


var _t = core._t;
var _lt = core._lt;

// Messages that might be shown to the user dependening on the state of wkhtmltopdf
var link = '<br><br><a href="http://wkhtmltopdf.org/" target="_blank">wkhtmltopdf.org</a>';
var WKHTMLTOPDF_MESSAGES = {
    broken: _lt('Your installation of Wkhtmltopdf seems to be broken. The report will be shown ' +
                'in html.') + link,
    install: _lt('Unable to find Wkhtmltopdf on this system. The report will be shown in ' +
                 'html.') + link,
    upgrade: _lt('You should upgrade your version of Wkhtmltopdf to at least 0.12.0 in order to ' +
                 'get a correct display of headers and footers as well as support for ' +
                 'table-breaking between pages.') + link,
    workers: _lt('You need to start WETH with at least two workers to print a pdf version of ' +
                 'the reports.'),
};

ActionManager.include({
    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Downloads a PDF report for the given url. It blocks the UI during the
     * report generation and download.
     *
     * @param {string} url
     * @returns {Promise} resolved when the report has been downloaded ;
     *   rejected if something went wrong during the report generation
     */
    _downloadReport: function (url) {
        var self = this;
        framework.blockUI();
        return new Promise(function (resolve, reject) {
            var type = 'qweb-' + url.split('/')[2];
            var blocked = !session.get_file({
                url: '/report/download',
                data: {
                    data: JSON.stringify([url, type]),
                    context: JSON.stringify(session.user_context),
                },
                success: resolve,
                error: (error) => {
                    self.call('crash_manager', 'rpc_error', error);
                    reject();
                },
                complete: framework.unblockUI,
            });
            if (blocked) {
                // AAB: this check should be done in get_file service directly,
                // should not be the concern of the caller (and that way, get_file
                // could return a promise)
                var message = _t('A popup window with your report was blocked. You ' +
                                 'may need to change your browser settings to allow ' +
                                 'popup windows for this page.');
                self.do_warn(_t('Warning'), message, true);
            }
        });
    },

    /**
     * Launch download action of the report
     *
     * @private
     * @param {Object} action the description of the action to execute
     * @param {Object} options @see doAction for details
     * @returns {Promise} resolved when the action has been executed
     */
    _triggerDownload: function (action, options, type){
        var self = this;
        var reportUrls = this._makeReportUrls(action);
        return this._downloadReport(reportUrls[type]).then(function () {
            if (action.close_on_report_download) {
                var closeAction = { type: 'ir.actions.act_window_close' };
                return self.doAction(closeAction, _.pick(options, 'on_close'));
            } else {
                return options.on_close();
            }
        });
    },
    /**
     * Executes actions of type 'ir.actions.report'.
     *
     * @private
     * @param {Object} action the description of the action to execute
     * @param {Object} options @see doAction for details
     * @returns {Promise} resolved when the action has been executed
     */
    _executeReportAction: function (action, options) {
        var self = this;

        if (action.report_type === 'qweb-html') {
            return this._executeReportClientAction(action, options);
        } else if (action.report_type === 'qweb-pdf') {
            // check the state of wkhtmltopdf before proceeding
            return this.call('report', 'checkWkhtmltopdf').then(function (state) {
                // display a notification according to wkhtmltopdf's state
                if (state in WKHTMLTOPDF_MESSAGES) {
                    self.do_notify(_t('Report'), WKHTMLTOPDF_MESSAGES[state], true);
                }

                if (state === 'upgrade' || state === 'ok') {
                    // trigger the download of the PDF report
                    return self._triggerDownload(action, options, 'pdf');
                } else {
                    // open the report in the client action if generating the PDF is not possible
                    return self._executeReportClientAction(action, options);
                }
            });
        } else if (action.report_type === 'qweb-text') {
            return self._triggerDownload(action, options, 'text');
        } else {
            console.error("The ActionManager can't handle reports of type " +
                action.report_type, action);
            return Promise.reject();
        }
    },
    /**
     * Executes the report client action, either because the report_type is
     * 'qweb-html', or because the PDF can't be generated by wkhtmltopdf (in
     * the case of 'qweb-pdf' reports).
     *
     * @param {Object} action
     * @param {Object} options
     * @returns {Promise} resolved when the client action has been executed
     */
    _executeReportClientAction: function (action, options) {
        var urls = this._makeReportUrls(action);
        var clientActionOptions = _.extend({}, options, {
            context: action.context,
            data: action.data,
            display_name: action.display_name,
            name: action.name,
            report_file: action.report_file,
            report_name: action.report_name,
            report_url: urls.html,
        });
        return this.doAction('report.client_action', clientActionOptions);
    },
    /**
     * Overrides to handle the 'ir.actions.report' actions.
     *
     * @override
     * @private
     */
    _handleAction: function (action, options) {
        if (action.type === 'ir.actions.report') {
            return this._executeReportAction(action, options);
        }
        return this._super.apply(this, arguments);
    },
    /**
     * Generates an object containing the report's urls (as value) for every
     * qweb-type we support (as key). It's convenient because we may want to use
     * another report's type at some point (for example, when `qweb-pdf` is not
     * available).
     *
     * @param {Object} action
     * @returns {Object}
     */
    _makeReportUrls: function (action) {
        var reportUrls = {
            html: '/report/html/' + action.report_name,
            pdf: '/report/pdf/' + action.report_name,
            text: '/report/text/' + action.report_name,
        };
        // We may have to build a query string with `action.data`. It's the place
        // were report's using a wizard to customize the output traditionally put
        // their options.
        if (_.isUndefined(action.data) || _.isNull(action.data) ||
            (_.isObject(action.data) && _.isEmpty(action.data))) {
            if (action.context.active_ids) {
                var activeIDsPath = '/' + action.context.active_ids.join(',');
                reportUrls = _.mapObject(reportUrls, function (value) {
                    return value += activeIDsPath;
                });
            }
            reportUrls.html += '?context=' + encodeURIComponent(JSON.stringify(session.user_context));
        } else {
            var serializedOptionsPath = '?options=' + encodeURIComponent(JSON.stringify(action.data));
            serializedOptionsPath += '&context=' + encodeURIComponent(JSON.stringify(action.context));
            reportUrls = _.mapObject(reportUrls, function (value) {
                return value += serializedOptionsPath;
            });
        }
        return reportUrls;
    },
});
});
