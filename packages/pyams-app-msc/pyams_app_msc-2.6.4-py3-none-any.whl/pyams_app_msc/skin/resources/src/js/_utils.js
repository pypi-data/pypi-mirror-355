
const MyAMS = {

	/**
	 * Get target URL matching given source
	 *
	 * Given URL can include variable names (with their namespace), given between braces, as in {MyAMS.baseURL}
	 */
	getSource: (url) => {
		return url.replace(/{[^{}]*}/g, function (match) {
			return MyAMS.getFunctionByName(match.substr(1, match.length - 2));
		});
	},

	/**
	 * Get a function given by name
	 * Small piece of code by Jason Bunting
	 */
	getFunctionByName: (functionName, context) => {
		if (typeof(functionName) === 'function') {
			return functionName;
		}
		if (!functionName) {
			return undefined;
		}
		const
			namespaces = functionName.split("."),
			func = namespaces.pop();
		context = (context === undefined || context === null) ? window : context;
		for (const namespace of namespaces) {
			try {
				context = context[namespace];
			} catch (e) {
				return undefined;
			}
		}
		try {
			return context[func];
		} catch (e) {
			return undefined;
		}
	},

	/**
	 * Execute a function given by name
	 */
	executeFunctionByName: (functionName, context /*, args */) => {
		const func = MyAMS.getFunctionByName(functionName, window);
		if (typeof func === 'function') {
			const args = Array.prototype.slice.call(arguments, 2);
			return func.apply(context, args);
		}
	},

	/**
	 * Get an object given by name
	 *
	 * @param objectName: dotted name
	 * @param context: original context, default to window
	 * @returns {Window|*|undefined}
	 */
	getObject: (objectName, context) => {
		if (typeof(objectName) !== 'string') {
			return objectName;
		}
		if (!objectName) {
			return undefined;
		}
		const namespaces = objectName.split(".");
		context = (context === undefined || context === null) ? window : context;
		for (const namespace of namespaces) {
			try {
				context = context[namespace];
			} catch (e) {
				return undefined;
			}
		}
		return context;
	},

	/**
	 * Script loader function
	 *
	 * @param url: script URL
	 * @param callback: a callback to be called after script loading
	 * @param options: a set of options to be added to AJAX call
	 * @param onerror: an error callback to be called instead of generic callback
	 */
	getScript: (url, callback, options, onerror) => {
		if (typeof(callback) === 'object') {
			onerror = options;
			options = callback;
			callback = null;
		}
		if (options === undefined) {
			options = {};
		}
		const
			defaults = {
				dataType: 'script',
				url: MyAMS.getSource(url),
				success: callback,
				error: onerror,
				cache: true,
				async: options.async === undefined ? typeof(callback) === 'function' : options.async
			};
		const settings = $.extend({}, defaults, options);
		return $.ajax(settings);
	},

	/**
	 * CSS file loader function
	 * Cross-browser code copied from Stoyan Stefanov blog to be able to
	 * call a callback when CSS is really loaded.
	 * See: https://www.phpied.com/when-is-a-stylesheet-really-loaded
	 *
	 * @param url: CSS file URL
	 * @param id: a unique ID given to CSS file
	 * @param callback: optional callback function to be called when CSS file is loaded. If set, callback is called
	 *   with a 'first_load' boolean argument to indicate is CSS was already loaded (*false* value) or not (*true*
	 *   value).
	 * @param options: callback options
	 */
	getCSS: (url, id, callback, options) => {
		if (callback) {
			callback = MyAMS.getFunctionByName(callback);
		}
		const head = $('HEAD');
		let style = $('style[data-ams-id="' + id + '"]', head);
		if (style.length === 0) {
			style = $('<style>').attr('data-ams-id', id)
				.text('@import "' + MyAMS.getSource(url) + '";');
			if (callback) {
				const styleInterval = setInterval(function () {
					try {
						const _check = style[0].sheet.cssRules;  // Is only populated when file is loaded
						clearInterval(styleInterval);
						callback.call(window, true, options);
					} catch (e) {
						// CSS is not loaded yet...
					}
				}, 10);
			}
			style.appendTo(head);
		} else {
			if (callback) {
				callback.call(window, false, options);
			}
		}
	},

	/**
	 * Initialize MyAMS data attributes
	 *
	 * @param element: source element
	 */
	initData: (element=document) => {
		$('[data-ams-data]', element).each((idx, elt) => {
			const
				dataElement = $(elt),
				data = dataElement.data('ams-data');
			if (data) {
				for (const name in data) {
					if (data.hasOwnProperty(name)) {
						let elementData = data[name];
						if (typeof (elementData) !== 'string') {
							elementData = JSON.stringify(elementData);
						}
						dataElement.attr('data-' + name, elementData);
					}
				}
			}
			dataElement.removeAttr('data-ams-data');
		});
	},

	/**
	 * MyAMS helpers
	 */
	helpers: {

		/**
		 * Click handler used to clear datetime input
		 */
		clearDatetimeValue: (evt) => {
			const
				target = $(evt.currentTarget).data('target'),
				picker = $(target).data('datetimepicker');
			if (picker) {
				picker.date(null);
			}
		}
	}
};


/**
 * Strings extensions
 */
$.extend(String.prototype, {

	/**
	 * Replace dashed names with camelCase variation
	 */
	camelCase: function() {
		if (!this) {
			return this;
		}
		return this.replace(/-(.)/g, (dash, rest) => {
			return rest.toUpperCase();
		});
	},

	/**
	 * Replace camelCase string with dashed name
	 */
	deCase: function() {
		if (!this) {
			return this;
		}
		return this.replace(/[A-Z]/g, (cap) => {
			return `-${cap.toLowerCase()}`;
		});
	},

	/**
	 * Convert first letter only to lowercase
	 */
	initLowerCase: function() {
		if (!this) {
			return this;
		}
		return this.charAt(0).toLowerCase() + this.slice(1);
	},

	/**
	 * Convert URL params to object
	 */
	unserialize: function () {
		if (!this) {
			return this;
		}
		const
			str = decodeURIComponent(this),
			chunks = str.split('&'),
			obj = {};
		for (const chunk of chunks) {
			const [key, val] = chunk.split('=', 2);
			obj[key] = val;
		}
		return obj;
	}
});


