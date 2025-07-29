"use strict";
(self["webpackChunkdjango_rijkshuisstijl"] = self["webpackChunkdjango_rijkshuisstijl"] || []).push([["link-select"],{

/***/ "./rijkshuisstijl/js/components/form/link-select.js":
/*!**********************************************************!*\
  !*** ./rijkshuisstijl/js/components/form/link-select.js ***!
  \**********************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   LinkSelect: function() { return /* binding */ LinkSelect; }
/* harmony export */ });
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./constants */ "./rijkshuisstijl/js/components/form/constants.js");
/**
 * Navigates to selected value of select on change.
 * @class
 */class LinkSelect{/**
     * Constructor method.
     * @param {HTMLElement} node
     */constructor(node){/** {HTMLElement} */this.node=node;this.bindEvents();}/**
     * Binds events to callbacks.
     */bindEvents(){this.node.addEventListener('change',this.navigate.bind(this));}/**
     * Navigates to the selected link, opens new window if this.node.dataset.target equals "_blank".
     */navigate(){const target=this.node.dataset.target;const href=this.node.value||this.node.dataset.value;if(target==='_blank'){window.open(href);return;}location.href=href;}}// Start!
[..._constants__WEBPACK_IMPORTED_MODULE_0__.LINK_SELECTS].forEach(node=>new LinkSelect(node));

/***/ })

}]);