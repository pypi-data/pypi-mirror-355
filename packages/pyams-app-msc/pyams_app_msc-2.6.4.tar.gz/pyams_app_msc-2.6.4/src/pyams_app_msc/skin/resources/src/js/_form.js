

import 'jquery-form';
import 'jquery-validation';
import 'jsrender';
import "jquery.scrollto";

import MyAMS from "./_utils";


const ERRORS_TEMPLATE_STRING = `
	<div class="alert alert-{{:status}}" role="alert">
		<button type="button" class="close" data-dismiss="alert" 
				aria-label="{{*: MyAMS.i18n.BTN_CLOSE }}">
			<i class="fa fa-times" aria-hidden="true"></i>
		</button>
		{{if header}}
		<h5 class="alert-heading">{{:header}}</h5>
		{{/if}}
		{{if message}}
		<p>{{:message}}</p>
		{{/if}}
		{{if messages}}
		<ul>
		{{for messages}}
			<li>
				{{if header}}<strong>{{:header}} :</strong>{{/if}}
				{{:message}}
			</li>
		{{/for}}
		</ul>
		{{/if}}
		{{if widgets}}
		<ul>
		{{for widgets}}
			<li>
				{{if header}}<strong>{{:header}} :</strong>{{/if}}
				{{:message}}
			</li>
		{{/for}}
		</ul>
		{{/if}}
	</div>`;

const ERROR_TEMPLATE = $.templates({
	markup: ERRORS_TEMPLATE_STRING,
	allowCode: true
});


/**
 * Clear form messages
 */
const clearMessages = (form) => {
	$('.alert-success, SPAN.state-success', form).not('.persistent').remove();
	$('.state-success', form).removeClassPrefix('state-');
	$('.invalid-feedback', form).remove();
	$('.is-invalid', form).removeClass('is-invalid');
}


/**
 * Clear form alerts
 */
const clearAlerts = (form) => {
	$('.alert-danger, SPAN.state-error', form).not('.persistent').remove();
	$('.state-error', form).removeClassPrefix('state-');
	$('.invalid-feedback', form).remove();
	$('.is-invalid', form).removeClass('is-invalid');
}