/**
 * JQuery extensions
 */
$.fn.extend({

	exists: function() {
		return $(this).length > 0;
	},

	listattr: function(attr) {
		const result = [];
		this.each((index, element) => {
			result.push($(element).attr(attr));
		});
		return result;
	},

	removeClassPrefix: function(prefix) {
		this.each(function(i, it) {
			const classes = it.className.split(/\s+/).map((item) => {
				return item.startsWith(prefix) ? "" : item;
			});
			it.className = $.trim(classes.join(" "));
		});
		return this;
	}
});


/**
 * Initialize custom click handlers
 */

const openPage = (href) => {
	if (window.location.toString() === href) {
		window.location.reload();
	} else {
		window.location = href;
	}
};

const linkClickHandler = (evt) => {
	return new Promise((resolve, reject) => {
		const
			link = $(evt.currentTarget),
			handlers = link.data('ams-disabled-handlers');
		if ((handlers === true) || (handlers === 'click') || (handlers === 'all')) {
			return;
		}
		let href = link.attr('href') || link.data('ams-url');
		if (!href ||
			href.startsWith('javascript:') ||
			link.attr('target') ||
			(link.data('ams-context-menu') === true)) {
			return;
		}
		evt.preventDefault();
		evt.stopPropagation();

		let url,
			target,
			params;
		if (href.indexOf('?') >= 0) {
			url = href.split('?');
			target = url[0];
			params = url[1].unserialize();
		} else {
			target = href;
			params = undefined;
		}
		const hrefGetter = MyAMS.getFunctionByName(target);
		if (typeof hrefGetter === 'function') {
			href = hrefGetter(link, params);
		}
		if (!href) {
			resolve(null);
		}
		else if (typeof href === 'function') {
			resolve(href(link, params));
		} else {
			// Standard AJAX or browser URL call
			// Convert %23 characters to #
			href = href.replace(/%23/, '#');
			if (evt.ctrlKey) {
				window.open && window.open(href);
				resolve();
			} else {
				const linkTarget = link.data('ams-target') || link.attr('target');
				if (linkTarget) {
					if (linkTarget === '_blank') {
						window.open && window.open(href);
						resolve();
					} else if (linkTarget === '_top') {
						window.location = href;
						resolve();
					}
				} else {
					openPage(href);
					resolve();
				}
			}
		}
	});
};

$(document).on('click', '[data-ams-click-handler]', (event) => {
	const
		source = $(event.currentTarget),
		data = source.data();
	if (data.amsClickHandler) {
		if ((data.amsStopPropagation === true) || (data.amsClickStopPropagation === true)) {
			event.stopPropagation();
		}
		if (data.amsClickKeepDefault !== true) {
			event.preventDefault();
		}
		const handlers = data.amsClickHandler.split(/\s+/);
		for (const handler of handlers) {
			const callback = MyAMS.getFunctionByName(handler);
			if (callback !== undefined) {
				callback.call(source, event, data.amsClickHandlerOptions);
			}
		}
	}
});

$(document).on('click',
	'a[href!="#"]:not([data-toggle]), ' +
	'[data-ams-url]:not([data-toggle])', (evt) => {
	// check for specific click handler
	const handler = $(evt).data('ams-click-handler');
	if (handler) {
		return;
	}
	// check for DataTable collapse handler
	if (evt.target.tagName === 'TD') {
		const target = $(evt.target);
		if (target.hasClass('dtr-control')) {
			const table = target.parents('table.datatable');
			if (table.hasClass('collapsed')) {
				return;
			}
		}
	}
	return linkClickHandler(evt);
});


/**
 * Initialize custom change handlers
 */
$(document).on('change', '[data-ams-change-handler]', (event) => {
	const source = $(event.target);
	// Disable change handlers for readonly inputs
	// These change handlers are activated by IE!!!
	if (source.prop('readonly')) {
		return;
	}
	const data = source.data();
	if (data.amsChangeHandler) {
		if ((data.amsStopPropagation === true) || (data.amsChangeStopPropagation === true)) {
			event.stopPropagation();
		}
		if (data.amsChangeKeepDefault !== true) {
			event.preventDefault();
		}
		const handlers = data.amsChangeHandler.split(/\s+/);
		for (const handler of handlers) {
			const callback = MyAMS.getFunctionByName(handler);
			if (callback !== undefined) {
				callback.call(source, event, data.amsChangeHandlerOptions);
			} else {
				console.debug(`Unknown change handler ${handler}!`);
			}
		}
	}
});


/**
 * Initialize custom events handlers
 */
$(document).ready(() => {
	$('[data-ams-events-handlers]').each((idx, elt) => {
		const
			source = $(elt),
			handlers = source.data('ams-events-handlers');
		if (handlers) {
			const
				selector = source.data('ams-events-handlers-context'),
				context = selector ? source.parents(selector) : source;
			for (const [event, handler] of Object.entries(handlers)) {
				context.on(event, (event, ...options) => {
					const callback = MyAMS.getFunctionByName(handler);
					if (options.length > 0) {
						callback.call(document, event, ...options);
					} else {
						callback.call(document, event, source.data('ams-events-options') || {});
					}
				});
			}
		}
	});
});


window.MyAMS = MyAMS;

export default MyAMS;
