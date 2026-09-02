if ( window.location.hostname === 'developer.wikimedia.org' ) {
	( function () {
		// Copied from mediawiki.user.js in the mediawiki repository, see
		// https://gerrit.wikimedia.org/g/mediawiki/core/+/76e3d9eff0de66da60a6536ccdee95e4b1e083fa/resources/src/mediawiki.user.js#98
		function generateRandomSessionId() {
			let rnds;
			// We first attempt to generate a set of random values using the WebCrypto API's
			// getRandomValues method. If the WebCrypto API is not supported, the Uint16Array
			// type does not exist, or getRandomValues fails (T263041), an exception will be
			// thrown, which we'll catch and fall back to using Math.random.
			try {
				// Initialize a typed array containing 5 0-initialized 16-bit integers.
				// Note that Uint16Array is array-like but does not implement Array.
				rnds = new Uint16Array(5);
				// Overwrite the array elements with cryptographically strong random values.
				// https://developer.mozilla.org/en-US/docs/Web/API/Crypto/getRandomValues
				// NOTE: this operation can fail internally (T263041), so the try-catch block
				// must be preserved even after WebCrypto is supported in all modern (Grade A)
				// browsers.
				crypto.getRandomValues(rnds);
			} catch (e) {
				rnds = new Array(5);
				// 0x10000 is 2^16 so the operation below will return a number
				// between 2^16 and zero
				for (let i = 0; i < 5; i++) {
					rnds[i] = Math.floor(Math.random() * 0x10000);
				}
			}
			// Convert the 5 16bit-numbers into 20 characters (4 hex per 16 bits).
			// Concatenation of two random integers with entropy n and m
			// returns a string with entropy n+m if those strings are independent.
			// Tested that below code is faster than array + loop + join.
			return (
				(rnds[0] + 0x10000).toString(16).slice(1) +
				(rnds[1] + 0x10000).toString(16).slice(1) +
				(rnds[2] + 0x10000).toString(16).slice(1) +
				(rnds[3] + 0x10000).toString(16).slice(1) +
				(rnds[4] + 0x10000).toString(16).slice(1)
			);
		}

		function setCookie( cname, cvalue, exseconds ) {
			const d = new Date();
			d.setTime( d.getTime() + 1000 * exseconds );
			let expires = "expires="+ d.toUTCString();
			document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
		}

		function getCookie( cname ) {
			let name = cname + "=";
			let decodedCookie = decodeURIComponent( document.cookie );
			let ca = decodedCookie.split( ';' );
			for ( let i = 0; i <ca.length; i++ ) {
				let c = ca[i];
				while ( c.charAt(0) === ' ' ) {
					c = c.substring( 1 );
				}
				if ( c.indexOf( name ) === 0 ) {
					return c.substring( name.length, c.length );
				}
			}

			return "";
		}

		function getSessionId() {
			let id = getCookie( 'session_id' );

			if ( id === "" ) {
				id = generateRandomSessionId();
			}

			setCookie( 'session_id', id, 3600 );

			return id;
		}

		function getBeaconEvent() {
			const STREAM_NAME = "product_metrics.web_base";
			const SCHEMA_ID = "/analytics/product_metrics/web/base/2.2.0";
			// Use the list of languages under /data/locale since there is no easy way to tell
			// the current language from the path (English pages have no prefix and pages can have
			// subpages) nor the document html tag language attribute (that is the theme language
			// and locales are not a subset of THEME_LANGS). For example, the lang attribute for
			// "/ko/" or "/zh-hant/" paths is "en".
			const LANGUAGES = [
				"ar",
				"bn",
				"de",
				"en",
				"en-gb",
				"es",
				"fa",
				"fi",
				"fr",
				"ga",
				"he",
				"ja",
				"ko",
				"lb",
				"mk",
				"nl",
				"pl",
				"pt-br",
				"ru",
				"sh-latn",
				"sk",
				"sl",
				"tr",
				"zh-hans",
				"zh-hant",
			];
			// Get the content language and normalized page URI
			let page_lang = "en"
			let page_path = location.pathname;
			page_path = page_path.replace( /[\\/]+/g, '/' );
			if ( page_path.substring( page_path.length - 1 ) !== "/" ) {
				page_path = page_path + "/";
			}

			let path_components = page_path.split( "/" );
			if ( path_components.length >= 3 && LANGUAGES.indexOf( path_components[1] ) !== -1 ) {
				page_lang = path_components[1]
				page_path = "/" + path_components.slice( 2 ).join( "/" );
			}

			let browsing_session_id = getSessionId();

			return {
				$schema: SCHEMA_ID,
				meta: {
					stream: STREAM_NAME,
					domain: location.hostname,
				},
				action: "page_visit",
				action_context: JSON.stringify({
					uri_path: page_path,
				}),
				action_source: document.referrer,
				agent: {
					client_platform_family:
						Math.min(window.screen.width, window.screen.height) < 768
							? "mobile_browser"
							: "desktop_browser",
					ua_string: navigator.userAgent,
				},
				page: {
					content_language: page_lang,
				},
				performer: {
					session_id: browsing_session_id,
					is_logged_in: false
				},
			};
		}

		const ANALYTICS_ENDPOINT = "/ins-502b/v2/events";

		const event = getBeaconEvent();
		const eventData = JSON.stringify( event );
		//console.log( "Beacon to send to " + ANALYTICS_ENDPOINT + ":\n" + eventData );
		navigator.sendBeacon( ANALYTICS_ENDPOINT + '?hasty=true', eventData );
	} )();
}
