
import MyAMS from "./_utils";
import PyAMS_search from "./_search";

import "./_i18n";


$(() => {

	MyAMS.initData();

	/**
	 * Bootstrap tooltips and popovers
	 */
	$('body').tooltip({
		selector: '.hint'
	});

	$('[data-toggle="popover"]').popover({
		html: true,
		content: function(){
			return $(`[id="${$(this).data('target')}"`).html();
		}
	});


	/**
	 * Disable click on empty link
	 */
	$('a').on('click', (evt, x, y, z) => {
		if ($(evt.currentTarget).attr('href') === '#') {
			evt.preventDefault();
		}
	});


	/**
	 * Main navigation
	 */
	$('#main-navigation ul').superfish({
		delay: 600,
		animation: {
			opacity: 'show',
			height: 'show'
		},
		speed: 'fast',
		autoArrows: true,
		dropShadows: false
	});
	$('.mobile-menu-button, .mobile-menu-title').click(() => {
		$('.mobile-menu-inner').stop().slideToggle(350);
		return false;
	});


	/**
	 * Gallery modals
	 */
	const fitModalToContent = (modal) => {
		const target = $(modal.data('ams-resize-target'));
		if (target.length > 0) {
			const
				dialog = $('.modal-dialog', modal),
				padding = dialog.width() - target.width();
			dialog.css('max-width',
				Math.min($(window).width(), target.get(0).naturalWidth + padding));
		}
	};

	const showImage = (link, modal) => {
		const data = link.data();
		modal.find('.gallery-img')
			.one('load', () => {
				fitModalToContent(modal);
			})
			.attr('src', link.attr('href'))
			.attr('alt', data.alt_title || '');
		modal.find('.title').text(data.title || '');
		modal.find('.author').text(data.author || '');
		modal.find('.description').html(data.description || '');
		// check previous link
		const
			prevButton = $('.carousel-control-prev', modal),
			prevLink = link.parents('.col').first().prev().find('a.card');
		prevButton.off('click');
		if (prevLink.length > 0) {
			prevButton.on('click', () => {
				showImage(prevLink, modal);
			});
		}
		// check next link
		const
			nextButton = $('.carousel-control-next', modal),
			nextLink = link.parents('.col').first().next().find('a.card');
		nextButton.off('click');
		if (nextLink.length > 0) {
			nextButton.on('click', () => {
				showImage(nextLink, modal);
			});
		}
	};

	$('.modal-gallery').on('show.bs.modal', (evt) => {
		const
			link = $(evt.relatedTarget),
			modal = $(evt.target);
		showImage(link, modal);
	});


	/**
	 * Update generic forms
	 */
	window.PyAMS_search = PyAMS_search;

	const forms = $('.ams-form');
	if (forms.length > 0) {
		import('./_form').then(({default: PyAMS_form}) => {
			PyAMS_form.init(forms);
		});
	}


	/**
	 * Initialize calendars
	 */
	const calendars = $('.calendar');
	if (calendars.length > 0) {
		import('./_calendar').then(({default: PyAMS_calendar}) => {
			PyAMS_calendar.init(calendars);
		});
	}


	/**
	 * Initialize tables
	 */
	const tables = $('.datatable');
	if (tables.length > 0) {
		import('./_table').then(({default: PyAMS_datatable}) => {
			PyAMS_datatable.init(tables);
		});
	}


	/**
	 * Initialize maps
	 */
	const maps = $('.osmmap-map');
	if (maps.length > 0) {
		import('./_gis').then(({default: PyAMS_GIS}) => {
			MyAMS.gis = PyAMS_GIS;
			PyAMS_GIS.init(maps);
		});
	}


	/**
	 * Initialize glossary
	 */
	const createModal = (content) => {
		return new Promise((resolve, reject) => {
			const template = $(`<div class="modal fade">
				${content}
			</div>`);
			$('.draggable', template).addClass('w-100');
			template.appendTo($('body'));
			resolve(template.modal('show'));
		});
	};

	const openGlossaryTerm = (evt) => {
		const modals = $('.modal:visible');
		if (modals.length > 0) {
			modals.modal('hide');
		}
		const modal_id = 'glossary-term';
		$(`[id="${modal_id}"]`)
			.parents('.modal')
			.modal('dispose')
			.remove();
		$('.modal-backdrop').remove();
		const term = $(evt.target).data('term') || $(evt.target).text();
		$.get(`/get-glossary-term.html?term=${term}`).then((result) => {
			createModal(result).then();
		});
	};

	$(document).on('click', '.thesaurus-term', openGlossaryTerm);


	/**
	 * Alerts configuration
	 */
	Date.prototype.addHours = function (h) {
		return new Date(this.valueOf() + 86400000 * (h / 24));
	};

	const localStorageName = 'alerted::'

	const checkAlerts = () => {

		$('.alert-item').each((idx, elt) => {
			const
				alert = $(elt),
				storageKey = `${localStorageName}${alert.data('alert-id')}`;
			let alerted_on = localStorage.getItem(storageKey);
			if (alerted_on) {
				alerted_on = new Date(alerted_on);
				const now = new Date(),
					hide_until = alerted_on.addHours(parseInt(alert.data('alert-maximum-interval')));
				if (hide_until > now) {  // Hide alert
					alert.remove();
				}
			}
		});
	};

	$(document).on('click', '[data-dismiss="alert"]', (evt) => {
		const
			alert = $(evt.target).parents('.alert-item'),
			storageKey = `${localStorageName}${alert.data('alert-id')}`;
		alert.remove();
		localStorage.setItem(storageKey, (new Date()).toISOString());
	});

	checkAlerts();

});