const PyAMS_form = {

	init: (forms) => {

		$('label', forms).removeClass('col-md-3');
		$('.col-md-9', forms).removeClass('col-md-9');
		$('input, select, textarea', forms).addClass('form-control');
		$('button', forms).addClass('border');
		$('button[type="submit"]', forms).addClass('btn-primary');

		const lang = $('html').attr('lang');


		//
		// Initialize input masks
		//

		const inputs = $('input[data-input-mask]');
		if (inputs.length > 0) {
			import("inputmask").then(() => {
				inputs.each((idx, elt) => {
					const
						input = $(elt),
						data = input.data(),
						defaultOptions = {
							autoUnmask: true,
							clearIncomplete: true,
							removeMaskOnSubmit: true
						},
						settings = $.extend({}, defaultOptions, data.amsInputMaskOptions || data.amsOptions || data.options),
						veto = {veto: false};
					input.trigger('before-init.ams.inputmask', [input, settings, veto]);
					if (veto.veto) {
						return;
					}
					const
						mask = new Inputmask(data.inputMask, settings),
						plugin = mask.mask(elt);
					input.trigger('after-init.ams.inputmask', [input, plugin]);
				});
			});
		}


		//
		// Initialize select2 widgets
		//

		const selects = $('.select2');
		if (selects.length > 0) {
			import("select2").then(() => {
				selects.each((idx, elt) => {
					const
						select = $(elt),
						data = select.data(),
						defaultOptions = {
							theme: data.amsSelect2Options || data.amsTheme || 'bootstrap',
							language: data.amsSelect2Language || data.amsLanguage || lang
						},
						ajaxUrl = data.amsSelect2AjaxUrl || data.amsAjaxUrl || data['ajax-Url'];
					if (ajaxUrl) {
						// check AJAX data helper function
						let ajaxParamsHelper;
						const ajaxParams = MyAMS.getFunctionByName(
							data.amsSelect2AjaxParams || data.amsAjaxParams || data['ajax-Params']) ||
							data.amsSelect2AjaxParams || data.amsAjaxParams || data['ajax-Params'];
						if (typeof ajaxParams === 'function') {
							ajaxParamsHelper = ajaxParams;
						} else if (ajaxParams) {
							ajaxParamsHelper = (params) => {
								return _select2Helpers.select2AjaxParamsHelper(params, ajaxParams);
							}
						}
						defaultOptions.ajax = {
							url: MyAMS.getFunctionByName(
								data.amsSelect2AjaxUrl || data.amsAjaxUrl) ||
								data.amsSelect2AjaxUrl || data.amsAjaxUrl,
							data: ajaxParamsHelper || MyAMS.getFunctionByName(
								data.amsSelect2AjaxData || data.amsAjaxData) ||
								data.amsSelect2AjaxData || data.amsAjaxData,
							processResults: MyAMS.getFunctionByName(
								data.amsSelect2AjaxProcessResults || data.amsAjaxProcessResults) ||
								data.amsSelect2AjaxProcessResults || data.amsAjaxProcessResults,
							transport: MyAMS.getFunctionByName(
								data.amsSelect2AjaxTransport || data.amsAjaxTransport) ||
								data.amsSelect2AjaxTransport || data.amsAjaxTransport
						};
						defaultOptions.minimumInputLength = data.amsSelect2MinimumInputLength ||
							data.amsMinimumInputLength || data.minimumInputLength || 1;
					}
					const
						settings = $.extend({}, defaultOptions, data.amsSelect2Options || data.amsOptions || data.options),
						veto = {veto: false};
					select.trigger('before-init.ams.select2', [select, settings, veto]);
					if (veto.veto) {
						return;
					}
					const plugin = select.select2(settings);
					select.trigger('after-init.ams.select2', [select, plugin]);
				});
			});
		}


		//
		// Initialize datetime widgets
		//

		const dates = $('.datetime');
		if (dates.length > 0) {
			import("tempusdominus-bootstrap-4").then(() => {
				dates.each((idx, elt) => {
					const
						input = $(elt),
						data = input.data(),
						defaultOptions = {
							locale: data.amsDatetimeLanguage || data.amsLanguage || lang,
							icons: {
								time: 'far fa-clock',
								date: 'far fa-calendar',
								up: 'fas fa-arrow-up',
								down: 'fas fa-arrow-down',
								previous: 'fas fa-chevron-left',
								next: 'fas fa-chevron-right',
								today: 'far fa-calendar-check-o',
								clear: 'far fa-trash',
								close: 'far fa-times'
							},
							date: input.val() || elt.defaultValue,
							format: data.amsDatetimeFormat || data.amsFormat
						},
						settings = $.extend({}, defaultOptions, data.datetimeOptions || data.options),
						veto = {veto: false};
					input.trigger('before-init.ams.datetime', [input, settings, veto]);
					if (veto.veto) {
						return;
					}
					input.datetimepicker(settings);
					const plugin = input.data('datetimepicker');
					if (data.amsDatetimeIsoTarget || data.amsIsoTarget) {
						input.on('change.datetimepicker', (evt) => {
							const
								source = $(evt.currentTarget),
								data = source.data(),
								target = $(data.amsDatetimeIsoTarget || data.amsIsoTarget);
							target.val(evt.date ? evt.date.toISOString(true) : null);
						});
					}
					input.trigger('after-init.ams.datetime', [input, plugin]);
				});
			});
		}


		//
		// Initialize forms
		//

		const defaultOptions = {
			submitHandler: PyAMS_form.submitHandler,
			messages: {}
		};

		const getFormOptions = (form, options) => {
			$('[data-ams-validate-messages]', form).each((idx, elt) => {
				options.messages[$(elt).attr('name')] = $(elt).data('ams-validate-messages');
				options.errorClass = 'error d-block';
				options.errorPlacement = (error, element) => {
					element.parents('div:first').append(error);
				};
			});
			return options;
		};

		const validateForms = () => {
			$(forms).each((idx, form) => {
				const options = $.extend({}, defaultOptions);
				$(form).validate(getFormOptions(form, options));
			});
		}

		if (lang === 'fr') {
			import("jquery-validation/dist/localization/messages_fr").then(() => {
				validateForms();
			});
		} else {
			validateForms();
		}
	},


	/**
	 * Show message extracted from JSON response
	 */
	showMessage: (errors, form) => {

		const createMessages = () => {
			const
				header = errors.header ||
					MyAMS.i18n.SUCCESS,
				props = {
					status: 'success',
					header: header,
					message: errors.message || null
				};
			$(ERROR_TEMPLATE.render(props)).prependTo(form);
		}

		clearMessages(form);
		clearAlerts(form);
		createMessages();
		$.scrollTo('.alert', {
			offset: -15
		});

	},


	/**
	 * Show errors extracted from JSON response
	 */
	showErrors: (errors, form) => {

		const setInvalid = (form, input, message) => {
			if (typeof input === 'string') {
				input = $(`[name="${input}"]`, form);
			}
			if (input.exists()) {
				const widget = input.closest('.form-widget');
				$('.invalid-feedback', widget).remove();
				$('<span>')
					.text(message)
					.addClass('is-invalid invalid-feedback')
					.appendTo(widget);
				input.removeClass('valid')
					.addClass('is-invalid');
			}
		}

		const createAlerts = () => {
			const messages = [];
			for (const message of errors.messages || []) {
				if (typeof message === 'string') {
					messages.push({
						header: null,
						message: message
					});
				} else {
					messages.push(message);
				}
			}
			for (const widget of errors.widgets || []) {
				messages.push({
					header: widget.label,
					message: widget.message
				});
			}
			const
				header = errors.header ||
					(messages.length > 1 ? MyAMS.i18n.ERRORS_OCCURRED : MyAMS.i18n.ERROR_OCCURRED),
				props = {
					status: 'danger',
					header: header,
					message: errors.error || null,
					messages: messages
				};
			$(ERROR_TEMPLATE.render(props)).prependTo(form);
			// update status of invalid widgets
			for (const widget of errors.widgets || []) {
				let input;
				if (widget.id) {
					input = $(`#${widget.id}`, form);
				} else {
					input = $(`[name="${widget.name}"]`, form);
				}
				if (input.exists()) {
					setInvalid(form, input, widget.message);
				}
				// open parent fieldsets switchers
				const fieldsets = input.parents('fieldset.switched');
				fieldsets.each((idx, elt) => {
					$('legend.switcher', elt).click();
				});
				// open parent tab panels
				const panels = input.parents('.tab-pane');
				panels.each((idx, elt) => {
					const
						panel = $(elt),
						tabs = panel.parents('.tab-content')
							.siblings('.nav-tabs');
					$(`li:nth-child(${panel.index() + 1})`, tabs)
						.addClass('is-invalid');
					$('li.is-invalid:first a', tabs)
						.click();
				});
			}
		}

		clearMessages(form);
		clearAlerts(form);
		createAlerts();
		$.scrollTo('.alert', {
			offset: -15
		});

	},

	submitHandler: (form) => {

		const doSubmit = (form) => {
			// record submit button as hidden input
			const
				button = $('button[type="submit"]', form),
				name = button.attr('name'),
				input = $('input[name="' + name + '"]', form);
			if (input.length === 0) {
				$('<input />')
					.attr('type', 'hidden')
					.attr('name', name)
					.attr('value', button.attr('value'))
					.appendTo(form);
			} else {
				input.val(button.attr('value'));
			}
			// record CSRF token as hidden input
			const csrf_param = $('meta[name=csrf-param]').attr('content'),
				  csrf_token = $('meta[name=csrf-token]').attr('content'),
				  csrf_input = $(`input[name="${csrf_param}"]`, form);
			if (csrf_input.length === 0) {
				$('<input />')
					.attr('type', 'hidden')
					.attr('name', csrf_param)
					.attr('value', csrf_token)
					.appendTo(form);
			} else {
				csrf_input.val(csrf_token);
			}
			// submit form!
			$(form).ajaxSubmit({
				// success handler
				success: (result, status, response, form) => {
					const contentType = response.getResponseHeader('content-type');
					if (contentType === 'application/json') {
						const status = result.status;
						switch (status) {
							case 'success':
								PyAMS_form.showMessage(result, form);
								break;
							case 'error':
								PyAMS_form.showErrors(result, form);
								break;
							case 'reload':
							case 'redirect':
								const location = result.location;
								if (window.location.href === location) {
									window.location.reload();
								} else {
									window.location.replace(location);
								}
								break;
							default:
								if (window.console) {
									window.console.warn(`Unhandled JSON status: ${status}`);
									window.console.warn(` > ${result}`);
								}
						}
					} else if (contentType === 'text/html') {
						const target = $('#main');
						target.html(result);
					}
				},
				// error handler
				error: (response, status, message, form) => {
					clearAlerts(form);
					const
						header = MyAMS.i18n.ERROR_OCCURRED,
						props = {
							status: 'danger',
							header: header,
							message: message
						};
					$(ERROR_TEMPLATE.render(props)).prependTo(form);
					$.scrollTo('.alert', {
						offset: -15
					});
				}
			});
		};

		if (window.grecaptcha) {  // check if recaptcha was loaded
			const captcha_key = $(form).data('ams-form-captcha-key');
			grecaptcha.execute(captcha_key, {
				action: 'form_submit'
			}).then((token) => {
				$('.state-error', form).removeClass('state-error');
				$('input[name="g-recaptcha-response"]', form).val(token);
				doSubmit(form);
			});
		} else {
			doSubmit(form);
		}
	}

};


export default PyAMS_form;
