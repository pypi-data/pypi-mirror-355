(self["webpackChunkdjango_rijkshuisstijl"] = self["webpackChunkdjango_rijkshuisstijl"] || []).push([["sticky-navigation-bar"],{

/***/ "./node_modules/debounce/index.js":
/*!****************************************!*\
  !*** ./node_modules/debounce/index.js ***!
  \****************************************/
/***/ (function(module) {

/**
 * Returns a function, that, as long as it continues to be invoked, will not
 * be triggered. The function will be called after it stops being called for
 * N milliseconds. If `immediate` is passed, trigger the function on the
 * leading edge, instead of the trailing. The function also has a property 'clear' 
 * that is a function which will clear the timer to prevent previously scheduled executions. 
 *
 * @source underscore.js
 * @see http://unscriptable.com/2009/03/20/debouncing-javascript-methods/
 * @param {Function} function to wrap
 * @param {Number} timeout in ms (`100`)
 * @param {Boolean} whether to execute at the beginning (`false`)
 * @api public
 */
function debounce(func, wait, immediate){
  var timeout, args, context, timestamp, result;
  if (null == wait) wait = 100;

  function later() {
    var last = Date.now() - timestamp;

    if (last < wait && last >= 0) {
      timeout = setTimeout(later, wait - last);
    } else {
      timeout = null;
      if (!immediate) {
        result = func.apply(context, args);
        context = args = null;
      }
    }
  };

  var debounced = function(){
    context = this;
    args = arguments;
    timestamp = Date.now();
    var callNow = immediate && !timeout;
    if (!timeout) timeout = setTimeout(later, wait);
    if (callNow) {
      result = func.apply(context, args);
      context = args = null;
    }

    return result;
  };

  debounced.clear = function() {
    if (timeout) {
      clearTimeout(timeout);
      timeout = null;
    }
  };
  
  debounced.flush = function() {
    if (timeout) {
      result = func.apply(context, args);
      context = args = null;
      
      clearTimeout(timeout);
      timeout = null;
    }
  };

  return debounced;
};

// Adds compatibility for ES modules
debounce.debounce = debounce;

module.exports = debounce;


/***/ }),

/***/ "./rijkshuisstijl/js/components/sticky-detect/sticky-navigation-bar.js":
/*!*****************************************************************************!*\
  !*** ./rijkshuisstijl/js/components/sticky-detect/sticky-navigation-bar.js ***!
  \*****************************************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var bem_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! bem.js */ "./node_modules/bem.js/dist/bem.js");
/* harmony import */ var bem_js__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(bem_js__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./constants */ "./rijkshuisstijl/js/components/sticky-detect/constants.js");
/* harmony import */ var debounce__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! debounce */ "./node_modules/debounce/index.js");
/* harmony import */ var debounce__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(debounce__WEBPACK_IMPORTED_MODULE_2__);
/**
 * Keeps track of sticky state.
 * @class
 */class StickyDetect{/**
     * Constructor method.
     * @param {HTMLElement} node
     */constructor(node){/** @type {HTMLElement} */this.node=node;this.bindEvents();}/**
     * Binds events to callbacks.
     */bindEvents(){window.addEventListener('scroll',debounce__WEBPACK_IMPORTED_MODULE_2__(this.update.bind(this)));}update(){const threshold=this.node.style.top||0;const exp=this.node.getClientRects()[0].top<=threshold;const state=bem_js__WEBPACK_IMPORTED_MODULE_0___default().hasModifier(this.node,_constants__WEBPACK_IMPORTED_MODULE_1__.MODIFIER_STUCK);bem_js__WEBPACK_IMPORTED_MODULE_0___default().toggleModifier(this.node,_constants__WEBPACK_IMPORTED_MODULE_1__.MODIFIER_STUCK,exp);if(!state&&exp){window.scrollBy(0,10);}}}// Start!
[..._constants__WEBPACK_IMPORTED_MODULE_1__.STICKY_DETECTS].forEach(node=>new StickyDetect(node));

/***/ })

}]);