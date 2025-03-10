odoo.define('website.s_popup', function (require) {
'use strict';

const config = require('web.config');
const dom = require('web.dom');
const publicWidget = require('web.public.widget');
const utils = require('web.utils');

const PopupWidget = publicWidget.Widget.extend({
    selector: '.s_popup',
    events: {
        'click .js_close_popup': '_onCloseClick',
        'hide.bs.modal': '_onHideModal',
        'show.bs.modal': '_onShowModal',
    },

    /**
     * @override
     */
    start: function () {
        this._popupAlreadyShown = !!utils.get_cookie(this.$el.attr('id'));
        if (!this._popupAlreadyShown) {
            this._bindPopup();
        }
        return this._super(...arguments);
    },
    /**
     * @override
     */
    destroy: function () {
        this._super.apply(this, arguments);
        $(document).off('mouseleave.open_popup');
        this.$target.find('.modal').modal('hide');
        clearTimeout(this.timeout);
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @private
     */
    _bindPopup: function () {
        const $main = this.$target.find('.modal');

        let display = $main.data('display');
        let delay = $main.data('showAfter');

        if (config.device.isMobile) {
            if (display === 'mouseExit') {
                display = 'afterDelay';
                delay = 5000;
            }
            this.$('.modal').removeClass('s_popup_middle').addClass('s_popup_bottom');
        }

        if (display === 'afterDelay') {
            this.timeout = setTimeout(() => this._showPopup(), delay);
        } else {
            $(document).on('mouseleave.open_popup', () => this._showPopup());
        }
    },
    /**
     * @private
     */
    _hidePopup: function () {
        this.$target.find('.modal').modal('hide');
    },
    /**
     * @private
     */
    _showPopup: function () {
        if (this._popupAlreadyShown) {
            return;
        }
        this.$target.find('.modal').modal('show');
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     */
    _onCloseClick: function () {
        this._hidePopup();
    },
    /**
     * @private
     */
    _onHideModal: function () {
        const nbDays = this.$el.find('.modal').data('consentsDuration');
        utils.set_cookie(this.$el.attr('id'), true, nbDays * 24 * 60 * 60);
        this._popupAlreadyShown = true;

        this.$target.find('.media_iframe_video iframe').each((i, iframe) => {
            iframe.src = '';
        });
    },
    /**
     * @private
     */
    _onShowModal() {
        this.el.querySelectorAll('.media_iframe_video').forEach(media => {
            const iframe = media.querySelector('iframe');
            iframe.src = media.dataset.oeExpression || media.dataset.src; // TODO still oeExpression to remove someday
        });
    },
});

publicWidget.registry.popup = PopupWidget;

// Try to update the scrollbar based on the current context (modal state)
// and only if the modal overflowing has changed

function _updateScrollbar(ev) {
    const context = ev.data;
    const isOverflowing = dom.hasScrollableContent(context._element);
    if (context._isOverflowingWindow !== isOverflowing) {
        context._isOverflowingWindow = isOverflowing;
        context._checkScrollbar();
        context._setScrollbar();
        if (isOverflowing) {
            document.body.classList.add('modal-open');
        } else {
            document.body.classList.remove('modal-open');
            context._resetScrollbar();
        }
    }
}

// Prevent bootstrap to prevent scrolling and to add the strange body
// padding-right they add if the popup does not use a backdrop (especially
// important for default cookie bar).

const _baseShowElement = $.fn.modal.Constructor.prototype._showElement;
$.fn.modal.Constructor.prototype._showElement = function () {
    _baseShowElement.apply(this, arguments);

    if (this._element.classList.contains('s_popup_no_backdrop')) {
        // Update the scrollbar if the content changes or if the window has been
        // resized. Note this could technically be done for all modals and not
        // only the ones with the s_popup_no_backdrop class but that would be
        // useless as allowing content scroll while a modal with that class is
        // opened is a very specific WETH behavior.
        $(this._element).on('content_changed.update_scrollbar', this, _updateScrollbar);
        $(window).on('resize.update_scrollbar', this, _updateScrollbar);

        this._odooLoadEventCaptureHandler = _.debounce(() => _updateScrollbar({ data: this }, 100));
        this._element.addEventListener('load', this._odooLoadEventCaptureHandler, true);

        _updateScrollbar({ data: this });
    }
};

const _baseHideModal = $.fn.modal.Constructor.prototype._hideModal;
$.fn.modal.Constructor.prototype._hideModal = function () {
    _baseHideModal.apply(this, arguments);

    // Note: do this in all cases, not only for popup with the
    // s_popup_no_backdrop class, as the modal may have lost that class during
    // edition before being closed.
    this._element.classList.remove('s_popup_overflow_page');

    $(this._element).off('content_changed.update_scrollbar');
    $(window).off('resize.update_scrollbar');

    if (this._odooLoadEventCaptureHandler) {
        this._element.removeEventListener('load', this._odooLoadEventCaptureHandler, true);
        delete this._odooLoadEventCaptureHandler;
    }
};

const _baseSetScrollbar = $.fn.modal.Constructor.prototype._setScrollbar;
$.fn.modal.Constructor.prototype._setScrollbar = function () {
    if (this._element.classList.contains('s_popup_no_backdrop')) {
        this._element.classList.toggle('s_popup_overflow_page', !!this._isOverflowingWindow);

        if (!this._isOverflowingWindow) {
            return;
        }
    }
    return _baseSetScrollbar.apply(this, arguments);
};

const _baseGetScrollbarWidth = $.fn.modal.Constructor.prototype._getScrollbarWidth;
$.fn.modal.Constructor.prototype._getScrollbarWidth = function () {
    if (this._element.classList.contains('s_popup_no_backdrop') && !this._isOverflowingWindow) {
        return 0;
    }
    return _baseGetScrollbarWidth.apply(this, arguments);
};

return PopupWidget;
});
