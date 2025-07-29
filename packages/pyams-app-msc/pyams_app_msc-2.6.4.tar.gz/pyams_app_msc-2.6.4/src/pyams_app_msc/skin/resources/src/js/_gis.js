import MyAMS from "./_utils";


const createMap = (map, config, options, callback) => {

	return new Promise((resolve, reject) => {

		const data = map.data();
		let settings = {
			preferCanvas: data.mapLeafletPreferCanvas || false,
			attributionControl: data.mapLeafletAttributionControl === undefined ?
				config.attributionControl : data.mapLeafletAttributionControl,
			zoomControl: data.mapLeafletZoomControl === undefined ?
				config.zoomControl : data.mapLeafletZoomControl,
			fullscreenControl: data.mapLeafletFullscreen === undefined ?
				config.fullscreenControl && {
					pseudoFullscreen: true
				} || null :
				data.mapLeafletFullscreen,
			crs: data.mapLeafletCrs || MyAMS.getObject(config.crs) || L.CRS.EPSG3857,
			center: data.mapLeafletCenter || config.center,
			zoom: data.mapLeafletZoom || config.zoom,
			gestureHandling: data.mapLeafletWheelZoom === undefined ?
				!config.scrollWheelZoom : data.mapLeafletWheelZoom,
			keyboard: data.mapLeafletKeyboard === undefined ?
				config.keyboard && !L.Browser.mobile : data.amsLeafletKeyboard
		};
		settings = $.extend({}, settings, options);
		map.trigger('map.init', [map, settings, config]);
		const
			leafmap = L.map(map.attr('id'), settings),
			layersConfig = [],
			baseLayers = {},
			overlayLayers = {};
		if (config.layers) {
			for (const layerConfig of config.layers) {
				map.trigger('map.layer.init', [map, layerConfig]);
				layersConfig.push(PyAMS_GIS.getLayer(map, leafmap, layerConfig));
			}
		} else {
			layersConfig.push(L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
				name: 'osm',
				title: 'OpenStreetMap',
				maxZoom: 19,
				attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
			}));
		}
		$.when.apply($, layersConfig).then((...layers) => {
			for (const [idx, layer] of Object.entries(layers)) {
				if (config.layers) {
					if (config.layers[idx].isVisible) {
						layer.addTo(leafmap);
					}
					if (config.layers[idx].isOverlay) {
						overlayLayers[config.layers[idx].title] = layer;
					} else {
						baseLayers[config.layers[idx].title] = layer;
					}
				} else {
					layer.addTo(leafmap);
				}
			}
			if (config.zoomControl && (data.mapLeafletHideZoomControl !== true)) {
				L.control.scale().addTo(leafmap);
			}
			if (config.layerControl) {
				L.control.layers(baseLayers, overlayLayers).addTo(leafmap);
			}
			if (config.center) {
				leafmap.setView(new L.LatLng(config.center.lat, config.center.lon),
					config.zoom || 13);
			} else if (config.bounds) {
				leafmap.fitBounds(config.bounds);
			}
			if (config.marker) {
				const icon = L.icon({
					iconUrl: '/--static--/pyams_gis/img/marker-icon.png',
					iconSize: [25, 41],
					iconAnchor: [12, 39]
				});
				const marker = L.marker();
				marker.setIcon(icon);
				marker.setLatLng({
					lon: config.marker.lon,
					lat: config.marker.lat
				});
				marker.addTo(leafmap);
			}
			map.data('leafmap', leafmap);
			map.data('leafmap.config', config);
			map.data('leafmap.layers', layers.reduce((res, layer) => ({
				...res,
				[layer.options.name]: layer
			}), {}));
			map.trigger('map.finishing', [map, leafmap, config]);
			if (callback) {
				callback(leafmap, config);
			}
			map.trigger('map.finished', [map, leafmap, config]);
			resolve(leafmap);
		});
	});
};


const PyAMS_GIS = {

	/**
	 * Map initialization
	 *
	 * @param maps: maps elements
	 * @param options: optional maps configuration settings
	 * @param callback: maps initialization callback
	 */
	init: (maps, options, callback) => {

		window.PyAMS_GIS = PyAMS_GIS;
		Promise.all([
			import('leaflet'),
			import("leaflet/dist/leaflet.css")
		]).then(() => {
			Promise.all([
				import('leaflet-gesture-handling'),
				import("leaflet-gesture-handling/dist/leaflet-gesture-handling.css"),
				import('leaflet-fullscreen'),
				import('leaflet-fullscreen/dist/leaflet.fullscreen.css')
			]).then(() => {
				const $maps = $.map(maps, (elt) => {
					return new Promise((resolve, reject) => {
						const
							map = $(elt),
							data = map.data(),
							config = data.mapConfiguration;
						if (config) {
							resolve(createMap(map, config, options, callback));
						} else {
							$.get(data.mapConfigurationUrl || 'get-map-configuration.json').then((config) => {
								createMap(map, config, options, callback).then((leafmap) => {
									resolve({
										'leafmap': leafmap,
										'config': config
									});
								});
							});
						}
					});
				});
				$.when.apply($, $maps).then();
			});
		});
	},

	/**
	 * Get layer definition
	 *
	 * @param map: source map element
	 * @param leafmap: current Leaflet map
	 * @param layer: current layer definition
	 */
	getLayer: (map, leafmap, layer) => {
		return new Promise((resolve, reject) => {
			const factory = MyAMS.getObject(layer.factory);
			if (factory !== undefined) {
				delete layer.factory;
				const deferred = [];
				if (layer.dependsOn) {
					for (const name in layer.dependsOn) {
						if (!layer.dependsOn.hasOwnProperty(name)) {
							continue;
						}
						if (MyAMS.getObject(name) === undefined) {
							deferred.push(MyAMS.getScript(layer.dependsOn[name]));
						}
					}
					delete layer.dependsOn;
				}
				$.when.apply($, deferred).then(() => {
					resolve(factory(map, leafmap, layer));
				});
			}
		});
	},

	/**
	 * Layers factories
	 */
	factory: {

		GeoJSON: (map, leafmap, layer) => {
			const url = layer.url;
			delete layer.url;
			const result = L.geoJSON(null, layer);
			map.on('map.finished', (evt, map, leafmap, config) => {
				$.get(url, (data) => {
					result.addData(data.geometry, {
						style: layer.style
					});
					if (config.fitLayer === layer.name) {
						leafmap.fitBounds(result.getBounds());
					}
				});
			});
			return result;
		},

		TileLayer: (map, leafmap, layer) => {
			const url = layer.url;
			delete layer.url;
			return L.tileLayer(url, layer);
		},

		WMS: function(map, leafmap, layer) {
			const url = layer.url;
			delete layer.url;
			return L.tileLayer.wms(url, layer);
		},

		Geoportal: {
			WMS: (map, leafmap, layer) => {
				MyAMS.getCSS('/--static--/pyams_gis/css/GpPluginLeaflet.min.css', 'geoportal');
				return L.geoportalLayer.WMS(layer);
			}
		},

		ESRI: {
			Feature: (map, leafmap, layer) => {
				return L.esri.featureLayer(layer);
			}
		},

		Google: (map, leafmap, layer) => {
			const apiKey = layer.apiKey;
			delete layer.apiKey;
			if (MyAMS.getObject('window.google.maps') === undefined) {
				const script = MyAMS.getScript('https://maps.googleapis.com/maps/api/js?key=' + apiKey);
				$.when.apply($, [script]);
			}
			return L.gridLayer.googleMutant(layer);
		}
	}
};

export default PyAMS_GIS;
